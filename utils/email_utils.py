import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import traceback

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")           # smtp.ethereal.email
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))     # 587
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")                  # dari Ethereal
SENDER_EMAIL = os.getenv("SENDER_EMAIL")         # email ethereal

def send_email(to_email: str, subject: str, body: str):
    # DEBUG: Tampilkan isi email ke terminal
    print("\n📧 Simulated Email")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("Body:")
    print(body)
    print("=============================\n")

    # Tetap kirim email seperti biasa
    message = EmailMessage()
    message["From"] = SENDER_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body, subtype="html")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def send_verification_email(receiver_email: str, token: str):
    subject = "Verifikasi Email Akun Anda"
    verify_link = f"http://localhost:8000/users/verify-email?token={token}"

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
