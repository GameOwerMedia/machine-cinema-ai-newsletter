"""Rendering helpers for newsletter entries."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from urllib.parse import urlparse

STYLE_ICONS = {
    "creators": "🎨",
    "marketing": "📣",
    "bizdev": "💼",
}


def _format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _normalise_summary(summary: str | None) -> str:
    if not summary:
        return ""
    return " ".join(part.strip() for part in summary.splitlines() if part.strip())


def format_post(item: Dict[str, Any], style: str = "creators") -> str:
    """Format a story dictionary into markdown expected by ``generate_all``."""
    icon = STYLE_ICONS.get(style, "🧠")

    title = (item.get("title") or "Untitled update").strip()
    link = (item.get("link") or "").strip()
    summary = _normalise_summary(item.get("summary"))
    source = (item.get("source") or "").strip()
    published = _format_date(item.get("published"))

    if not source and link:
        parsed = urlparse(link)
        source = parsed.netloc

    headline = f"{icon} [{title}]({link})" if link else f"{icon} {title}"

    metadata_parts = [part for part in (source, published) if part]
    if metadata_parts:
        headline = f"{headline} — {' • '.join(metadata_parts)}"

    if summary:
        return f"{headline}\n> {summary}"
    return headline

