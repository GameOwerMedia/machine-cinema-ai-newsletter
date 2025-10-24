#!/usr/bin/env python3
"""Send the generated newsletter to all subscribers via SMTP.

The script expects credentials via environment variables (``SMTP_HOST``,
``SMTP_PORT``, ``SMTP_USERNAME``, ``SMTP_PASSWORD`` and ``SENDER_EMAIL``).
If any of them is missing, the script exits gracefully without failing the
pipeline, emitting an informational message instead.
"""
from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import markdown  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    markdown = None

SUBSCRIBERS_FILE = Path("data/subscribers.txt")
OUT_DIR = Path("out")


def discover_latest_markdown() -> Optional[Path]:
    if not OUT_DIR.exists():
        return None
    candidates = sorted(OUT_DIR.glob("*_ALL.md"))
    return candidates[-1] if candidates else None


def load_subscribers(path: Path) -> List[str]:
    if not path.exists():
        return []
    emails: List[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            email = line.split("|", 1)[0].strip()
            if email:
                emails.append(email)
    return emails


def build_message(markdown_path: Path, sender: str, recipients: Iterable[str], subject: Optional[str] = None) -> EmailMessage:
    md_source = markdown_path.read_text(encoding="utf-8")
    if subject is None:
        date_hint = markdown_path.stem.split("_", 1)[0]
        subject = f"Machine Cinema AI Newsletter — {date_hint}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = sender

    md_text = md_source.strip()
    msg.set_content(md_text)

    if markdown is not None:
        html_body = markdown.markdown(md_source, extensions=["tables", "fenced_code"])  # type: ignore[attr-defined]
        msg.add_alternative(html_body, subtype="html")

    msg["Bcc"] = ", ".join(recipients)
    return msg


def ensure_credentials() -> Optional[dict]:
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SENDER_EMAIL")
    port = int(os.environ.get("SMTP_PORT") or "587")

    if not all([host, user, password, sender]):
        print("SMTP credentials missing – skipping email delivery.")
        return None
    return {
        "host": host,
        "user": user,
        "password": password,
        "sender": sender,
        "port": port,
    }


def send(markdown_path: Path, subject: Optional[str] = None) -> None:
    creds = ensure_credentials()
    if creds is None:
        return

    recipients = load_subscribers(SUBSCRIBERS_FILE)
    if not recipients:
        print("No subscribers registered – skipping email delivery.")
        return

    message = build_message(markdown_path, creds["sender"], recipients, subject)

    with smtplib.SMTP(creds["host"], creds["port"]) as smtp:
        smtp.starttls()
        smtp.login(creds["user"], creds["password"])
        smtp.send_message(message, from_addr=creds["sender"], to_addrs=[creds["sender"], *recipients])
    print(f"Sent newsletter to {len(recipients)} subscribers.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send Machine Cinema newsletter emails")
    parser.add_argument("--markdown", dest="markdown", type=Path, default=None, help="Path to the markdown newsletter file")
    parser.add_argument("--subject", dest="subject", default=None, help="Optional email subject override")
    args = parser.parse_args()

    md_path = args.markdown or discover_latest_markdown()
    if md_path is None or not md_path.exists():
        print("No newsletter markdown found – skipping email delivery.")
        return 0

    send(md_path, subject=args.subject)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
