from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional

import yaml


DEFAULT_BUCKETS: Dict[str, Mapping[str, object]] = {
    "creators": {
        "label": "GenerativeAI creators",
        "style": "creators",
        "keywords": [
            "prompt",
            "workflow",
            "lora",
            "style",
            "comfyui",
            "stable diffusion",
            "sdxl",
            "veo",
            "runway",
            "kling",
            "pika",
            "krea",
            "midjourney",
            "gen-3",
            "controlnet",
            "inpainting",
            "outpainting",
            "frame",
            "storyboard",
            "editor",
            "video generation",
            "image-to-video",
            "ip-adapter",
            "rag video",
            "image",
            "video",
            "audio",
            "media",
        ],
    },
    "marketing": {
        "label": "Marketing / fun",
        "style": "marketing",
        "keywords": [
            "campaign",
            "marketing",
            "ads",
            "reklama",
            "brand",
            "viral",
            "trend",
            "influencer",
            "case study",
            "cmo",
            "konkurs",
            "social",
            "mem",
            "fun",
            "creative",
            "tiktok",
            "instagram",
            "youtube",
            "x ",
        ],
    },
    "bizdev": {
        "label": "Biznes & dev",
        "style": "bizdev",
        "keywords": [
            "ustawa",
            "regulacja",
            "prawo",
            "funding",
            "seed",
            "series",
            "ipo",
            "m&a",
            "nvidia",
            "tsmc",
            "intel",
            "amd",
            "factory",
            "fabryka",
            "data center",
            "cloud",
            "sla",
            "api",
            "sdk",
            "benchmark",
            "latency",
            "throughput",
            "token",
            "enterprise",
            "security",
            "compliance",
            "eu ai act",
            "governance",
            "llm",
            "invest",
            "inwestycja",
            "rynek",
            "biznes",
            "deweloper",
            "developer",
            "stack",
        ],
    },
}


@dataclass
class NewsletterSettings:
    per_bucket: int = 5
    mode: str = "segments"  # segments | top
    buckets: Dict[str, Mapping[str, object]] = field(
        default_factory=lambda: copy.deepcopy(DEFAULT_BUCKETS)
    )

    def validate(self) -> None:
        if self.per_bucket < 1:
            raise ValueError("newsletter.per_bucket must be >= 1")
        if self.mode not in {"segments", "top"}:
            raise ValueError("newsletter.mode must be 'segments' or 'top'")
        for bucket, info in self.buckets.items():
            if "label" not in info:
                raise ValueError(f"Bucket '{bucket}' must define a label")
            if "style" not in info:
                raise ValueError(f"Bucket '{bucket}' must define a style")
            keywords = info.get("keywords")
            if keywords is not None and not isinstance(keywords, Iterable):
                raise ValueError(f"Bucket '{bucket}' keywords must be iterable")


@dataclass
class CuratedSource:
    path: Path = Path("data/news.json")


@dataclass
class LiveFeed:
    name: str
    url: str
    kind: str = "rss"  # rss | google
    query: Optional[str] = None


@dataclass
class LiveSettings:
    feeds: List[LiveFeed] = field(default_factory=list)


@dataclass
class Config:
    newsletter: NewsletterSettings = field(default_factory=NewsletterSettings)
    curated: CuratedSource = field(default_factory=CuratedSource)
    live: LiveSettings = field(default_factory=LiveSettings)


def _deep_update(base: MutableMapping[str, object], updates: Mapping[str, object]) -> None:
    for key, value in updates.items():
        if key in base and isinstance(base[key], MutableMapping) and isinstance(value, Mapping):
            _deep_update(base[key], value)  # type: ignore[arg-type]
        else:
            base[key] = value  # type: ignore[index]


def _load_raw_config(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}
    if not isinstance(payload, Mapping):
        raise ValueError("sources.yml must contain a mapping at the top level")
    return payload


def load_config(config_path: Path | None = None) -> Config:
    path = config_path or Path("sources.yml")
    raw_defaults: Dict[str, object] = {
        "newsletter": {
            "per_bucket": 5,
            "mode": "segments",
            "buckets": copy.deepcopy(DEFAULT_BUCKETS),
        },
        "curated": {"path": str(CuratedSource().path)},
        "live": {
            "feeds": [
                {
                    "name": "Google AI",
                    "kind": "google",
                    "query": "artificial intelligence",
                    "url": "https://news.google.com/rss/search?q=Artificial+Intelligence&hl=en-US&gl=US&ceid=US:en",
                }
            ]
        },
    }
    overrides = _load_raw_config(path)
    merged = copy.deepcopy(raw_defaults)
    _deep_update(merged, overrides)

    newsletter_cfg = NewsletterSettings(
        per_bucket=int(merged["newsletter"].get("per_bucket", 5)),
        mode=str(merged["newsletter"].get("mode", "segments")),
        buckets=copy.deepcopy(merged["newsletter"].get("buckets", DEFAULT_BUCKETS)),
    )
    newsletter_cfg.validate()

    curated_cfg = CuratedSource(path=Path(str(merged["curated"].get("path", "data/news.json"))))

    feeds_data = merged.get("live", {}).get("feeds", [])
    feeds: List[LiveFeed] = []
    if isinstance(feeds_data, Iterable):
        for entry in feeds_data:
            if not isinstance(entry, Mapping):
                continue
            name = str(entry.get("name") or entry.get("url") or "feed")
            url = str(entry.get("url") or "")
            if not url:
                continue
            kind = str(entry.get("kind") or "rss").lower()
            query = entry.get("query")
            feeds.append(LiveFeed(name=name, url=url, kind=kind, query=query))

    live_cfg = LiveSettings(feeds=feeds)

    return Config(newsletter=newsletter_cfg, curated=curated_cfg, live=live_cfg)
