import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import handle_subscriber_issue as hsi


class HandleSubscriberIssueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.data_path = Path(self.tmpdir.name) / "subscribers.txt"

    def test_extract_section_returns_text_without_placeholder(self) -> None:
        body = "### Email address\nvalue@example.com\n\n### Name (optional)\n_No response_"
        email = hsi.extract_section(body, "email")
        name = hsi.extract_section(body, "name")
        self.assertEqual(email, "value@example.com")
        self.assertEqual(name, "")

    def test_append_if_new_writes_header_and_entry(self) -> None:
        with mock.patch.object(hsi, "DATA_PATH", self.data_path):
            added_first = hsi.append_if_new("user@example.com", "Name", "Source", issue_number=7)
            added_second = hsi.append_if_new("user@example.com", "Name", "Source", issue_number=8)
        self.assertTrue(added_first)
        self.assertFalse(added_second)
        contents = self.data_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(contents[0], "# email|name|source|issue|added_at_utc")
        self.assertIn("user@example.com|Name|Source|#7", contents[1])

    def test_main_outputs_json_payload(self) -> None:
        issue_body = (
            "### Email address\nuser@example.com\n\n"
            "### Name (optional)\nTest User\n\n"
            "### How did you hear about us?\nInternet"
        )
        event = {"issue": {"number": 3, "body": issue_body}}
        event_path = Path(self.tmpdir.name) / "event.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        with mock.patch.object(hsi, "DATA_PATH", self.data_path):
            buffer = io.StringIO()
            with mock.patch("sys.stdout", buffer):
                exit_code = hsi.main(str(event_path))
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "added")
        self.assertTrue(payload["changes"])
        self.assertEqual(payload["email"], "user@example.com")

    def test_main_handles_invalid_email(self) -> None:
        issue_body = "### Email address\ninvalid\n"
        event = {"issue": {"number": 5, "body": issue_body}}
        event_path = Path(self.tmpdir.name) / "event_invalid.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        with mock.patch.object(hsi, "DATA_PATH", self.data_path):
            buffer = io.StringIO()
            with mock.patch("sys.stdout", buffer):
                exit_code = hsi.main(str(event_path))
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "invalid")
        self.assertFalse(payload["changes"])


if __name__ == "__main__":
    unittest.main()
