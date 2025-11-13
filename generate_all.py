"""Build the bilingual news dataset consumed by the static front-end."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

from dateutil import parser as date_parser

from fetch_ai_news import gather, save_seen

try:  # Optional dependency, falls back gracefully when unavailable
    from googletrans import Translator  # type: ignore
except Exception:  # pragma: no cover - optional import guard
    Translator = None

# Buckets used by the layout
SECTION_TAGS = ("creators", "marketing", "bizdev")

# How many stories per section
N_PER_BUCKET = 5

# Keyword sets reused from the previous HTML generator. The scoring heuristic
# stays the same so we can keep a consistent editorial mix.
CREATORS_KW = {
    "stable diffusion",
    "midjourney",
    "runway",
    "comfyui",
    "automatic1111",
    "dall-e",
    "chatgpt",
    "gpt-4",
    "claude",
    "leonardo",
    "krea",
    "tensor",
    "pika",
    "veo",
    "kling",
    "sora",
    "luma",
    "animatediff",
    "openai",
    "anthropic",
    "prompt",
    "prompt engineering",
    "lora",
    "controlnet",
    "inpainting",
    "outpainting",
    "img2img",
    "txt2img",
    "video2video",
    "style transfer",
    "fine-tuning",
    "dreambooth",
    "embeddings",
    "workflow",
    "pipeline",
    "obraz",
    "image",
    "wideo",
    "video",
    "audio",
    "dźwięk",
    "muzyka",
    "3d",
    "model",
    "animacja",
    "generative",
    "gen-3",
    "gen-4",
    "multimodal",
    "twórca",
    "twórcy",
    "kreatywny",
    "grafika",
    "projekt",
    "design",
    "artysta",
    "sztuka",
    "art",
    "creative",
    "content",
    "treść",
    "kreator",
    "generowanie",
    "projektant",
    "ilustrator",
    "fotograf",
    "filmowiec",
    "montaż",
    "postprodukcja",
}

MARKETING_KW = {
    "kampania",
    "campaign",
    "marketing",
    "reklama",
    "ad",
    "ads",
    "advert",
    "promocja",
    "promotion",
    "brand",
    "branding",
    "wizerunek",
    "pr",
    "tiktok",
    "instagram",
    "facebook",
    "youtube",
    "x ",
    "twitter",
    "linkedin",
    "social media",
    "social",
    "post",
    "story",
    "reels",
    "short",
    "shorts",
    "viral",
    "trend",
    "hot",
    "popular",
    "engagement",
    "interakcja",
    "zasięg",
    "reach",
    "audience",
    "publiczność",
    "followers",
    "subscribers",
    "roi",
    "conversion",
    "ctr",
    "click",
    "impression",
    "analytics",
    "metrics",
    "statistics",
    "data",
    "insights",
    "performance",
    "results",
    "effectiveness",
    "influencer",
    "influencerka",
    "content creator",
    "twórca treści",
    "bloger",
    "vloger",
    "youtuber",
    "tiktoker",
    "case study",
    "przypadek",
    "studium",
    "success",
    "sukces",
    "konkurs",
    "competition",
    "giveaway",
    "nagroda",
    "fun",
    "zabawa",
    "rozrywka",
    "entertainment",
    "humor",
    "mem",
    "meme",
}

BIZDEV_KW = {
    "ustawa",
    "regulacja",
    "prawo",
    "law",
    "regulation",
    "compliance",
    "gdpr",
    "privacy",
    "prywatność",
    "license",
    "licencja",
    "copyright",
    "autorskie",
    "patent",
    "ip",
    "intellectual property",
    "własność intelektualna",
    "funding",
    "investment",
    "inwestycja",
    "venture",
    "vc",
    "seed",
    "series",
    "ipo",
    "stock",
    "giełda",
    "exchange",
    "m&a",
    "acquisition",
    "merger",
    "finanse",
    "finance",
    "revenue",
    "przychód",
    "profit",
    "zysk",
    "loss",
    "strata",
    "enterprise",
    "biznes",
    "business",
    "corporation",
    "firma",
    "company",
    "startup",
    "scaleup",
    "sme",
    "msme",
    "deweloper",
    "developer",
    "programista",
    "software",
    "oprogramowanie",
    "api",
    "sdk",
    "framework",
    "biblioteka",
    "cloud",
    "chmura",
    "aws",
    "azure",
    "gcp",
    "google cloud",
    "server",
    "serwer",
    "data center",
    "centrum danych",
    "hosting",
    "storage",
    "przechowywanie",
    "database",
    "baza danych",
    "sql",
    "nosql",
    "big data",
    "ai infrastructure",
    "polski",
    "polska",
    "warszawa",
    "kraków",
    "wrocław",
    "poznań",
    "gdańsk",
    "poland",
    "europe",
    "europa",
    "ue",
    "unia europejska",
    "grant",
    "dotacja",
    "subsidy",
    "fundusz",
    "fund",
    "accelerator",
    "akcelerator",
    "incubator",
    "inkubator",
    "government",
    "rząd",
    "ministry",
    "ministerstwo",
    "digital",
    "cyfryzacja",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80"

OUTPUT_DATA_PATH = Path("data/news.json")
OUTPUT_DOCS_PATH = Path("docs/data/news.json")

_TRANSLATOR = None


def _get_translator():
    global _TRANSLATOR
    if _TRANSLATOR is False:
        return None
    if _TRANSLATOR is None and Translator is not None:
        try:
            _TRANSLATOR = Translator()
        except Exception:
            _TRANSLATOR = False
    return None if _TRANSLATOR is False else _TRANSLATOR


def _translate_batch(texts: Sequence[str], dest: str = "en") -> List[Optional[str]]:
    translator = _get_translator()
    if not texts:
        return []
    if translator is None:
        return [None] * len(texts)

    translated_texts: List[Optional[str]] = []
    for text in texts:
        try:
            result = translator.translate(text, dest=dest)
        except Exception:
            translated_texts.append(None)
            continue
        translated_texts.append(getattr(result, "text", None))
    return translated_texts


def _ensure_translations(items: List[Dict[str, str]]) -> None:
    texts: List[str] = []
    lookup: List[Tuple[int, str]] = []
    for idx, item in enumerate(items):
        for key in ("title", "summary"):
            value = (item.get(key) or "").strip()
            if value:
                texts.append(value)
                lookup.append((idx, key))

    translations = _translate_batch(texts, dest="en") if texts else []

    for (idx, key), translated in zip(lookup, translations):
        english_value = translated or (items[idx].get(key) or "")
        items[idx][f"{key}_en"] = english_value


def score_for(bucket: str, item: Dict[str, str]) -> float:
    title = (item.get("title") or "")
    summ = (item.get("summary") or "")
    text = f"{title} {summ}".lower()
    score = 0.0
    if bucket == "creators":
        keywords = CREATORS_KW
    elif bucket == "marketing":
        keywords = MARKETING_KW
    else:
        keywords = BIZDEV_KW

    for keyword in keywords:
        if keyword in text:
            score += 2
    if item.get("summary"):
        score += 1
    score -= min(len(title), 140) / 200.0
    return score


def pick_top(
    items: Sequence[Dict[str, str]],
    bucket: str,
    n: int,
    already_used: Set[str],
    scorer,
) -> List[Dict[str, str]]:
    ranked = sorted(items, key=lambda it: scorer(bucket, it), reverse=True)
    chosen: List[Dict[str, str]] = []
    seen_domains: Set[str] = set()

    for article in ranked:
        link = article.get("link") or ""
        if not link or link in already_used:
            continue
        domain = link.split("/")[2] if "://" in link else link
        domain = domain.lower()
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        chosen.append(article)
        already_used.add(link)
        if len(chosen) >= n:
            break

    if len(chosen) < n:
        fallback = sorted(
            [x for x in items if (x.get("link") or "") not in already_used],
            key=lambda x: len(x.get("title", "")),
        )
        for article in fallback:
            link = article.get("link") or ""
            if not link:
                continue
            already_used.add(link)
            chosen.append(article)
            if len(chosen) >= n:
                break

    return chosen


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "article"


def _as_iso(value: str) -> str:
    try:
        parsed = date_parser.parse(value)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc).isoformat()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _domain_root(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        return url
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    if parsed.netloc:
        return f"https://{parsed.netloc}"
    return url


def _prepare_articles(raw_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    for item in raw_items:
        if not item.get("image"):
            item["image"] = DEFAULT_IMAGE
        if "published" in item:
            item["published"] = _as_iso(item["published"])
    raw_items.sort(key=lambda it: it.get("published", ""), reverse=True)
    return raw_items


def build_payload(raw_items: List[Dict[str, str]]) -> List[Dict[str, object]]:
    if not raw_items:
        return []

    working = _prepare_articles(list(raw_items))
    _ensure_translations(working)

    already_used: Set[str] = set()

    # Mark hero story
    hero = working[0]
    hero.setdefault("tags", set()).add("hero")
    hero_link = hero.get("link")
    if hero_link:
        already_used.add(hero_link)

    # Mark latest-in-brief block (excluding hero)
    for article in working[1:7]:
        link = article.get("link")
        if not link:
            continue
        article.setdefault("tags", set()).add("brief")
        already_used.add(link)

    # Section buckets
    for bucket in SECTION_TAGS:
        picks = pick_top(working, bucket, N_PER_BUCKET, already_used=already_used, scorer=score_for)
        for article in picks:
            article.setdefault("tags", set()).add(bucket)

    payload: List[Dict[str, object]] = []
    used_ids: Set[str] = set()
    for article in working:
        link = article.get("link") or ""
        title = article.get("title") or ""
        base_id = _slugify(title or link)
        candidate = base_id
        index = 2
        while candidate in used_ids:
            candidate = f"{base_id}-{index}"
            index += 1
        used_ids.add(candidate)

        tags = article.get("tags") or set()
        if isinstance(tags, set):
            tags = sorted(tags)

        payload.append(
            {
                "id": candidate,
                "source": article.get("source") or _domain_root(link),
                "sourceUrl": _domain_root(link),
                "title": title,
                "summary": article.get("summary") or "",
                "title_en": article.get("title_en") or title,
                "summary_en": article.get("summary_en") or article.get("summary") or "",
                "language": "pl",
                "publishedAt": article.get("published") or datetime.now(timezone.utc).isoformat(),
                "url": link,
                "imageUrl": article.get("image") or DEFAULT_IMAGE,
                "tags": tags,
            }
        )
    return payload


def write_payload(payload: List[Dict[str, object]], *, save_seen_urls: bool = True) -> None:
    OUTPUT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    with open(OUTPUT_DOCS_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    if save_seen_urls:
        save_seen([item.get("url", "") for item in payload if item.get("url")])


def generate(save_seen_urls: bool = True) -> List[Dict[str, object]]:
    items = gather()
    payload = build_payload(items)
    if not payload:
        return []
    write_payload(payload, save_seen_urls=save_seen_urls)
    return payload


def main() -> None:
    payload = generate(save_seen_urls=True)
    if not payload:
        print("Brak nowych artykułów w ostatnich 24h.")
        return
    print(f"Zapisano {len(payload)} artykułów do {OUTPUT_DATA_PATH}")


if __name__ == "__main__":
    main()
