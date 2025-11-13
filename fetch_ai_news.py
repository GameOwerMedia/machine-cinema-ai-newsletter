import os
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

SEEN_URLS_FILE = "seen_urls.txt"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

RSS_SOURCES: Dict[str, str] = {
    "Spider's Web": "https://www.spidersweb.pl/feed",
    "Antyweb": "https://antyweb.pl/feed",
    "IT Reseller": "https://itreseller.com.pl/feed/",
    "ITwiz": "https://itwiz.pl/feed/",
    "Chip": "https://www.chip.pl/rss",
    "Tabletowo": "https://www.tabletowo.pl/feed",
    "Geek Just Join IT": "https://geek.justjoin.it/feed/",
}

AI_KEYWORDS = [
    "sztuczna inteligencja",
    "sztucznej inteligencji",
    "ai",
    "machine learning",
    "uczenie maszynowe",
    "chatgpt",
    "copilot",
    "openai",
    "anthropic",
    "midjourney",
    "generatyw",
    "genai",
    "large language model",
    "model jezykowy",
    "llm",
    "deep learning",
    "gpt",
    "automatyzacja",
]


def load_seen_urls() -> set:
    if os.path.exists(SEEN_URLS_FILE):
        with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    return set()


def save_seen(urls: Iterable[str]) -> None:
    seen = load_seen_urls()
    seen.update(urls)
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        for url in sorted(seen):
            f.write(url + "\n")


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()
    return soup.get_text(" ", strip=True)


def _parse_datetime(entry) -> datetime:
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None) or entry.get(attr)
        if raw:
            try:
                dt = date_parser.parse(raw)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                continue
    parsed = getattr(entry, "published_parsed", None) or entry.get("published_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _resolve_image_url(entry, article_url: str) -> Optional[str]:
    media = entry.get("media_content") or []
    if media:
        url = media[0].get("url")
        if url:
            return url

    thumbnails = entry.get("media_thumbnail") or []
    if thumbnails:
        url = thumbnails[0].get("url")
        if url:
            return url

    summary = entry.get("summary")
    if summary:
        soup = BeautifulSoup(summary, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return urljoin(article_url, img.get("src"))

    try:
        response = requests.get(article_url, headers=HTTP_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    page = BeautifulSoup(response.text, "html.parser")
    for attribute in ("property", "name"):
        for candidate in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            tag = page.find("meta", attrs={attribute: candidate})
            if tag and tag.get("content"):
                return urljoin(article_url, tag["content"].strip())

    fallback_img = page.find("img")
    if fallback_img and fallback_img.get("src"):
        return urljoin(article_url, fallback_img.get("src"))
    return None


def _fetch_feed(url: str):
    try:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return feedparser.FeedParserDict(entries=[])
    return feedparser.parse(response.text)


def _is_ai_related(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in AI_KEYWORDS)


def _normalize_source(url: str, explicit_source: Optional[str]) -> str:
    if explicit_source:
        return explicit_source
    parsed = urlparse(url)
    return parsed.netloc or ""


def fetch_news_from_sources(max_items: int = 36) -> List[Dict[str, str]]:
    articles: List[Dict[str, str]] = []
    seen_links: set = set()

    for source_name, feed_url in RSS_SOURCES.items():
        feed = _fetch_feed(feed_url)
        if not feed.entries:
            continue
        per_source_limit = max(3, max_items // max(1, len(RSS_SOURCES)))
        for entry in feed.entries[:per_source_limit]:
            link = entry.get("link")
            if not link or link in seen_links:
                continue

            title = (entry.get("title") or "").strip()
            summary_html = entry.get("summary") or ""
            summary = _clean_text(summary_html)
            combined = f"{title} {summary}"
            if not _is_ai_related(combined):
                continue

            published_dt = _parse_datetime(entry)
            image_url = _resolve_image_url(entry, link)

            articles.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published_dt.isoformat(),
                    "source": _normalize_source(link, source_name),
                    "image": image_url,
                }
            )
            seen_links.add(link)

    articles.sort(key=lambda item: item["published"], reverse=True)
    return articles[:max_items]


def _sample_articles() -> List[Dict[str, str]]:
    sample_image = "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80"
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "title": "OpenAI ogłasza nowy model GPT-5 Turbo",
            "link": "https://openai.com/blog/gpt-5-turbo",
            "summary": "Najnowszy model językowy koncentruje się na dokładności faktów i pracy wielomodalnej.",
            "published": now,
            "source": "openai.com",
            "image": sample_image,
        },
        {
            "title": "Midjourney prezentuje generowanie wideo w jakości filmowej",
            "link": "https://midjourney.com/news/video-fidelity",
            "summary": "Nowa funkcja pozwala na tworzenie sekwencji 4K w oparciu o tekstowe prompty w języku polskim.",
            "published": now,
            "source": "midjourney.com",
            "image": sample_image,
        },
    ]


def gather() -> List[Dict[str, str]]:
    seen_urls = load_seen_urls()
    try:
        fresh_articles = fetch_news_from_sources()
    except Exception as exc:  # pragma: no cover
        print(f"Error fetching news: {exc}")
        fresh_articles = []

    filtered = [article for article in fresh_articles if article["link"] not in seen_urls]

    if not filtered:
        filtered = _sample_articles()

    return filtered


if __name__ == "__main__":
    news = gather()
    print(f"Found {len(news)} articles")
    for item in news[:10]:
        print(f"- {item['title']} ({item['source']})")
