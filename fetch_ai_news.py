"""Compatibility layer around the new newsletter package."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, List

from newsletter.config import load_config
from newsletter.data_sources import load_curated
from newsletter.seen import SeenCache


def gather(config_path: str | None = None) -> List[dict]:
    """Return curated stories for backwards compatibility."""
    config = load_config(Path(config_path) if config_path else None)
    stories = load_curated(config)
    return [story.serialise() for story in stories]


def save_seen(urls: Iterable[str], scope: str = "rolling") -> None:
    cache = SeenCache(scope=scope)
    today = date.today()
    cache.remember(today, urls)
