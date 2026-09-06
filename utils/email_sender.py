"""Optional SMTP helper. Email is skipped when configuration is missing."""

import smtplib
from email.message import EmailMessage

from flask import current_app


def email_is_configured():
    config = current_app.config
    return bool(config.get("SMTP_HOST") and config.get("MAIL_FROM"))


def send_email(to_address, subject, body):
    """Send a plain-text email. Returns True on success, False if skipped or failed."""
    if not to_address:
        return False
    if not email_is_configured():
        return False

    config = current_app.config
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config["MAIL_FROM"]
    message["To"] = to_address
    message.set_content(body)

    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=10) as smtp:
            if config.get("SMTP_USE_TLS", True):
                smtp.starttls()
            username = config.get("SMTP_USERNAME")
            password = config.get("SMTP_PASSWORD")
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
        return True
    except Exception:
        return False
