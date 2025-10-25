from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urlparse

import feedparser
import requests
from dateutil import parser as date_parser

from .config import Config, LiveFeed

LOGGER = logging.getLogger(__name__)


@dataclass
class Story:
    title: str
    summary: str
    link: str
    source: str
    published: Optional[datetime]
    raw_link: Optional[str] = None

    def serialise(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "source": self.source,
            "published": self.published.isoformat() if self.published else None,
        }


def normalise_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if not dt.tzinfo:
        return dt
    return dt.astimezone()


def load_curated(config: Config) -> List[Story]:
    path = config.curated.path
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh) or []
    stories: List[Story] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        link = str(raw.get("link") or "").strip()
        if not link:
            continue
        title = (raw.get("title") or "").strip() or "Untitled update"
        summary = (raw.get("summary") or raw.get("description") or "").strip()
        source = (raw.get("source") or "").strip() or urlparse(link).netloc or "source"
        published = raw.get("published") or raw.get("date")
        stories.append(
            Story(
                title=title,
                summary=summary,
                link=link,
                source=source,
                published=normalise_datetime(published),
            )
        )
    return stories


def _build_google_url(feed: LiveFeed) -> str:
    if feed.url:
        return feed.url
    query = feed.query or "artificial intelligence"
    encoded = requests.utils.quote(query)
    return (
        "https://news.google.com/rss/search?q="
        f"{encoded}&hl=en-US&gl=US&ceid=US:en"
    )


def _resolve_google_link(entry_link: str) -> Optional[str]:
    parsed = urlparse(entry_link)
    if "news.google.com" not in parsed.netloc:
        return None
    qs = parse_qs(parsed.query)
    candidate = qs.get("url") or qs.get("q")
    if candidate:
        return candidate[0]
    return None


def _resolve_canonical(url: str, timeout: float = 6.0) -> Optional[str]:
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "MachineCinemaBot/1.0"})
    except requests.RequestException as exc:
        LOGGER.debug("Canonical resolution failed for %s: %s", url, exc)
        return None
    final_url = response.url
    if not final_url:
        return None
    if final_url.startswith("http"):
        return final_url
    return None


def _extract_summary(entry) -> str:
    summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
    if isinstance(summary, str):
        return summary.strip()
    return ""


def _story_from_entry(entry, feed: LiveFeed) -> Optional[Story]:
    link = getattr(entry, "link", "") or getattr(entry, "id", "")
    if not link:
        return None
    title = getattr(entry, "title", "").strip() or "Untitled update"
    summary = _extract_summary(entry)
    published = None
    if getattr(entry, "published", None):
        published = normalise_datetime(entry.published)
    elif getattr(entry, "updated", None):
        published = normalise_datetime(entry.updated)

    raw_source = getattr(entry, "source", None)
    source = getattr(raw_source, "title", None) if raw_source else None
    if not source:
        source = urlparse(link).netloc or feed.name

    resolved_link: Optional[str] = None
    if feed.kind == "google":
        candidate = _resolve_google_link(link)
        if candidate:
            resolved_link = _resolve_canonical(candidate) or candidate
    else:
        resolved_link = _resolve_canonical(link)

    final_link = resolved_link or link
    return Story(
        title=title,
        summary=summary,
        link=final_link,
        source=source,
        published=published,
        raw_link=link,
    )


def load_live(config: Config) -> List[Story]:
    stories: List[Story] = []
    session_feeds = config.live.feeds or []
    for feed in session_feeds:
        url = _build_google_url(feed) if feed.kind == "google" else feed.url
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.warning("Nie udało się pobrać feedu %s: %s", feed.name, exc)
            continue
        if getattr(parsed, "bozo_exception", None):
            LOGGER.debug("Feed %s bozo_exception: %s", feed.name, parsed.bozo_exception)
        entries = getattr(parsed, "entries", [])
        for entry in entries:
            story = _story_from_entry(entry, feed)
            if story:
                stories.append(story)
    return stories


def sort_stories(stories: Iterable[Story]) -> List[Story]:
    return sorted(
        stories,
        key=lambda item: item.published or datetime.min,
        reverse=True,
    )
