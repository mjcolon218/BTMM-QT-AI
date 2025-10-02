# src/email_utils.py
import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

def send_email(subject, body, to_addr, from_addr,
               smtp_host, smtp_port, smtp_user, smtp_pass,
               attachment=None):
    """
    Send an email with optional attachment (PNG chart).
    """

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)

    # Add text body
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Add attachment if provided
    if attachment and os.path.exists(attachment):
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(attachment)}"'
        )
        msg.attach(part)

    # Send via SMTP
    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"✅ Email sent to {to_addr} with attachment {attachment if attachment else '(no attachment)'}")
