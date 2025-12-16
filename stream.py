# stream.py - Full final version (greeting-aware chatbot + all features)
import streamlit as st
from datetime import datetime
import io
import os
import re
import PyPDF2
import smtplib
import pandas as pd
from email.message import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from dotenv import load_dotenv
from groq import Groq
import matplotlib.pyplot as plt

# ===========================================
# PAGE CONFIG
# ===========================================
st.set_page_config(page_title="RegulaAI – Compliance Checker", layout="wide")
st.title("✅ RegulaAI – Compliance Checker")
st.caption("AI-powered Contract Compliance & Risk Analysis System")

# ===========================================
# EMAIL CONFIG (replace with secure storage)
# ===========================================
SENDER_EMAIL = "smtp_gmail.com"
SENDER_PASSWORD = "password_from_env
# ===========================================
# LOAD ENV + GROQ SETUP
# ===========================================
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    st.error("❌ Missing GROQ_API_KEY in .env")
else:
    client = Groq(api_key=GROQ_KEY)

# ===========================================
# SESSION STATE
# ===========================================
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""

if "chat" not in st.session_state:
    st.session_state.chat = []

if "updated_contract" not in st.session_state:
    st.session_state.updated_contract = ""

# ===========================================
# PDF EXTRACT FUNCTION (ENCRYPTION FIXED)
# ===========================================
def extract_text_from_pdf(uploaded_file, limit_chars=16000):
    text = ""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
    except Exception as e:
        return f"❌ Error reading PDF: {e}"

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # try without password
        except Exception:
            return "⚠️ PDF is encrypted and cannot be processed without a password."

    for page in reader.pages:
        if len(text) > limit_chars:
            break
        try:
            content = page.extract_text()
        except Exception:
            content = None
        if content:
            text += content + "\n"

    return text[:limit_chars]

# ===========================================
# RISK CALCULATION
# ===========================================
def calculate_risk(text):
    score = 0
    risks = []

    low_text = text.lower()
    if "termination" in low_text:
        score += 20
        risks.append("Termination clause may cause contract imbalance.")
    if "liability" in low_text:
        score += 25
        risks.append("Liability clause requires review.")
    if "indemn" in low_text:
        score += 20
        risks.append("Indemnification clause contains high-risk terms.")
    if "gdpr" not in low_text and any(word in low_text for word in ["personal data", "data protection", "privacy"]):
        score += 15
        risks.append("Missing explicit GDPR/compliance section.")
    return score, risks

