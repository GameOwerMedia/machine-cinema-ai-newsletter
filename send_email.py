from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send the Machine Cinema AI newsletter via SMTP")
    parser.add_argument("--html", required=True, help="Path to the HTML file to send")
    parser.add_argument("--subject", default="Machine Cinema AI Newsletter", help="Email subject")
    parser.add_argument("--text", default=None, help="Optional plain-text alternative body")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    html_path = Path(args.html)
    if not html_path.exists():
        raise SystemExit(f"HTML file not found: {html_path}")

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("NEWSLETTER_FROM")
    recipient = os.getenv("NEWSLETTER_TO")

    if not all([host, username, password, sender, recipient]):
        raise SystemExit("Missing SMTP configuration. Ensure SMTP_* and NEWSLETTER_* variables are set.")

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = sender
    msg["To"] = recipient

    html_content = html_path.read_text(encoding="utf-8")
    if args.text:
        text_content = Path(args.text).read_text(encoding="utf-8")
    else:
        text_content = "Daily AI newsletter from Machine Cinema Poland."

    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)

    print(f"Newsletter sent to {recipient}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
