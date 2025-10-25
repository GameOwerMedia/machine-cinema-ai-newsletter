from __future__ import annotations

import logging
from argparse import Namespace
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List

from .config import Config, load_config
from .data_sources import Story, load_curated, load_live, sort_stories
from .html import write_outputs
from .segments import Section, plan_sections
from .seen import SeenCache

LOGGER = logging.getLogger(__name__)


class GenerationError(RuntimeError):
    """Raised when the generator cannot produce a newsletter."""


def run(args: Namespace, base_dir: Path | None = None) -> dict:
    base = base_dir or Path.cwd()
    config = load_config(base / getattr(args, "config", "sources.yml"))
    seen_cache = SeenCache(
        path=base / ".cache/seen.json",
        scope=args.seen_scope,
        ttl_days=args.seen_ttl,
        reset=args.reset_seen,
    )
    today = date.today()
    with seen_cache.acquire_lock(today):
        stories = _load_stories(args.mode, config)
        if not stories:
            raise GenerationError("Brak artykułów w wybranym trybie.")
        deduped = _dedupe(stories)
        ordered = sort_stories(deduped)
        available_links = [story.link for story in ordered]
        fresh_links = set(seen_cache.filter_new(available_links, today))
        fresh = [story for story in ordered if story.link in fresh_links]
        stale = [story for story in ordered if story.link not in fresh_links]
        candidates = fresh + stale
        sections = plan_sections(config, candidates)
        published_links = [story.link for section in sections for story in section.stories]
        if not published_links:
            raise GenerationError("Brak artykułów do publikacji po filtrach.")
        title = _title_for(today)
        write_outputs(
            today,
            title,
            sections,
            out_dir=base / "out",
            site_dir=base / "site",
        )
        seen_cache.remember(today, [link for link in published_links if link in fresh_links])
        return {
            "date": today.isoformat(),
            "title": title,
            "sections": _serialise_sections(sections),
            "published_count": len(published_links),
        }


def _load_stories(mode: str, config: Config) -> List[Story]:
    mode = (mode or "curated").lower()
    stories: List[Story] = []
    if mode == "curated":
        try:
            stories = load_curated(config)
        except FileNotFoundError:
            LOGGER.warning("Curated dataset missing, fallback to live mode")
            stories = load_live(config)
    elif mode == "live":
        stories = load_live(config)
    else:
        raise ValueError("mode must be 'curated' or 'live'")
    return stories


def _dedupe(stories: Iterable[Story]) -> List[Story]:
    seen = set()
    deduped: List[Story] = []
    for story in stories:
        if story.link in seen:
            continue
        seen.add(story.link)
        deduped.append(story)
    return deduped


def _title_for(day: date) -> str:
    return f"Newsletter AI — Machine Cinema Poland — {day.isoformat()}"


def _serialise_sections(sections: Iterable[Section]) -> List[dict]:
    return [
        {
            "title": section.title,
            "style": section.style,
            "stories": [story.serialise() for story in section.stories],
        }
        for section in sections
    ]
