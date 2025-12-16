from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in the .env file.")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# User prompt
prompt = "Explain what IS ISRO"

# Create streaming chat completion
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=True
)

# Print streamed response
print("AI Response:\n")
for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
