# ============================================================
# RegulaAI – Enhanced Contract Compliance & Monitoring System
# ============================================================
# Framework : Streamlit
# AI        : Groq LLM (LLaMA)
# Features  : Upload, Dashboard, Risk Analysis,
#             Amendments, Chatbot, PDF Export, Email Alerts
# ============================================================

import streamlit as st
import os, io, re, smtplib
from datetime import datetime
import matplotlib.pyplot as plt

import pypdf
from email.message import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from groq import Groq

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="RegulaAI – Compliance System",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("## ✅ RegulaAI – Contract Compliance System")
st.caption("AI-Powered Contract Compliance & Risk Analysis Platform")

# ============================================================
# LOAD ENV
# ============================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY missing in .env file")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SESSION STATE
# ============================================================
st.session_state.setdefault("contracts", [])
st.session_state.setdefault("active_contract", None)
st.session_state.setdefault("updated_contract", "")
st.session_state.setdefault("current_page", "🏠 Dashboard")

# ============================================================
# HELPERS
# ============================================================
def extract_text_from_pdf(file, limit=16000):
    try:
        reader = pypdf.PdfReader(file)
        if reader.is_encrypted:
            reader.decrypt("")
        text = ""
        for page in reader.pages:
            if len(text) > limit:
                break
            if page.extract_text():
                text += page.extract_text() + "\n"
        return text[:limit]
    except Exception as e:
        return f"❌ PDF Error: {e}"

def calculate_risk(text):
    score = 0
    reasons = []
    t = text.lower()

    if "termination" in t:
        score += 20; reasons.append("Termination clause detected")
    if "liability" in t:
        score += 25; reasons.append("Liability clause detected")
    if "indemn" in t:
        score += 20; reasons.append("Indemnification clause detected")
    if "gdpr" not in t and any(x in t for x in ["personal data","privacy","data protection"]):
        score += 15; reasons.append("Missing GDPR compliance")

    return score, reasons

def ask_groq(question, contract_text):
    system_prompt = f"""
You are RegulaAI — an AI Legal Assistant.

Rules:
1. Use ONLY the provided contract.
2. If no contract exists, say: "Please upload a contract first."
3. Do NOT add new obligations.
4. For amendments:
   [[UPDATED]]...[[/UPDATED]]
   [[REMOVED]]...[[/REMOVED]]

Contract:
{contract_text}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":question}
        ]
    )
    return response.choices[0].message.content

def generate_pdf(text):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont("Helvetica", 11)

    y = 800
    for line in text.split("\n"):
        if "[[UPDATED]]" in line:
            clean = re.sub(r"\[\[/?UPDATED\]\]", "", line)
            pdf.setFillColorRGB(1,0,0)
            pdf.drawString(40,y,clean)
            pdf.line(40,y-2,520,y-2)
        elif "[[REMOVED]]" in line:
            clean = re.sub(r"\[\[/?REMOVED\]\]", "", line)
            pdf.setFillColorRGB(0.4,0.4,0.4)
            pdf.drawString(40,y,clean)
            pdf.line(40,y+4,520,y+4)
        else:
            pdf.setFillColorRGB(0,0,0)
            pdf.drawString(40,y,line)

        y -= 14
        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica",11)
            y = 800

    pdf.save()
    buffer.seek(0)
    return buffer

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
pages = [
    "🏠 Dashboard",
    "📤 Upload Contract",
    "🌍 Global Contracts",
    "📊 Risk Analysis",
    "🛠️ Amendments",
    "💬 Chatbot"
]

page = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(st.session_state.current_page)
)

# ============================================================
# DASHBOARD
# ============================================================
if page == "🏠 Dashboard":
    st.session_state.current_page = page

    total = len(st.session_state.contracts)
    risky = sum(1 for c in st.session_state.contracts if c["risk"] > 50)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Contracts", total)
    c2.metric("High Risk", risky)
    c3.metric("Groq API", "Connected")
    c4.metric("System", "Stable")

    if st.session_state.contracts:
        last = st.session_state.contracts[-1]
        st.info(f"📄 Last Uploaded: **{last['name']}** | Risk: **{last['risk']}%**")

# ============================================================
# UPLOAD CONTRACT
# ============================================================
elif page == "📤 Upload Contract":
    st.session_state.current_page = page

    file = st.file_uploader("Upload Contract PDF", type=["pdf"])
    if file:
        text = extract_text_from_pdf(file)
        if text.startswith("❌"):
            st.error(text)
        else:
            risk, reasons = calculate_risk(text)
            st.session_state.contracts.append({
                "name": file.name,
                "text": text,
                "risk": risk,
                "reasons": reasons,
                "uploaded": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("✅ Contract uploaded successfully")
            st.session_state.current_page = "🏠 Dashboard"
            st.rerun()

# ============================================================
# GLOBAL CONTRACTS
# ============================================================
elif page == "🌍 Global Contracts":
    st.session_state.current_page = page

    if not st.session_state.contracts:
        st.info("No contracts uploaded yet")
    else:
        for i,c in enumerate(st.session_state.contracts):
            with st.expander(f"{c['name']} | Risk {c['risk']}%"):
                st.write("Uploaded:", c["uploaded"])
                st.write("Issues:", ", ".join(c["reasons"]) or "None")
                if st.button("Select Contract", key=i):
                    st.session_state.active_contract = c
                    st.success("Contract selected")

# ============================================================
# RISK ANALYSIS
# ============================================================
elif page == "📊 Risk Analysis":
    st.session_state.current_page = page
    c = st.session_state.active_contract

    if not c:
        st.warning("Select a contract first")
        st.stop()

    fig, ax = plt.subplots()
    ax.pie([c["risk"],100-c["risk"]], labels=["Risk","Safe"], autopct="%1.1f%%")
    st.pyplot(fig)

    for r in c["reasons"]:
        st.error(r)

# ============================================================
# AMENDMENTS
# ============================================================
elif page == "🛠️ Amendments":
    st.session_state.current_page = page
    c = st.session_state.active_contract

    if not c:
        st.warning("Select a contract first")
        st.stop()

    st.text_area("Original Contract", c["text"], height=220)

    if st.button("Generate Amendments"):
        st.session_state.updated_contract = ask_groq(
            "Improve compliance and clarity using [[UPDATED]] and [[REMOVED]]",
            c["text"]
        )

    if st.session_state.updated_contract:
        st.text_area("Updated Contract", st.session_state.updated_contract, height=300)

        email = st.text_input("Recipient Email")
        if st.button("Send PDF"):
            pdf = generate_pdf(st.session_state.updated_contract)
            msg = EmailMessage()
            msg["From"] = SENDER_EMAIL
            msg["To"] = email
            msg["Subject"] = "Updated Contract – RegulaAI"
            msg.set_content("Attached is the updated contract.")
            msg.add_attachment(pdf.read(), maintype="application", subtype="pdf", filename="updated_contract.pdf")

            try:
                with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
                    s.login(SENDER_EMAIL,SENDER_PASSWORD)
                    s.send_message(msg)
                st.success("📧 Email sent successfully")
            except Exception as e:
                st.error(e)

# ============================================================
# CHATBOT
# ============================================================
elif page == "💬 Chatbot":
    st.session_state.current_page = page
    c = st.session_state.active_contract

    if not c:
        st.warning("Select a contract first")
        st.stop()

    q = st.text_input("Ask a question about this contract")
    if st.button("Ask"):
        st.write("**AI:**", ask_groq(q, c["text"]))

# ============================================================
# END
# ============================================================
