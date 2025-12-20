# ✅ RegulaAI – AI Powered Regulatory Compliance Checker

🔗 **Live App**:  
https://ai-powered-regulatory-compliance-infosys-2mptf6hpvkfqovoapmsgm.streamlit.app/

RegulaAI is an **AI-powered contract compliance and risk analysis web application** that helps users analyze legal contracts, identify risks, monitor regulatory rules, generate amendments, and interact through an intelligent chatbot.

---

## 🚀 Key Features

### 📤 Contract Upload
- Upload contracts in **PDF format**
- Automatic text extraction
- Handles encrypted PDFs

### 📊 Risk Dashboard
- Calculates contract risk score
- Detects:
  - Termination clauses
  - Liability clauses
  - Indemnification risks
  - Missing GDPR / data protection clauses
- Interactive charts:
  - Pie chart
  - Bar chart
  - Line chart

### 📜 Regulatory Update Monitor
- Extracts regulatory and compliance-related rules
- Highlights compliance gaps from the contract

### 🛠️ Smart Contract Amendment System
- AI-generated improved contract
- Clear change markers:
  - `[[UPDATED]] ... [[/UPDATED]]`
  - `[[REMOVED]] ... [[/REMOVED]]`
- Generates highlighted PDF:
  - Red underline → updates
  - Red strike-through → removals
- Sends updated contract via email

### 🤖 AI Chatbot
- Greeting-aware chatbot
- Uses uploaded contract automatically
- Supports:
  - Contract summarization
  - Clause extraction
  - Risk explanation
  - Regulatory queries
- Shows date/time **only when asked**

---

## 🧠 Tech Stack

- **Frontend**: Streamlit  
- **Backend**: Python  
- **LLM**: Groq (LLaMA 3.1)  
- **PDF Processing**: PyPDF2, ReportLab  
- **Data & Charts**: Pandas, Matplotlib  
- **Email Service**: SMTP (Gmail App Password)  
- **Secrets Management**: Streamlit Cloud Secrets  

---

## 📁 Project Structure

```

Ai-Powered-Regulatory-Compliance-Infosys/
│
├── stream.py                  # Main Streamlit app
├── app.py
├── regulai_rag.py
├── regulatory_update_tracker.py
├── db.py
├── mail.py
├── requirements.txt
├── faiss_index/
├── full_contract_txt/
├── Results/
├── .gitignore
├── LICENSE
└── README.md

````

---

## 🔐 Environment Variables (Streamlit Secrets)

Secrets are configured in **Streamlit Cloud**, not in `.env`.

```toml
GROQ_API_KEY = "your_groq_api_key"
SENDER_EMAIL = "your_email@gmail.com"
EMAIL_PASSWORD = "your_gmail_app_password"
````

⚠️ Use **Gmail App Password**, not your normal Gmail password.

---

## ▶️ Run Locally (Optional)

```bash
pip install -r requirements.txt
streamlit run stream.py
```

---

## 🎯 Use Cases

* Legal contract review
* Regulatory compliance checking
* Risk assessment for enterprises
* AI-assisted contract amendments
* Legal-tech and compliance automation

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👩‍💻 Author

**Sreeja**
AI-Powered Legal & Compliance Application
Built using Streamlit and Groq LLM.

---

⭐ If you like this project, please give it a star!

```

---

If you want, I can:
- 🔹 Shorten this README for **resume**
- 🔹 Add **screenshots section**
- 🔹 Write **hackathon pitch description**
- 🔹 Convert this into **project report**

Just tell me 😊
```
