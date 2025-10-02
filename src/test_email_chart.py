import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from dotenv import load_dotenv

load_dotenv()

ALERT_TO   = "mjcolon218@gmail.com"
ALERT_FROM = os.getenv("ALERT_FROM")
SMTP_HOST  = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER  = os.getenv("SMTP_USER", ALERT_FROM)
SMTP_PASS  = os.getenv("SMTP_PASS")

def send_email_with_attachment(subject, body, attachment_path):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"]    = ALERT_FROM
    msg["To"]      = ALERT_TO
    msg["Date"]    = formatdate(localtime=True)

    # Add body
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Add attachment if exists
    if os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment_path)}"')
        msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())
    print("✅ Email sent with chart attached to", ALERT_TO)

if __name__ == "__main__":
    send_email_with_attachment(
        "Test Signal Chart",
        "This is a test with a PNG chart attached.",
        "outputs/alerts/test_chart.png"   # path created in Step 2
    )
