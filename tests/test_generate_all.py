import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import generate_all


class GenerateAllTests(unittest.TestCase):
    def test_main_persists_only_published_links(self):
        items = [
            {"link": f"https://example.com/{idx}", "title": f"Title {idx}"}
            for idx in range(6)
        ]

        selections = [
            [items[0], items[1]],
            [items[2], items[3]],
            [items[4], items[5]],
        ]

        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            site_dir = Path(tmpdir) / "site"

            with (
                mock.patch.object(generate_all, "gather", return_value=items) as gather_mock,
                mock.patch.object(generate_all, "load_config", return_value={}) as config_mock,
                mock.patch.object(
                    generate_all,
                    "format_post",
                    side_effect=lambda it, style: it["link"],
                ) as format_mock,
                mock.patch.object(generate_all, "pick_top", side_effect=selections) as pick_mock,
                mock.patch.object(generate_all, "save_seen_links") as save_mock,
            ):
                generate_all.main(outfile_format="md", out_dir=str(out_dir), site_dir=str(site_dir))

            gather_mock.assert_called_once()
            self.assertEqual(3, pick_mock.call_count)
            config_mock.assert_called_once()
            for call in pick_mock.call_args_list:
                self.assertEqual(generate_all.N_PER_BUCKET, call.args[2])

            expected_links = [item["link"] for selection in selections for item in selection]
            save_mock.assert_called_once_with(expected_links)

            out_files = list(out_dir.glob("*.md"))
            self.assertEqual(1, len(out_files))
            md_contents = out_files[0].read_text(encoding="utf-8")
            for link in expected_links:
                self.assertIn(link, md_contents)

    def test_per_bucket_from_config_controls_selection_size(self):
        items = [
            {"link": f"https://example.com/{idx}", "title": f"Title {idx}"}
            for idx in range(3)
        ]

        selections = [[items[0]], [items[1]], [items[2]]]

        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            site_dir = Path(tmpdir) / "site"

            with (
                mock.patch.object(generate_all, "gather", return_value=items),
                mock.patch.object(generate_all, "load_config", return_value={"newsletter": {"per_bucket": 1}}),
                mock.patch.object(generate_all, "pick_top", side_effect=selections) as pick_mock,
                mock.patch.object(generate_all, "format_post", side_effect=lambda it, style: it["link"]),
                mock.patch.object(generate_all, "save_seen_links") as save_mock,
            ):
                generate_all.main(outfile_format="md", out_dir=str(out_dir), site_dir=str(site_dir))

            self.assertTrue(all(call.args[2] == 1 for call in pick_mock.call_args_list))
            expected_links = [entry["link"] for group in selections for entry in group]
            save_mock.assert_called_once_with(expected_links)

    def test_main_writes_root_redirect_index(self):
        item = {"link": "https://example.com/story", "title": "Story"}

        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            site_dir = Path(tmpdir) / "site"

            with (
                mock.patch.object(generate_all, "gather", return_value=[item]),
                mock.patch.object(generate_all, "load_config", return_value={"newsletter": {"per_bucket": 1}}),
                mock.patch.object(generate_all, "pick_top", side_effect=[ [item], [item], [item] ]),
                mock.patch.object(generate_all, "format_post", side_effect=lambda it, style: it["link"]),
                mock.patch.object(generate_all, "save_seen_links")
            ):
                generate_all.main(outfile_format="md", out_dir=str(out_dir), site_dir=str(site_dir))

            root_index = site_dir.parent / "index.html"
            self.assertTrue(root_index.exists())
            contents = root_index.read_text(encoding="utf-8")
            self.assertIn("meta http-equiv=\"refresh\"", contents)
            self.assertIn("site/index.html", contents)


if __name__ == "__main__":
    unittest.main()
