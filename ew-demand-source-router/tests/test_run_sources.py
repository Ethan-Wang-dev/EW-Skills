import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_sources  # noqa: E402
from scripts.source_registry import REGISTRY, get_source  # noqa: E402


class RunSourcesTests(unittest.TestCase):
    def test_target_source_registry_is_explicit(self):
        expected = {
            "google_search", "google_trends", "similarweb", "semrush", "ahrefs",
            "reddit", "x", "discord", "fiverr", "upwork", "trustpilot", "chrome_store",
            "app_store", "there_is_an_ai_for_that", "product_hunt", "toolify", "traffic_cv",
            "stripe", "creem", "trustmrr", "ads_transparency", "wayback", "query_domains",
            "searchsuggest_tips", "pubspy", "wappalyzer", "virustotal", "github", "huggingface", "arxiv",
            "remotive", "arbeitnow",
        }
        self.assertTrue(expected.issubset(REGISTRY))
        for name in expected:
            spec = get_source(name)
            self.assertIn(spec.transport, {"json", "xml", "html", "browser", "manual"})

    def test_json_source_becomes_evidence_and_analysis(self):
        brief = {"target_user": "indie developer", "market": "US", "evidence_gaps": ["frequency"]}
        requests = [{"source": "github", "query": "feedback tool", "limit": 2}]
        payload = json.dumps({"items": [{"full_name": "acme/feedback", "description": "Collect feedback", "html_url": "https://github.com/acme/feedback", "stargazers_count": 12, "forks_count": 2, "updated_at": "2026-09-01"}]})
        transport = {"adapter": "http", "access_state": "public", "http_status": 200, "bytes": len(payload)}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_sources, "http_fetch", return_value=(payload, transport, payload.encode())):
            result = run_sources.run_batch(brief, requests, Path(directory), max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False)
            output = Path(directory)
            self.assertTrue((output / "summary.md").exists())
        self.assertEqual(len(result["evidence"]), 1)
        self.assertEqual(result["evidence"][0]["source_type"], "trend")
        self.assertEqual(result["evidence"][0]["supports"], "competition")
        self.assertEqual(result["evidence"][0]["adapter"], "http")

    def test_job_api_parser_extracts_skills_location_and_salary_as_a_listing_signal(self):
        brief = {"target_user": "job seeker", "market": "remote", "evidence_gaps": ["frequency"]}
        requests = [{"source": "remotive", "query": "AI", "limit": 2}]
        payload = json.dumps({"jobs": [{"title": "AI Evaluator", "company_name": "Acme", "candidate_required_location": "Worldwide", "job_type": "freelance", "salary": "$20/hour", "publication_date": "2026-09-10", "tags": ["AI/ML", "research"], "description": "Evaluate model answers", "url": "https://remotive.com/jobs/1"}]})
        transport = {"adapter": "http", "access_state": "public", "http_status": 200, "bytes": len(payload)}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_sources, "http_fetch", return_value=(payload, transport, payload.encode())):
            result = run_sources.run_batch(brief, requests, Path(directory), max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False)
        self.assertEqual(len(result["evidence"]), 1)
        record = result["evidence"][0]
        self.assertEqual(record["supports"], "demand")
        self.assertEqual(record["metric"]["location"], "Worldwide")
        self.assertIn("AI/ML", record["metric"]["tags"])

    def test_arbeitnow_parser_filters_query_locally(self):
        body = json.dumps({"data": [
            {"title": "AI Product Manager", "company_name": "Acme", "location": "Remote", "remote": True, "tags": ["AI", "product"], "description": "Own product strategy", "url": "https://arbeitnow.com/jobs/1", "created_at": 1700000000},
            {"title": "Accountant", "company_name": "Other", "location": "Berlin", "tags": ["finance"], "description": "Close books", "url": "https://arbeitnow.com/jobs/2", "created_at": 1700000000}
        ]})
        rows = run_sources.get_source("arbeitnow").parser(body, "https://www.arbeitnow.com/api/job-board-api", {"query": "AI product", "limit": 10})
        self.assertEqual(len(rows), 1)
        self.assertIn("AI Product Manager", rows[0]["quote_or_observation"])

    def test_manual_source_is_visible_as_coverage_gap(self):
        brief = {"target_user": "buyer", "market": "US"}
        requests = [{"source": "semrush", "query": "keyword"}]
        with tempfile.TemporaryDirectory() as directory:
            result = run_sources.run_batch(brief, requests, Path(directory), max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False)
        self.assertEqual(result["runs"][0]["access_state"], "not_applicable")
        self.assertEqual(result["evidence"], [])
        self.assertIn("value_or_payment", result["analysis"]["open_gaps"])

    def test_manual_registry_with_explicit_public_url_uses_opt_in_browser(self):
        brief = {"target_user": "buyer", "market": "US"}
        requests = [{"source": "stripe", "url": "https://example.com/public-pricing"}]
        with tempfile.TemporaryDirectory() as directory:
            result = run_sources.run_batch(brief, requests, Path(directory) / "out", max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False)
        self.assertEqual(result["runs"][0]["adapter"], "browser")
        self.assertEqual(result["runs"][0]["access_state"], "partial")
        self.assertIn("allow-browser", result["runs"][0]["fallback_used"])

    def test_manual_source_can_use_explicit_authorized_browser(self):
        brief = {"target_user": "buyer", "market": "US"}
        requests = [{"source": "semrush", "adapter": "authenticated_browser", "url": "https://www.semrush.com/analytics/keywordoverview/?q=feedback", "actions": [{"action": "wait", "ms": 1000}]}]
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "profile"
            profile.mkdir()
            transport = {"adapter": "authenticated_browser", "access_state": "authenticated", "bytes": 18}
            with patch.object(run_sources, "browser_fetch", return_value=("Keyword feedback volume 320", transport, b"Keyword feedback volume 320")) as fetch:
                result = run_sources.run_batch(brief, requests, Path(directory) / "out", max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False, allow_authenticated_browser=True, browser_profile=str(profile))
            self.assertEqual(result["runs"][0]["access_state"], "authenticated")
            self.assertEqual(result["runs"][0]["adapter"], "authenticated_browser")
            self.assertEqual(len(result["evidence"]), 1)
            adapter_text = (Path(directory) / "out" / "adapter-runs" / "001-semrush.json").read_text(encoding="utf-8")
            self.assertNotIn(str(profile), adapter_text)
            fetch.assert_called_once()

    def test_authenticated_adapter_requires_explicit_user_state(self):
        brief = {"target_user": "buyer", "market": "US"}
        requests = [{"source": "semrush", "adapter": "authenticated_browser", "url": "https://www.semrush.com/analytics/keywordoverview/?q=feedback"}]
        with tempfile.TemporaryDirectory() as directory:
            result = run_sources.run_batch(brief, requests, Path(directory) / "out", max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False, allow_authenticated_browser=True)
        self.assertEqual(result["runs"][0]["access_state"], "partial")
        self.assertEqual(result["evidence"], [])

    def test_user_export_request_is_merged_into_batch(self):
        brief = {"target_user": "buyer", "market": "US"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            export = root / "ahrefs.json"
            export.write_text(json.dumps({"items": [{"keyword": "feedback tool", "volume": 90}]}), encoding="utf-8")
            requests = [{"source": "ahrefs", "adapter": "user_export", "path": str(export), "limit": 10}]
            result = run_sources.run_batch(brief, requests, root / "out", max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False)
            self.assertEqual(result["runs"][0]["adapter"], "user_export")
            self.assertEqual(result["runs"][0]["access_state"], "authenticated")
            self.assertEqual(len(result["evidence"]), 1)
            self.assertEqual(result["evidence"][0]["source_type"], "search")

    def test_browser_actions_are_bounded_and_do_not_allow_scripts_or_submission(self):
        with self.assertRaises(ValueError):
            run_sources.browser_action_command({"action": "eval", "js": "document.cookie"})
        with self.assertRaises(ValueError):
            run_sources.browser_action_command({"action": "press", "key": "Enter"})
        with self.assertRaises(ValueError):
            run_sources.browser_action_command({"action": "fill", "selector": "input[name=password]", "text": "secret"})
        command, audit = run_sources.browser_action_command({"action": "scroll", "direction": "down", "pixels": 100})
        self.assertEqual(command, ["scroll", "down", "100"])
        self.assertEqual(audit["action"], "scroll")

    def test_browser_url_cannot_embed_credentials(self):
        with self.assertRaises(ValueError):
            run_sources.browser_fetch("https://user:pass@example.com/private", timeout=1, session_name="test")

    def test_browser_login_challenge_is_not_promoted_to_evidence(self):
        brief = {"target_user": "buyer", "market": "US"}
        requests = [{"source": "semrush", "adapter": "authenticated_browser", "url": "https://example.com/login"}]
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "profile"
            profile.mkdir()
            transport = {"adapter": "authenticated_browser", "access_state": "authenticated", "auth_challenge_detected": True, "bytes": 24}
            with patch.object(run_sources, "browser_fetch", return_value=("Please sign in to continue", transport, b"Please sign in to continue")):
                result = run_sources.run_batch(brief, requests, Path(directory) / "out", max_requests=10, max_bytes=100_000, timeout=1, delay=0, allow_browser=False, allow_authenticated_browser=True, browser_profile=str(profile))
        self.assertEqual(result["runs"][0]["access_state"], "partial")
        self.assertEqual(result["evidence"], [])


if __name__ == "__main__":
    unittest.main()
