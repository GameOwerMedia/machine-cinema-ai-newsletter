#!/usr/bin/env python3
"""Utility invoked from the subscribe.yml workflow.

It inspects the issue payload, extracts fields from the issue form and
persists them to ``data/subscribers.txt``.  The script never fails the
workflow – instead it reports a JSON document describing what happened,
which the caller can inspect via workflow outputs.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

DATA_PATH = Path("data/subscribers.txt")
SECTION_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email": re.compile(r"### Email address\s*\n+([\s\S]*?)(?=\n### |\Z)", re.IGNORECASE),
    "name": re.compile(r"### Name \(optional\)\s*\n+([\s\S]*?)(?=\n### |\Z)", re.IGNORECASE),
    "source": re.compile(r"### How did you hear about us\?\s*\n+([\s\S]*?)(?=\n### |\Z)", re.IGNORECASE),
}
EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def extract_section(body: str, section: str) -> Optional[str]:
    pattern = SECTION_PATTERNS.get(section)
    if not pattern:
        return None
    match = pattern.search(body)
    if not match:
        return None
    value = match.group(1).strip()
    # Issue forms leave "_No response_" placeholders when a field is blank.
    if not value or value.lower() == "_no response_":
        return ""
    return value


def ensure_data_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        header = "# email|name|source|issue|added_at_utc\n"
        DATA_PATH.write_text(header, encoding="utf-8")


def append_if_new(email: str, name: str, source: str, issue_number: int) -> bool:
    ensure_data_file()
    lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
    emails = {ln.split("|", 1)[0].strip().lower() for ln in lines if ln and not ln.startswith("#")}
    if email.lower() in emails:
        return False
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = "|".join([
        email,
        name,
        source,
        f"#{issue_number}",
        timestamp,
    ])
    with DATA_PATH.open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")
    return True


def main(event_path: str) -> int:
    with open(event_path, "r", encoding="utf-8") as fh:
        event = json.load(fh)

    issue = event.get("issue", {})
    body = issue.get("body") or ""

    email_raw = (extract_section(body, "email") or "").strip()
    email = email_raw.lower()
    name = extract_section(body, "name") or ""
    source = extract_section(body, "source") or ""

    result: Dict[str, object] = {
        "status": "invalid",
        "email": email,
        "changes": False,
    }

    if not email or not EMAIL_RE.match(email):
        result.update({
            "status": "invalid",
            "reason": "missing_or_invalid_email",
        })
    else:
        issue_number = issue.get("number", 0)
        changed = append_if_new(email, name.strip(), source.strip(), issue_number)
        result.update({
            "status": "added" if changed else "duplicate",
            "changes": bool(changed),
            "name": name.strip(),
            "source": source.strip(),
        })

    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: handle_subscriber_issue.py <github_event_path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