# ===========================================
# AI CHATBOT (greeting-aware, contract-aware)
# ===========================================
def ask_groq(question):
    try:
        now = datetime.now()
        lower_q = (question or "").lower()
        # detect if user explicitly wants date/time/day
        wants_datetime = any(kw in lower_q for kw in [
            "time", "date", "day", "today", "current time", "now", "which day", "what day", "what is the time"
        ])

        contract_text = st.session_state.contract_text if st.session_state.contract_text else "[NO CONTRACT UPLOADED]"

        if wants_datetime:
            # System prompt constrained to only answer with date/time info when asked
            system_context = f"""
You must answer accurately using the real system date/time provided below.
Do NOT include extra commentary unless the user asks for it.

Current Date: {now.strftime('%B %d, %Y')}
Day: {now.strftime('%A')}
Time (24-hour): {now.strftime('%H:%M:%S')}
Time (12-hour): {now.strftime('%I:%M:%S %p')}
Timezone: System Local Time

If the user asks about date/time/day, respond concisely with the requested value using the provided information.
If the user asks anything else in the same message, include both the date/time and then answer the other part.
"""
        else:
            # Full intelligent assistant behavior without forcing date/time responses
            system_context = f"""
You are RegulaAI — an AI Legal Assistant.

Behavior rules:
1. DO NOT mention date or time unless the user explicitly asks for it.
2. For greetings (hello, hi, hey), respond naturally, e.g. "Hello! How can I help you today?"
3. For contract-related requests, ALWAYS use the uploaded contract (below). If no contract present, respond: "Please upload a contract first."
4. For "summarize", "extract clauses", "show risks", "regulatory rules", or clause Q&A, analyze the contract and answer based on its content.
5. For "generate amendments", return modified clauses using [[UPDATED]]...[[/UPDATED]] for additions and [[REMOVED]]...[[/REMOVED]] for removals.
6. NEVER guess the date/time/day. If user asks for date/time/day, use system provided values only.

Contract text (may be "[NO CONTRACT UPLOADED]"):
{contract_text}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": question}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {e}"

# ===========================================
# Utility: draw updated PDF with underlines & strike-throughs
# ===========================================
def generate_highlighted_pdf(text_with_markers):
    PAGE_WIDTH, PAGE_HEIGHT = A4
    left_margin = 40
    right_margin = 40
    top_margin = PAGE_HEIGHT - 40
    line_height = 14  # points
    max_width = PAGE_WIDTH - left_margin - right_margin

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFont("Helvetica", 11)

    y = top_margin

    segment_re = re.compile(
        r'(\[\[UPDATED\]\].*?\[\[/UPDATED\]\]|\[\[REMOVED\]\].*?\[\[/REMOVED\]\]|\[?[^[]+)',
        flags=re.DOTALL
    )

    def wrap_text_to_chunks(s):
        words = s.split()
        if not words:
            return ['']
        lines = []
        cur = words[0]
        for w in words[1:]:
            test = cur + ' ' + w
            if pdf.stringWidth(test, "Helvetica", 11) <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    for raw_line in text_with_markers.split("\n"):
        if raw_line.strip() == "":
            y -= line_height
            if y < 40:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = top_margin
            continue

        segs = segment_re.findall(raw_line)
        styled_segments = []
        for seg in segs:
            seg = seg or ""
            seg = seg.replace("\r", "")
            if seg.startswith("[[UPDATED]]") and seg.endswith("[[/UPDATED]]"):
                inner = seg[len("[[UPDATED]]"):-len("[[/UPDATED]]")]
                styled_segments.append((inner, "updated"))
            elif seg.startswith("[[REMOVED]]") and seg.endswith("[[/REMOVED]]"):
                inner = seg[len("[[REMOVED]]"):-len("[[/REMOVED]]")]
                styled_segments.append((inner, "removed"))
            else:
                styled_segments.append((seg, "plain"))

        printable_lines = []
        current_line = []
        current_line_width = 0

        for seg_text, style in styled_segments:
            pieces = seg_text.split("\n")
            for pi, piece in enumerate(pieces):
                piece = piece if piece is not None else ""
                if piece == "":
                    piece_wrapped = ['']
                else:
                    piece_wrapped = wrap_text_to_chunks(piece)

                for wi, wpiece in enumerate(piece_wrapped):
                    draw_text = wpiece
                    # leading space logic
                    if current_line and not draw_text.startswith(" "):
                        test_text = " " + draw_text
                    else:
                        test_text = draw_text
                    test_width = pdf.stringWidth(test_text, "Helvetica", 11)
                    if current_line_width + test_width <= max_width:
                        if current_line and not draw_text.startswith(" "):
                            draw_text = " " + draw_text
                        current_line.append((draw_text, style))
                        current_line_width += pdf.stringWidth(draw_text, "Helvetica", 11)
                    else:
                        if current_line:
                            printable_lines.append(current_line)
                        current_line = [(draw_text, style)]
                        current_line_width = pdf.stringWidth(draw_text, "Helvetica", 11)
                if pi < len(pieces) - 1:
                    if current_line:
                        printable_lines.append(current_line)
                    current_line = []
                    current_line_width = 0

        if current_line:
            printable_lines.append(current_line)

        for pline in printable_lines:
            x = left_margin
            for seg_text, style in pline:
                if seg_text == "":
                    seg_text = ""
                if style == "plain":
                    pdf.setFillColorRGB(0, 0, 0)
                    pdf.drawString(x, y, seg_text)
                    tw = pdf.stringWidth(seg_text, "Helvetica", 11)
                    x += tw
                elif style == "updated":
                    pdf.setFillColorRGB(1, 0, 0)
                    pdf.drawString(x, y, seg_text)
                    tw = pdf.stringWidth(seg_text, "Helvetica", 11)
                    underline_y = y - 2
                    pdf.setLineWidth(0.9)
                    pdf.setStrokeColorRGB(1, 0, 0)
                    pdf.line(x, underline_y, x + tw, underline_y)
                    x += tw
                    pdf.setFillColorRGB(0, 0, 0)
                elif style == "removed":
                    pdf.setFillColorRGB(0.2, 0.2, 0.2)
                    pdf.drawString(x, y, seg_text)
                    tw = pdf.stringWidth(seg_text, "Helvetica", 11)
                    strike_y = y + 4
                    pdf.setLineWidth(1.0)
                    pdf.setStrokeColorRGB(1, 0, 0)
                    pdf.line(x, strike_y, x + tw, strike_y)
                    x += tw
                    pdf.setFillColorRGB(0, 0, 0)
            y -= line_height
            if y < 40:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = top_margin

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# ===========================================
# SIDEBAR NAVIGATION
# ===========================================
page = st.sidebar.radio(
    "Navigate",
    ["Upload Contract", "Risk Dashboard", "Regulatory Updates", "Amendment System", "AI Chatbot"]
)

# ===========================================
# PAGE 1 — UPLOAD CONTRACT
# ===========================================
if page == "Upload Contract":
    st.subheader("📤 Upload Contract Document")

    uploaded_file = st.file_uploader("Upload PDF contract", type=["pdf"])

    if uploaded_file:
        text = extract_text_from_pdf(uploaded_file)
        st.session_state.contract_text = text

        if text.startswith("⚠️") or text.startswith("❌"):
            st.error(text)
        else:
            st.success("✅ Contract uploaded successfully")
            risk_score, risks = calculate_risk(text)
            st.metric("Risk Level", "HIGH ⚠️" if risk_score > 50 else "MEDIUM")
            st.subheader("📄 Extracted Contract Content")
            st.text_area("Contract Text", text, height=350)

# ===========================================
# PAGE 2 — RISK DASHBOARD
# ===========================================
elif page == "Risk Dashboard":
    st.subheader("📊 Risk Dashboard")

    if not st.session_state.contract_text:
        st.warning("Please upload a contract first.")
        st.stop()

    risk_score, risks = calculate_risk(st.session_state.contract_text)

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", risk_score)
    col2.metric("Issues Found", len(risks))
    col3.metric("Compliance Level", "LOW" if risk_score > 60 else "MEDIUM")

    fig, ax = plt.subplots()
    ax.pie(
        [risk_score, max(0, 100 - risk_score)],
        labels=["Risk", "Safe"],
        autopct="%1.1f%%",
        startangle=90
    )
    st.pyplot(fig)

    st.subheader("⚠️ Detected Risks")
    if risks:
        for r in risks:
            st.error(r)
    else:
        st.success("No automated risks detected by the basic scanner.")

    risk_data = pd.DataFrame({
        "Risk Type": ["Termination", "Liability", "Indemnification", "Missing GDPR"],
        "Score": [
            20 if "termination" in st.session_state.contract_text.lower() else 0,
            25 if "liability" in st.session_state.contract_text.lower() else 0,
            20 if "indemn" in st.session_state.contract_text.lower() else 0,
            15 if "gdpr" not in st.session_state.contract_text.lower() else 0
        ]
    })

    st.subheader("📈 Risk Trend / Line Chart")
    st.line_chart(risk_data.set_index("Risk Type"))

    st.subheader("📘 Clause Analysis")
    st.table(pd.DataFrame({
        "Clause": ["Termination", "Liability", "Indemnification", "GDPR"],
        "Found": [
            "Yes" if "termination" in st.session_state.contract_text.lower() else "No",
            "Yes" if "liability" in st.session_state.contract_text.lower() else "No",
            "Yes" if "indemn" in st.session_state.contract_text.lower() else "No",
            "Yes" if "gdpr" in st.session_state.contract_text.lower() else "No"
        ]
    }))

    st.subheader("📊 Risk Comparison Chart")
    st.bar_chart(risk_data.set_index("Risk Type"))

    with st.expander("📄 Detailed Risk Data"):
        st.dataframe(risk_data)

# ===========================================
# PAGE 3 — REGULATORY UPDATES
# ===========================================
elif page == "Regulatory Updates":
    st.subheader("📜 Regulatory Update Monitor")

    if not st.session_state.contract_text:
        st.warning("⚠️ Please upload a contract first.")
        st.stop()

    st.info("🔍 Analyzing contract for regulatory requirements…")

    prompt = f"""
