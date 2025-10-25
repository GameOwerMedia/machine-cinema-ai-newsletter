from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import urlparse

from .config import Config
from .data_sources import Story


@dataclass
class Section:
    title: str
    stories: List[Story]
    style: str


def _normalise_keywords(keywords: Iterable[str] | None) -> List[str]:
    if not keywords:
        return []
    return [kw.lower() for kw in keywords]


def _score(bucket: str, story: Story, keywords: Sequence[str]) -> float:
    text = f"{story.title} {story.summary}".lower()
    score = 0.0
    for kw in keywords:
        if kw in text:
            score += 2.0
    if story.summary:
        score += 1.0
    score -= min(len(story.title), 140) / 200.0
    return score


def _domain(story: Story) -> str:
    parsed = urlparse(story.link)
    netloc = parsed.netloc or story.link.split("/")[0]
    return netloc.lower()


def plan_sections(config: Config, stories: List[Story]) -> List[Section]:
    per_bucket = config.newsletter.per_bucket
    if config.newsletter.mode == "top":
        return [_plan_top(config, stories, per_bucket)]
    return _plan_segments(config, stories, per_bucket)


def _plan_segments(config: Config, stories: List[Story], per_bucket: int) -> List[Section]:
    used_links = set()
    sections: List[Section] = []
    for bucket_name, meta in config.newsletter.buckets.items():
        keywords = _normalise_keywords(meta.get("keywords"))
        ranked = sorted(
            stories,
            key=lambda story: (_score(bucket_name, story, keywords), story.published_rank()),
            reverse=True,
        )
        chosen, _ = _pick_with_diversity(ranked, per_bucket, used_links)
        sections.append(
            Section(
                title=str(meta.get("label", bucket_name.title())),
                stories=chosen,
                style=str(meta.get("style", bucket_name)),
            )
        )
    return sections


def _plan_top(config: Config, stories: List[Story], limit: int) -> Section:
    bucket_keywords = {
        bucket: _normalise_keywords(meta.get("keywords"))
        for bucket, meta in config.newsletter.buckets.items()
    }
    ranked = sorted(
        stories,
        key=lambda story: (
            max(
                (_score(bucket, story, keywords) for bucket, keywords in bucket_keywords.items()),
                default=0.0,
            ),
            story.published_rank(),
        ),
        reverse=True,
    )
    chosen, _ = _pick_with_diversity(ranked, limit, set())
    return Section(title="Top stories", stories=chosen, style="top")


def _pick_with_diversity(ranked: List[Story], limit: int, used_links: set[str]) -> Tuple[List[Story], set[str]]:
    chosen: List[Story] = []
    used_domains: set[str] = set()
    for story in ranked:
        if story.link in used_links:
            continue
        domain = _domain(story)
        if domain in used_domains:
            continue
        used_domains.add(domain)
        used_links.add(story.link)
        chosen.append(story)
        if len(chosen) >= limit:
            return chosen, used_domains
    if len(chosen) < limit:
        for story in ranked:
            if story.link in used_links:
                continue
            used_links.add(story.link)
            chosen.append(story)
            if len(chosen) >= limit:
                break
    return chosen[:limit], used_domains
