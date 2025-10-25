from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

import newsletter.data_sources as data_sources
from newsletter.app import run
from newsletter.data_sources import Story
from newsletter.seen import SeenCache


def _args(**overrides):
    defaults = {
        "mode": "curated",
        "config": "sources.yml",
        "reset_seen": True,
        "seen_ttl": None,
        "seen_scope": "rolling",
        "verbose": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _write_config(base: Path, per_bucket: int = 2, mode: str = "segments") -> None:
    config = f"""newsletter:\n  per_bucket: {per_bucket}\n  mode: {mode}\ncurated:\n  path: data/news.json\nlive:\n  feeds: []\n"""
    (base / "sources.yml").write_text(config, encoding="utf-8")


def _write_dataset(base: Path) -> None:
    stories = [
        {
            "title": f"Story {idx}",
            "summary": "Details about AI and marketing",
            "link": f"https://example.com/{idx}",
            "source": "Example",
            "published": "2025-01-0{}T09:00:00Z".format(idx % 9 + 1),
        }
        for idx in range(1, 7)
    ]
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "news.json").write_text(json.dumps(stories), encoding="utf-8")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(data_sources.requests, "get", lambda *args, **kwargs: pytest.skip("network not allowed"))
    monkeypatch.setattr(data_sources.feedparser, "parse", lambda *args, **kwargs: pytest.skip("network not allowed"))


@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_curated_mode_generates_outputs(temp_env):
    _write_config(temp_env)
    _write_dataset(temp_env)
    result = run(_args(), base_dir=temp_env)
    out_md = temp_env / "out" / f"{result['date']}_ALL.md"
    assert out_md.exists()
    assert (temp_env / "site" / "index.html").exists()
    assert (temp_env / "index.html").exists()
    assert (temp_env / ".nojekyll").exists()
    seen_path = temp_env / ".cache" / "seen.json"
    cache_data = json.loads(seen_path.read_text(encoding="utf-8"))
    assert len(cache_data["rolling"]) == result["published_count"]


def test_fallback_to_live_when_curated_missing(monkeypatch, temp_env):
    _write_config(temp_env)

    sample_story = Story(
        title="Live story",
        summary="",
        link="https://live.example.com/1",
        source="Live",
        published=None,
    )
    monkeypatch.setattr("newsletter.app.load_live", lambda config: [sample_story])
    result = run(_args(mode="curated"), base_dir=temp_env)
    assert result["published_count"] >= 1


def test_top_mode_uses_per_bucket(monkeypatch, temp_env):
    _write_config(temp_env, per_bucket=3, mode="top")
    stories = [
        Story(
            title=f"Story {idx}",
            summary="Generative AI",
            link=f"https://domain{idx}.example.com/article",
            source="Example",
            published=None,
        )
        for idx in range(6)
    ]
    monkeypatch.setattr("newsletter.app.load_curated", lambda config: stories)
    result = run(_args(), base_dir=temp_env)
    assert result["published_count"] == 3


def test_segments_handle_missing_published(monkeypatch, temp_env):
    _write_config(temp_env, per_bucket=2, mode="segments")
    stories = []
    for idx in range(6):
        item = {
            "title": f"Story {idx}",
            "summary": "Prompt workflows",
            "link": f"https://example.com/mixed/{idx}",
            "source": "Example",
        }
        if idx % 2 == 0:
            item["published"] = f"2025-01-0{idx % 9 + 1}T09:00:00Z"
        else:
            item["published"] = None
        stories.append(item)
    data_dir = temp_env / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "news.json").write_text(json.dumps(stories), encoding="utf-8")
    monkeypatch.setattr("newsletter.segments._score", lambda bucket, story, keywords: 1.0)
    result = run(_args(), base_dir=temp_env)
    assert result["published_count"] == 6


def test_seen_cache_scope_and_ttl(tmp_path):
    cache_path = tmp_path / "seen.json"
    cache = SeenCache(path=cache_path, scope="rolling", ttl_days=1, reset=True)
    today = date.today()
    cache.remember(today, ["https://example.com/a"])
    assert cache.filter_new(["https://example.com/a"], today) == []
    yesterday = today - timedelta(days=2)
    cache.remember(yesterday, ["https://example.com/old"])
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    assert "https://example.com/old" not in data["rolling"]
