import os
import smtplib
from email.mime.text import MIMEText

DEFAULT_RECIPIENTS = ["vanessavlewis2002@gmail.com", "cl11588p@gmail.com"]


def get_recipients() -> list[str]:
    # Override the recipient list without touching code by setting MAIL_TO in .env
    # (comma-separated). Falls back to DEFAULT_RECIPIENTS when unset.
    raw = os.environ.get("MAIL_TO", "")
    addrs = [a.strip() for a in raw.split(",") if a.strip()]
    return addrs or DEFAULT_RECIPIENTS


def send_email(subject: str, body: str):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    # Gmail shows App Passwords in 4 space-separated groups; strip whitespace so
    # a pasted "aoux wgqb hnqw mpom" authenticates the same as the 16-char form.
    password = (os.environ.get("SMTP_PASSWORD") or "").replace(" ", "")

    if not all([host, user, password]):
        print("[notifier] SMTP not configured, skipping email. Set SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env")
        return

    recipients = get_recipients()
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())


def notify_new_jobs(jobs: list[dict]):
    if not jobs:
        return
    lines = [f"<b>{len(jobs)} new job posting(s) found:</b><br><br>"]
    for j in jobs:
        lines.append(
            f"<b>{j['company']}</b> — {j['title']} ({j.get('location', '')})<br>"
            f"<a href='{j['url']}'>{j['url']}</a><br><br>"
        )
    body = "".join(lines)
    subject = f"{len(jobs)} new job posting(s) — Job Dashboard"
    send_email(subject, body)
