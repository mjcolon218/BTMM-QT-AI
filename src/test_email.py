import os, smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from dotenv import load_dotenv

load_dotenv(override=True)

ALERT_TO   = "mjcolon218@gmail.com"
ALERT_FROM = os.getenv("ALERT_FROM", "mjcolon218@gmail.com")
SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", ALERT_FROM)
SMTP_PASS  = os.getenv("SMTP_PASS")

def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = ALERT_FROM
    msg["To"]      = ALERT_TO
    msg["Date"]    = formatdate(localtime=True)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())
    print("✅ Email sent to", ALERT_TO)

if __name__ == "__main__":
    send_email("Test Signal Alert", "This is just a test from your trading bot.")
