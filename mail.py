import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
def send_email(to_email, subject, message):
    # 🔐 Sender email (your Gmail)
    from_email = os.getenv("SENDER_EMAIL")

    # 🔑 Gmail APP PASSWORD (16 characters, no spaces)
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        return True, "✅ Email sent successfully"
    except Exception as e:
        return False, f"❌ Error: {e}"


# ✅ TEST RUN (only runs when mail.py is executed directly)
if __name__ == "__main__":
    success, msg = send_email(
        to_email="springboardmentor533@gmail.com",
        subject="Hello from Python!",
        message="This is a test email sent using Python SMTP 🤖"
    )
    print(msg)
