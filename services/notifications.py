"""Digest-building and send logic for watering reminders.

Sending is split into small functions (send_sms, send_email) so that
swapping the local implementations for AWS SNS/SES later only requires
changing the body of these two functions - callers are unaffected.
"""
import os
import smtplib
import uuid
from email.mime.text import MIMEText


def send_sms(phone_number, message):
    """Stubbed SMS send - prints/logs instead of calling a real carrier.

    Swap this out for a boto3 SNS `publish` call later.
    """
    print(f"[SMS to {phone_number}] {message}")
    return True


def send_email(to_address, subject, body):
    """Sends email via local SMTP if configured, otherwise stubs (prints).

    Swap this out for a boto3 SES `send_email` call later.
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_address = os.environ.get("SMTP_FROM", smtp_user or "noreply@example.com")

    if not smtp_host:
        print(f"[EMAIL to {to_address}] Subject: {subject}\n{body}")
        return True

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address

    with smtplib.SMTP(smtp_host, int(smtp_port or 587)) as server:
        server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.sendmail(from_address, [to_address], msg.as_string())
    return True


def build_sms_digest(thirsty_plants):
    names = [p["name"] for p in thirsty_plants]
    count = len(names)
    if count == 1:
        return f"1 plant needs water today: {names[0]}."
    return f"{count} plants need water today: {', '.join(names)}."


def build_email_digest(thirsty_plants):
    lines = ["The following plants need watering:", ""]
    for p in thirsty_plants:
        lines.append(
            f"- {p['name']} ({p['species']}): last watered "
            f"{p['last_watered_at']}, due {p['next_due_date']}, "
            f"{p['days_overdue']} day(s) overdue"
        )
    return "\n".join(lines)


def new_digest_id():
    return uuid.uuid4().hex
