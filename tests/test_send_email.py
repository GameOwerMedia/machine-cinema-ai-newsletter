import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import send_email


class SendEmailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.tmp_path = Path(self.tmpdir.name)

    def test_discover_latest_markdown_returns_latest(self) -> None:
        with mock.patch.object(send_email, "OUT_DIR", self.tmp_path):
            (self.tmp_path / "2024-01-01_ALL.md").write_text("first", encoding="utf-8")
            (self.tmp_path / "2024-01-02_ALL.md").write_text("second", encoding="utf-8")
            latest = send_email.discover_latest_markdown()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.name, "2024-01-02_ALL.md")

    def test_load_subscribers_ignores_comments(self) -> None:
        subs_file = self.tmp_path / "subscribers.txt"
        subs_file.write_text("# header\nfirst@example.com|Name|source\n\nsecond@example.com", encoding="utf-8")
        emails = send_email.load_subscribers(subs_file)
        self.assertEqual(emails, ["first@example.com", "second@example.com"])

    def test_build_message_sets_bcc(self) -> None:
        md_file = self.tmp_path / "newsletter.md"
        md_file.write_text("# Hello\n\nNewsletter body", encoding="utf-8")
        recipients = ["one@example.com", "two@example.com"]
        message = send_email.build_message(md_file, "sender@example.com", recipients, subject="Subject")
        self.assertEqual(message["Bcc"], ", ".join(recipients))
        plain_part = message.get_body(preferencelist=("plain",))
        self.assertIsNotNone(plain_part)
        self.assertIn("Newsletter body", plain_part.get_content())

    def test_ensure_credentials_missing_values(self) -> None:
        with mock.patch.dict(os.environ, {"SMTP_HOST": "", "SMTP_USERNAME": ""}, clear=True):
            creds = send_email.ensure_credentials()
        self.assertIsNone(creds)

    def test_ensure_credentials_returns_details(self) -> None:
        env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "2525",
            "SMTP_USERNAME": "user",
            "SMTP_PASSWORD": "pass",
            "SENDER_EMAIL": "sender@example.com",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            creds = send_email.ensure_credentials()
        self.assertEqual(
            creds,
            {
                "host": "smtp.example.com",
                "user": "user",
                "password": "pass",
                "sender": "sender@example.com",
                "port": 2525,
            },
        )


if __name__ == "__main__":
    unittest.main()
