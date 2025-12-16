# ==========================================================
# Milestone 1 — Load Dataset + Preprocess + Groq Integration
# ==========================================================

from groq import Groq
from dotenv import load_dotenv
import os
import re

# ----------------------------------------------------------
# Load environment variables from .env
# ----------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

# ----------------------------------------------------------
# Load Dataset (.txt file) — FIXED PATH
# ----------------------------------------------------------
dataset_path = os.path.join(
    os.getcwd(),
    "full_contract_txt",
    "sample.txt"
)

if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"⚠ Dataset not found at {dataset_path}")

with open(dataset_path, "r", encoding="utf-8", errors="ignore") as f:
    text = f.read().strip()

print("✅ Dataset loaded successfully!")
print(f"📄 Characters in dataset: {len(text)}")

# ----------------------------------------------------------
# Preprocess Text (clean + chunk)
# ----------------------------------------------------------
text = re.sub(r"\s+", " ", text)

CHUNK_SIZE = 1000
chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

print(f"✂️ Preprocessed into {len(chunks)} chunks")

# ----------------------------------------------------------
# Groq API Test
# ----------------------------------------------------------
client = Groq(api_key=GROQ_API_KEY)

try:
    print("\n🔌 Testing Groq API connection...\n")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant for regulatory compliance tasks."
            },
            {
                "role": "user",
                "content": "Summarize the key objectives of GDPR in 3 lines."
            }
        ],
        max_tokens=150,
        temperature=0.7
    )

    print("🤖 Groq API Response:\n")
    print(response.choices[0].message.content.strip())

except Exception as e:
    print(f"❌ Error connecting to Groq API: {e}")
