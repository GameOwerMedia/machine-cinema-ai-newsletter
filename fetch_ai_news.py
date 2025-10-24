"""Utilities for fetching AI news stories for the Machine Cinema newsletter.

This module keeps the fetching logic intentionally lightweight so the
newsletter can be generated deterministically during local development
and continuous integration runs.  The production pipeline aggregates
stories from several APIs; here we reuse the curated dataset checked into
``data/news.json`` and maintain a cache of URLs we
have already used.  ``generate_all.py`` calls :func:`gather` to retrieve
fresh items and :func:`save_seen` to persist which URLs were processed.

The module focuses on delivering dictionaries that contain the
information required by the downstream formatter:

``{"title", "summary", "link", "source", "published"}``

``published`` is normalized to an ISO timestamp string when possible so
other parts of the system can rely on consistent metadata.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any, Set
from urllib.parse import urlparse

DATASET_PATH = Path("data/news.json")
CACHE_PATH = Path(".cache/seen.json")


def _load_seen() -> Set[str]:
    """Return the set of URLs that were already processed."""
    if not CACHE_PATH.exists():
        return set()
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if isinstance(payload, list):
            return {str(x) for x in payload}
    except json.JSONDecodeError:
        # Corrupted cache – start fresh.
        return set()
    return set()


def _normalise_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Return a normalised copy of the incoming story dictionary."""
    link = item.get("link")
    if not link:
        raise ValueError("Each item must contain a 'link' field.")

    title = (item.get("title") or "").strip() or "Untitled update"
    summary = (item.get("summary") or item.get("description") or "").strip()
    source = (item.get("source") or "").strip()
    if not source:
        parsed = urlparse(link)
        source = parsed.netloc or "source"

    published_raw = item.get("published") or item.get("date")
    published = None
    if isinstance(published_raw, str):
        published = _parse_datetime(published_raw)
    elif isinstance(published_raw, (int, float)):
        published = datetime.fromtimestamp(float(published_raw))

    return {
        "title": title,
        "summary": summary,
        "link": link,
        "source": source,
        "published": published.isoformat() if isinstance(published, datetime) else None,
    }


def _parse_datetime(value: str) -> datetime | None:
    """Parse a timestamp into a :class:`datetime` when possible."""
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def gather() -> List[Dict[str, Any]]:
    """Collect fresh items for the newsletter.

    The function reads the curated dataset, removes URLs that have already
    been marked as "seen" and returns the remaining items ordered from the
    most recent to the oldest based on their ``published`` timestamp.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {DATASET_PATH}. Ensure sample data is available."
        )

    with DATASET_PATH.open("r", encoding="utf-8") as fh:
        raw_items = json.load(fh)

    seen = _load_seen()
    normalised: List[Dict[str, Any]] = []
    for raw in raw_items:
        try:
            item = _normalise_item(raw)
        except ValueError:
            # Skip malformed entries silently so a single bad record does not
            # break the entire generation pipeline.
            continue
        if item["link"] in seen:
            continue
        normalised.append(item)

    def _sort_key(entry: Dict[str, Any]):
        published = entry.get("published")
        if published:
            try:
                return datetime.fromisoformat(published)
            except ValueError:
                pass
        return datetime.min

    normalised.sort(key=_sort_key, reverse=True)
    return normalised


def save_seen(urls: Iterable[str]) -> None:
    """Persist the provided URLs to the cache file.

    The function merges new URLs with the existing cache and stores the
    resulting list sorted for deterministic output.
    """
    seen = _load_seen()
    for url in urls:
        if url:
            seen.add(str(url))

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(sorted(seen), fh, ensure_ascii=False, indent=2)

