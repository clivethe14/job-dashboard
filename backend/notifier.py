import os
import smtplib
from email.mime.text import MIMEText

RECIPIENTS = ["vanessavlewis2002@gmail.com", "cl11588p@gmail.com"]


def send_email(subject: str, body: str):
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")

    if not all([host, user, password]):
        print("[notifier] SMTP not configured, skipping email. Set SMTP_HOST/SMTP_USER/SMTP_PASSWORD in .env")
        return

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(RECIPIENTS)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, RECIPIENTS, msg.as_string())


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
