import unittest

from make_posts import format_post


class FormatPostTests(unittest.TestCase):
    def test_includes_icon_and_metadata(self):
        item = {
            "title": "Example",
            "link": "https://example.com/story",
            "summary": "Line one\nLine two",
            "source": "Example Source",
            "published": "2024-05-05T10:00:00+00:00",
        }

        rendered = format_post(item, style="marketing")

        self.assertTrue(rendered.startswith("📣 [Example](https://example.com/story)"))
        self.assertIn("Example Source", rendered)
        self.assertIn("2024-05-05", rendered)
        self.assertIn("> Line one Line two", rendered)

    def test_handles_missing_link_and_summary(self):
        item = {
            "title": "No Link",
            "summary": None,
            "source": "",
            "published": None,
        }

        rendered = format_post(item, style="unknown")

        self.assertEqual("🧠 No Link", rendered)


if __name__ == "__main__":
    unittest.main()
