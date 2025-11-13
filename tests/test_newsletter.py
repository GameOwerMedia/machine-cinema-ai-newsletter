from pathlib import Path
import sys

import json
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fetch_ai_news import gather
from make_posts import format_post
import generate_all as generator
from generate_all import pick_top, score_for


def test_gather_returns_sample_articles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("fetch_ai_news.fetch_news_from_sources", lambda max_items=36: [])

    articles = gather()

    assert isinstance(articles, list)
    assert articles, "Expected gather() to return sample articles"
    for article in articles:
        assert set(article) >= {"title", "link", "summary", "source", "image"}
        assert article["title"].strip()
        assert article["link"].startswith("http")


def test_format_post_includes_symbol_and_link():
    formatted = format_post(
        {
            "title": "OpenAI releases new GPT-5 model",
            "link": "https://openai.com/blog/gpt-5",
            "summary": "<p>Enhanced reasoning and multimodal abilities.</p>",
        },
        style="creators",
    )

    assert "[AI]" in formatted
    assert "LINK: https://openai.com/blog/gpt-5" in formatted
    assert "<p>" not in formatted


@pytest.fixture
def sample_articles():
    base = {
        "summary": "Example summary",
        "published": "2025-11-13T05:00:00Z",
        "image": "",
    }

    def make(idx, domain):
        return {
            **base,
            "title": f"Article {idx}",
            "link": f"https://{domain}/story-{idx}",
            "source": domain,
        }

    return [
        make(1, "example.com"),
        make(2, "example.com"),
        make(3, "another.com"),
        make(4, "third.com"),
        make(5, "fourth.com"),
        make(6, "fifth.com"),
    ]


def test_pick_top_prefers_unique_domains(sample_articles):
    chosen = pick_top(sample_articles, "creators", 4, already_used=set(), scorer=score_for)

    assert len(chosen) == 4
    domains = {article["link"].split("/")[2] for article in chosen}
    assert len(domains) == len(chosen)


def test_build_payload_assigns_hero_and_translations(sample_articles, monkeypatch):
    # Ensure deterministic order
    for idx, article in enumerate(sample_articles):
        article["published"] = f"2025-11-13T0{idx}:00:00Z"
        article["summary"] = f"Opis {idx}"

    monkeypatch.setattr(generator, "_translate_batch", lambda texts, dest="en": [text.upper() for text in texts])

    payload = generator.build_payload(sample_articles)

    assert payload, "Expected payload to contain items"
    hero_items = [item for item in payload if "hero" in item["tags"]]
    assert hero_items, "Hero tag should be assigned"
    assert payload[0]["title_en"], "English title should be present"
    assert payload[0]["summary_en"], "English summary should be present"
    assert all(item["language"] == "pl" for item in payload)


def test_write_payload_creates_files(tmp_path, monkeypatch):
    payload = [
        {
            "id": "story",
            "source": "example.com",
            "sourceUrl": "https://example.com",
            "title": "Story",
            "summary": "Summary",
            "title_en": "Story",
            "summary_en": "Summary",
            "language": "pl",
            "publishedAt": "2025-11-13T00:00:00+00:00",
            "url": "https://example.com/story",
            "imageUrl": "https://example.com/image.jpg",
            "tags": ["hero"],
        }
    ]

    data_path = tmp_path / "data/news.json"
    docs_path = tmp_path / "docs/data/news.json"

    monkeypatch.setattr(generator, "OUTPUT_DATA_PATH", data_path)
    monkeypatch.setattr(generator, "OUTPUT_DOCS_PATH", docs_path)

    seen_urls = []
    monkeypatch.setattr(generator, "save_seen", lambda urls: seen_urls.extend(urls))

    generator.write_payload(payload, save_seen_urls=True)

    assert data_path.exists()
    assert docs_path.exists()

    with open(data_path, "r", encoding="utf-8") as fh:
        stored = json.load(fh)

    assert stored[0]["id"] == "story"
    assert seen_urls == ["https://example.com/story"]


def test_ensure_translations_falls_back(monkeypatch):
    articles = [{"title": "Tytuł", "summary": "Krótki opis"}]

    monkeypatch.setattr(generator, "_translate_batch", lambda texts, dest="en": [None] * len(texts))

    generator._ensure_translations(articles)

    assert articles[0]["title_en"] == "Tytuł"
    assert articles[0]["summary_en"] == "Krótki opis"