Read the following contract and extract ONLY the regulatory or compliance-related rules.

Contract:
{st.session_state.contract_text}

Return the rules as a numbered list.
"""

    result = ask_groq(prompt)

    st.success("✅ Regulatory rules extracted successfully")
    st.markdown("### 📌 Rules Identified from Contract")
    st.markdown(result)

# ===========================================
# PAGE 4 — AMENDMENT SYSTEM
# ===========================================
elif page == "Amendment System":
    if not st.session_state.contract_text:
        st.warning("⚠️ Please upload the original contract first")
        st.stop()

    st.subheader("🛠️ Smart Contract Amendment System")
    original_text = st.session_state.contract_text
    st.text_area("📄 Original Contract", original_text, height=220)
    st.write("---")

    receiver_email = st.text_input("📧 Enter email to send updated contract")

    if st.button("✨ Generate Updated Contract"):
        with st.spinner("Analyzing and updating…"):
            prompt = f"""
Improve clarity, grammar, and legal consistency of this contract.
When suggesting removals, wrap removed text with [[REMOVED]]...[[/REMOVED]].
When suggesting additions/updates, wrap added or modified text with [[UPDATED]]...[[/UPDATED]].
Do NOT add new obligations. Only refine what is present.

Contract:
{original_text}
"""
            updated = ask_groq(prompt)
        st.session_state.updated_contract = updated
        st.success("✅ Updated contract generated!")

    if st.session_state.updated_contract:
        st.subheader("📘 Updated Contract (Markers shown)")
        st.text_area("Updated Version (markers shown)", st.session_state.updated_contract, height=300)

    if st.button("📨 Send Updated Contract PDF"):
        if not receiver_email:
            st.warning("⚠️ Enter email address")
            st.stop()
        if not st.session_state.updated_contract:
            st.warning("⚠️ Generate the updated contract first")
            st.stop()

        pdf_buffer = generate_highlighted_pdf(st.session_state.updated_contract)

        msg = EmailMessage()
        msg["Subject"] = "Updated Contract – RegulaAI"
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg.set_content("Attached is the updated contract with highlighted changes.")

        msg.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename="updated_contract.pdf"
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            st.success("✅ Updated PDF sent to email successfully!")
        except Exception as e:
            st.error(f"❌ Email failed: {e}")

# ===========================================
# PAGE 5 — AI CHATBOT (Full intelligent mode)
# ===========================================
elif page == "AI Chatbot":
    st.subheader("🤖 AI Chatbot – Ask Anything")
    st.markdown("Ask contract-specific or general questions. If a contract is uploaded the assistant will use it automatically.")

    question = st.text_input("Ask a question:")

    # Quick helper buttons
    col_a, col_b, col_c, col_d = st.columns(4)
    if col_a.button("Summarize Contract"):
        question = "Summarize the contract"
    if col_b.button("Extract Clauses"):
        question = "Extract clauses from the contract"
    if col_c.button("Show Risks"):
        question = "Show risks in the contract"
    if col_d.button("Regulatory Rules"):
        question = "Extract regulatory/compliance rules from the contract"

    if st.button("Ask") and question:
        with st.spinner("Thinking…"):
            answer = ask_groq(question)
        st.session_state.chat.append((question, answer))

    # Chat history (most recent first)
    for q, a in reversed(st.session_state.chat):
        st.write(f"🧑 **You:** {q}")
        st.write(f"🤖 **AI:** {a}")
        st.write("---")