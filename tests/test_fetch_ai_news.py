import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import fetch_ai_news as fan


class FetchAiNewsTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.tmp_path = Path(self.tmpdir.name)

        self.dataset_path = self.tmp_path / "news.json"
        self.cache_path = self.tmp_path / "seen.json"

        self.original_dataset = fan.DATASET_PATH
        self.original_cache = fan.CACHE_PATH
        fan.DATASET_PATH = self.dataset_path
        fan.CACHE_PATH = self.cache_path

        self.addCleanup(self._restore_paths)

    def _restore_paths(self):
        fan.DATASET_PATH = self.original_dataset
        fan.CACHE_PATH = self.original_cache

    def _write_dataset(self, payload):
        self.dataset_path.write_text(json.dumps(payload), encoding="utf-8")

    def _write_seen(self, urls):
        self.cache_path.write_text(json.dumps(list(urls)), encoding="utf-8")

    def test_gather_returns_items_sorted_by_published_desc(self):
        stories = [
            {
                "title": "Older",
                "summary": "First",
                "link": "https://example.com/older",
                "published": "2024-01-01T12:00:00+00:00",
            },
            {
                "title": "Newer",
                "summary": "Second",
                "link": "https://example.com/newer",
                "published": "2024-01-02T12:00:00+00:00",
            },
        ]
        self._write_dataset(stories)

        gathered = fan.gather()
        self.assertEqual(["https://example.com/newer", "https://example.com/older"], [it["link"] for it in gathered])

    def test_gather_ignores_items_already_seen(self):
        stories = [
            {
                "title": "Seen",
                "link": "https://example.com/seen",
                "published": "2024-01-03T00:00:00+00:00",
            },
            {
                "title": "Fresh",
                "link": "https://example.com/fresh",
                "published": "2024-01-04T00:00:00+00:00",
            },
        ]
        self._write_dataset(stories)
        self._write_seen({"https://example.com/seen"})

        gathered = fan.gather()
        self.assertEqual(1, len(gathered))
        self.assertEqual("https://example.com/fresh", gathered[0]["link"])

    def test_save_seen_merges_and_sorts_urls(self):
        self._write_seen({"https://example.com/b"})

        fan.save_seen(["https://example.com/c", "https://example.com/a"])

        saved = json.loads(self.cache_path.read_text(encoding="utf-8"))
        self.assertEqual([
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ], saved)


if __name__ == "__main__":
    unittest.main()
