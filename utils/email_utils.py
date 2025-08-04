import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import traceback

load_dotenv()

SMTP_KEY = os.getenv("SMTP_KEY")
SENDER_EMAIL = "syayidabdann@gmail.com"

# print("📡 SMTP_KEY:", SMTP_KEY)
# print("📨 SENDER_EMAIL:", SENDER_EMAIL)

def send_email(receiver_email: str, subject: str, content: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg.set_content(content, subtype="html")

        with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SMTP_KEY)
            server.send_message(msg)

        print("✅ Email sent successfully")
        return True

    except Exception as e:
        traceback.print_exc()
        print("❌ Failed to send email:", e)
        return False

def send_verification_email(receiver_email: str, token: str):
    subject = "Verifikasi Email Akun Anda"
    verify_link = f"http://localhost:8000/verify-email?token={token}"

    content = f"""
    <html>
        <body>
            <p>Halo 👋,<br><br>
            Terima kasih telah mendaftar. Silakan klik tombol di bawah ini untuk memverifikasi email Anda:<br><br>
            <a href="{verify_link}" style="padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none;">Verifikasi Email</a><br><br>
            Jika tombol tidak bekerja, salin dan tempel tautan ini ke browser Anda:<br>
            {verify_link}
            <br><br>Salam,<br>Tim Syayid
            </p>
        </body>
    </html>
    """
    return send_email(receiver_email, subject, content)
