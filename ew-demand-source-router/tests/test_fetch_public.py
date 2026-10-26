import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.fetch_public import VisibleTextParser, validate_url  # noqa: E402


class FetchPublicTests(unittest.TestCase):
    def test_extracts_visible_text_only(self):
        parser = VisibleTextParser()
        parser.feed("<h1>Hello</h1><script>secret()</script><p>World</p>")
        self.assertEqual(parser.text(), "Hello\nWorld")

    def test_rejects_credentials_and_non_http(self):
        with self.assertRaises(ValueError):
            validate_url("ftp://example.com/file")
        with self.assertRaises(ValueError):
            validate_url("https://user:pass@example.com/private")


if __name__ == "__main__":
    unittest.main()
