# ==========================================================
# main.py — Retrieval-Augmented Generation (RAG)
# Tech: FAISS + SentenceTransformers + Groq
# Supports: .txt and .pdf
# ==========================================================

import os
from pathlib import Path
import faiss
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# ----------------------------------------------------------
# OPTIONAL PDF SUPPORT (FIXED)
# ----------------------------------------------------------
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

# ----------------------------------------------------------
# ENV
# ----------------------------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise SystemExit("❌ GROQ_API_KEY missing in .env")

client = Groq(api_key=GROQ_API_KEY)

# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------
DATA_DIR = Path("full_contract_txt")   # gdpr.txt / policy.txt / PDFs
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4

# ----------------------------------------------------------
# LOAD DOCUMENTS
# ----------------------------------------------------------
def extract_text_from_pdf(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf not installed. Run: pip install pypdf")
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        try:
            pages.append(p.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(pages)

def load_documents():
    texts, sources = [], []
    for p in DATA_DIR.iterdir():
        if p.suffix.lower() == ".txt":
            texts.append(p.read_text(encoding="utf-8", errors="ignore"))
            sources.append(p.name)
        elif p.suffix.lower() == ".pdf":
            texts.append(extract_text_from_pdf(p))
            sources.append(p.name)
    return texts, sources

# ----------------------------------------------------------
# CHUNKING
# ----------------------------------------------------------
def chunk_text(text: str):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + CHUNK_SIZE])
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

# ----------------------------------------------------------
# BUILD FAISS
# ----------------------------------------------------------
def build_faiss(chunks):
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = embedder.encode(chunks, convert_to_numpy=True)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    return index, embedder

# ----------------------------------------------------------
# SIMPLE RISK HEURISTICS
# ----------------------------------------------------------
def risk_level(text: str) -> str:
    t = text.lower()
    if "unlimited" in t or "indefinite" in t:
        return "High"
    if "personal data" in t and "retain" not in t:
        return "Medium"
    return "Low"

# ----------------------------------------------------------
# RAG QUERY
# ----------------------------------------------------------
def ask_rag(question, index, embedder, chunks, chunk_sources):
    q_vec = embedder.encode([question])
    _, ids = index.search(q_vec, TOP_K)

    context = ""
    used_sources = set()
    for i in ids[0]:
        context += chunks[i] + "\n"
        used_sources.add(chunk_sources[i])

    prompt = f"""
You are a legal compliance analyst.

Context:
{context}

Question:
{question}

Answer clearly and mention compliance risks (Low/Medium/High).
"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )

    answer = resp.choices[0].message.content.strip()
    return answer, risk_level(context), list(used_sources)

# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def main():
    print("🚀 RegulaAI — Full RAG Compliance System (Groq)")

    docs, sources = load_documents()
    if not docs:
        raise SystemExit("❌ No .txt or .pdf files found in full_contract_txt")

    chunks, chunk_sources = [], []
    for d, src in zip(docs, sources):
        c = chunk_text(d)
        chunks.extend(c)
        chunk_sources.extend([src] * len(c))

    print(f"📁 Loaded {len(chunks)} text chunks")

    print("📦 Building FAISS index...")
    index, embedder = build_faiss(chunks)

    print("\n💬 Ask compliance questions (type 'exit')")

    while True:
        q = input("\nQuestion: ")
        if q.lower() == "exit":
            break

        ans, risk, src = ask_rag(q, index, embedder, chunks, chunk_sources)
        print("\n📘 Answer:\n", ans)
        print("⚠️ Risk Level:", risk)
        print("📁 Sources:", ", ".join(src))
        print("-" * 60)

if __name__ == "__main__":
    main()
