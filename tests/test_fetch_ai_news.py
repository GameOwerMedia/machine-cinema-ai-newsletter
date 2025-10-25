import json
from datetime import date
from pathlib import Path

import yaml

import fetch_ai_news


def write_config(tmp_path: Path, curated_path: Path) -> Path:
    config_path = tmp_path / "sources.yml"
    payload = {
        "curated": {"path": str(curated_path)},
        "live": {"feeds": []},
    }
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


def test_gather_returns_curated_serialisation(tmp_path):
    curated_path = tmp_path / "news.json"
    stories = [
        {
            "title": "Second story",
            "summary": "b",
            "link": "https://example.com/b",
            "source": "Example",
            "published": "2025-05-02T09:00:00Z",
        },
        {
            "title": "First story",
            "summary": "a",
            "link": "https://example.com/a",
            "source": "Example",
            "published": "2025-05-02T10:00:00Z",
        },
    ]
    curated_path.write_text(json.dumps(stories), encoding="utf-8")
    config_path = write_config(tmp_path, curated_path)

    gathered = fetch_ai_news.gather(str(config_path))

    assert len(gathered) == 2
    assert {item["link"] for item in gathered} == {"https://example.com/a", "https://example.com/b"}
    assert all("published" in item for item in gathered)


def test_save_seen_records_links(monkeypatch):
    recorded = {}

    class DummyCache:
        def __init__(self, scope="rolling"):
            recorded["scope"] = scope

        def remember(self, day, links):
            recorded["day"] = day
            recorded["links"] = list(links)

    class FakeDate(date):
        @classmethod
        def today(cls):
            return cls(2025, 5, 7)

    monkeypatch.setattr(fetch_ai_news, "SeenCache", lambda scope="rolling": DummyCache(scope))
    monkeypatch.setattr(fetch_ai_news, "date", FakeDate)

    fetch_ai_news.save_seen(["https://example.com/a", "https://example.com/b"], scope="daily")

    assert recorded["scope"] == "daily"
    assert recorded["day"] == FakeDate(2025, 5, 7)
    assert recorded["links"] == ["https://example.com/a", "https://example.com/b"]
