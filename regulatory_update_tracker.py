#!/usr/bin/env python3
# regulatory_update_tracker.py
# AI-Powered Regulatory Compliance Checker (RAG + Groq)

import os
import re
import json
import textwrap
from pathlib import Path
from dotenv import load_dotenv

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, black

from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

DOCS_PATH     = Path("./full_contract_txt")
REGS_PATH     = Path("./regulations_Dataset")  # optional
INDEX_PATH    = Path("./faiss_index")

MODEL_NAME    = "llama-3.3-70b-versatile"
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100
TOP_K         = 4
WRAP_WIDTH    = 95

if not os.getenv("GROQ_API_KEY"):
    raise SystemExit("❌ GROQ_API_KEY missing in .env")

# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_docs(path: Path):
    docs = []
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    for p in path.iterdir():
        try:
            if p.suffix.lower() == ".pdf":
                docs.extend(PyPDFLoader(str(p)).load())
            elif p.suffix.lower() in [".txt", ".md"]:
                docs.extend(TextLoader(str(p), encoding="utf-8").load())
        except Exception as e:
            print(f"[WARN] Failed to load {p.name}: {e}")
    return docs


def extract_text(docs):
    return "\n\n".join(d.page_content for d in docs)

# ============================================================
# RAG (FAISS)
# ============================================================

def build_vectorstore(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if INDEX_PATH.exists():
        return FAISS.load_local(
            str(INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True
        )

    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(str(INDEX_PATH))
    return vs

# ============================================================
# JSON EXTRACTION (LLM SAFE)
# ============================================================

def extract_json(text):
    try:
        return json.loads(text)
    except:
        m = re.search(r"\[.*\]", text, re.S)
        if m:
            try:
                return json.loads(m.group())
            except:
                return []
    return []

# ============================================================
# AMENDMENT GENERATION
# ============================================================

def generate_amendments(llm, contract_text, jurisdiction, laws):
    law_text = ", ".join(laws) if laws else "General compliance"

    prompt = f"""
You are a legal compliance expert.

Jurisdiction: {jurisdiction}
Applicable laws: {law_text}

Identify risky clauses and return ONLY JSON array:
[
  {{
    "clause_id": "...",
    "old_clause": "...",
    "new_clause": "...",
    "action": "replace" | "remove"
  }}
]

Contract:
{contract_text}
"""

    resp = llm.invoke(prompt)
    return extract_json(resp.content)

# ============================================================
# APPLY AMENDMENTS
# ============================================================

def apply_amendments(text, amendments):
    updated = text
    for a in amendments:
        old = a.get("old_clause", "")
        new = a.get("new_clause", "")
        action = a.get("action", "replace")

        if not old:
            continue

        if action == "remove":
            updated = updated.replace(old, "")
        else:
            updated = updated.replace(
                old,
                f"<<HIGHLIGHT>>{new}<</HIGHLIGHT>>"
            )
    return updated

# ============================================================
# SAVE PDF WITH RED HIGHLIGHTS
# ============================================================

def save_pdf(text, path):
    c = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER
    y = height - 40

    wrapper = textwrap.TextWrapper(width=WRAP_WIDTH)

    for line in text.split("\n"):
        segments = re.split(r"(<<HIGHLIGHT>>.*?<</HIGHLIGHT>>)", line)
        for seg in segments:
            if "<<HIGHLIGHT>>" in seg:
                seg = seg.replace("<<HIGHLIGHT>>", "").replace("<</HIGHLIGHT>>", "")
                c.setFillColor(red)
            else:
                c.setFillColor(black)

            for wrapped in wrapper.wrap(seg):
                if y < 50:
                    c.showPage()
                    y = height - 40
                c.drawString(40, y, wrapped)
                y -= 14
        y -= 8

    c.save()

# ============================================================
# RAG Q&A
# ============================================================

def rag_qa(llm, vectorstore, question):
    docs = vectorstore.similarity_search(question, k=TOP_K)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = f"""
Answer ONLY from context. If unknown, say "I don't know".

Context:
{context}

Question:
{question}
"""
    return llm.invoke(prompt).content

# ============================================================
# CLI
# ============================================================

def main():
    print("🚀 AI-Powered Contract Compliance Checker (Groq + RAG)")

    docs = load_docs(DOCS_PATH)
    full_text = extract_text(docs)

    vectorstore = build_vectorstore(docs)
    llm = ChatGroq(model=MODEL_NAME, temperature=0.2)

    current_text = full_text

    while True:
        print("\n1) Quick compliance analysis")
        print("2) Generate & apply amendments")
        print("3) Save corrected PDF")
        print("4) Ask compliance questions (RAG)")
        print("5) Exit")

        choice = input("Select: ").strip()

        if choice == "1":
            print(llm.invoke(f"List compliance issues:\n{current_text}").content)

        elif choice == "2":
            jur = input("Jurisdiction [global]: ") or "global"
            laws = input("Laws (GDPR,HIPAA) optional: ").split(",")
            amendments = generate_amendments(llm, current_text, jur, laws)
            current_text = apply_amendments(current_text, amendments)
            print("✅ Amendments applied")

        elif choice == "3":
            out = DOCS_PATH / "AMENDED_CONTRACT.pdf"
            save_pdf(current_text, out)
            print(f"✅ Saved: {out}")

        elif choice == "4":
            while True:
                q = input("Question (exit): ")
                if q.lower() == "exit":
                    break
                print(rag_qa(llm, vectorstore, q))

        elif choice == "5":
            break

        else:
            print("Invalid option")

if __name__ == "__main__":
    main()
