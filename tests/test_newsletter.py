from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fetch_ai_news import gather
from make_posts import format_post
from generate_all import pick_top, score_for


def test_gather_returns_sample_articles(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    articles = gather()

    assert isinstance(articles, list)
    assert articles, "Expected gather() to return sample articles"
    for article in articles:
        assert set(article) >= {"title", "link", "summary", "source"}
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
    }
    def make(idx, domain):
        return {
            **base,
            "title": f"Article {idx}",
            "link": f"https://{domain}/story-{idx}",
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
