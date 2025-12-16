import os
from pathlib import Path
from dotenv import load_dotenv
import faiss
import numpy as np
from groq import Groq

# ---------------- CONFIG ----------------
BASE_DIR = Path.cwd()
DOCS_PATH = BASE_DIR / "full_contract_txt"
TOP_K = 4
EMBED_DIM = 4096  # Groq embeddings via LLM context

# ---------------- ENV ----------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise SystemExit("❌ GROQ_API_KEY missing")

client = Groq(api_key=GROQ_API_KEY)

# ---------------- LOAD DOCUMENTS ----------------
def load_documents():
    texts = []
    for p in DOCS_PATH.glob("*.txt"):
        texts.append(p.read_text(encoding="utf-8"))
    return texts

# ---------------- SIMPLE CHUNKING ----------------
def chunk_text(text, size=1000):
    return [text[i:i+size] for i in range(0, len(text), size)]

# ---------------- EMBEDDINGS (SIMULATED VIA HASH) ----------------
def embed(texts):
    vectors = []
    for t in texts:
        v = np.zeros(EMBED_DIM, dtype="float32")
        for i, c in enumerate(t.encode()[:EMBED_DIM]):
            v[i] = c / 255
        vectors.append(v)
    return np.array(vectors)

# ---------------- BUILD FAISS ----------------
def build_index(texts):
    vectors = embed(texts)
    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(vectors)
    return index, texts

# ---------------- ASK QUESTION ----------------
def ask(question, index, texts):
    q_vec = embed([question])
    _, ids = index.search(q_vec, TOP_K)
    context = "\n".join([texts[i] for i in ids[0]])

    prompt = f"""
You are a compliance analyst.
Answer ONLY from the context.

Context:
{context}

Question:
{question}
"""
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content

# ---------------- MAIN ----------------
def main():
    print("🚀 RegulaAI – Compliance RAG (Groq, Free)")

    raw_texts = load_documents()
    if not raw_texts:
        raise SystemExit("❌ No .txt files found")

    chunks = []
    for t in raw_texts:
        chunks.extend(chunk_text(t))

    print(f"📁 Loaded {len(chunks)} text chunks")

    print("📦 Building FAISS index...")
    index, chunks = build_index(chunks)

    print("\n💬 Ask compliance questions (type 'exit')")
    while True:
        q = input("\nQuestion: ")
        if q.lower() == "exit":
            break
        print("\n📘 Answer:\n", ask(q, index, chunks))

if __name__ == "__main__":
    main()
