import csv
import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.ingest_export import build_records, write_output  # noqa: E402


class IngestExportTests(unittest.TestCase):
    def test_csv_becomes_evidence_without_inventing_payment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "semrush.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["Keyword", "Volume", "KD", "URL"])
                writer.writeheader()
                writer.writerow({"Keyword": "feedback workflow", "Volume": "320", "KD": "42", "URL": "https://example.com"})
            records, run = build_records(source, source_name="semrush", source_type="search", market="US", max_records=10)
            self.assertEqual(run["adapter"], "user_export")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["adapter"], "user_export")
            self.assertEqual(records[0]["evidence_strength"], "metric")
            self.assertIn("Volume", records[0]["metric"])
            self.assertNotIn("direct_payment", records[0]["evidence_strength"])

    def test_json_nested_rows_and_output_are_auditable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "reviews.json"
            source.write_text(json.dumps({"results": [{"review": "Export was slow", "date": "2026-09-01", "rating": 2}]}), encoding="utf-8")
            records, run = build_records(source, source_name="trustpilot", source_type="review", source_url="https://trustpilot.com", max_records=10)
            output = root / "out"
            write_output(records, run, output)
            self.assertTrue((output / "evidence.jsonl").exists())
            saved = json.loads((output / "adapter-runs" / "001-user-export.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["input_file_name"], "reviews.json")
            self.assertNotIn(str(source), json.dumps(saved))
            self.assertEqual(json.loads((output / "export-run.json").read_text(encoding="utf-8"))["evidence"][0]["supports"], "pain")

    def test_extensionless_json_is_sniffed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "download"
            source.write_text(json.dumps([{"text": "one exported row"}]), encoding="utf-8")
            records, run = build_records(source, source_name="discord", source_type="community")
        self.assertEqual(run["input_format"], "json")
        self.assertEqual(records[0]["supports"], "pain")


if __name__ == "__main__":
    unittest.main()
