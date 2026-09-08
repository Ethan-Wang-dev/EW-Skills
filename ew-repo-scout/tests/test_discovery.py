import io
import json
import sys
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import github_discover as discovery
import evaluate_results as evaluation


class FakeClient:
    def __init__(self, answer, token="fixture-token"):
        self.answer, self.token, self.calls = answer, token, []
        self.events, self.requests, self.cache_hits, self.max_requests = [], 0, 0, 60

    def get(self, url, accept=discovery.ACCEPT):
        self.calls.append(url)
        self.requests += 1
        value = self.answer(url)
        return dict(url=url, fetched_at="2026-09-08T12:00:00Z", from_cache=False, **value)


def hit(name, repo_id, **extra):
    return {"full_name": name, "source": "repo", "query": "web clipper", "rank": 1,
            "url": "https://github.com/" + name,
            "metadata": {"full_name": name, "id": repo_id, "description": None, **extra}}


class RetrievalTests(unittest.TestCase):
    def test_case_and_rename_dedup_preserves_separate_fork(self):
        result = discovery.merge_hits([hit("Org/Old", 1), hit("org/old", 1),
                                       hit("org/new", 1), hit("fork/new", 2, fork=True)])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["full_name"], "org/new")
        self.assertIn("Org/Old", result[0]["aliases"])
        self.assertTrue(result[1]["fork"])

    def test_pagination_records_totals_and_limits(self):
        def answer(url):
            page = int(parse_qs(urlparse(url).query)["page"][0])
            count = 100 if page == 1 else 1
            return {"status": "ok", "data": {"total_count": 101, "incomplete_results": False,
                    "items": [{"full_name": f"org/repo{page}_{i}", "id": page * 100 + i}
                              for i in range(count)]}}
        client = FakeClient(answer)
        hits, report = discovery.search_endpoint(client, "clip in:readme", "repo", 101)
        self.assertEqual(len(hits), 101)
        self.assertEqual(len(client.calls), 2)
        self.assertFalse(report["limited"])
        self.assertEqual(report["total_count"], 101)
        self.assertTrue(all(parse_qs(urlparse(url).query)["per_page"] == ["100"] for url in client.calls))
        self.assertNotIn("sort=best-match", client.calls[0])

    def test_code_without_auth_is_skipped_not_empty_success(self):
        client = FakeClient(lambda _: self.fail("Network must not be called"), token=None)
        hits, report = discovery.search_endpoint(client, "MutationObserver", "code", 8)
        self.assertEqual(hits, [])
        self.assertEqual(report["status"], "skipped_auth")
        self.assertEqual(client.calls, [])

    def test_code_evidence_is_preserved_and_private_hits_excluded(self):
        client = FakeClient(lambda _: {"status": "ok", "data": {"total_count": 2, "items": [
            {"repository": {"id": 1, "full_name": "o/r", "private": False},
             "path": "src/capture.js", "html_url": "https://github.com/o/r/blob/main/src/capture.js",
             "text_matches": [{"fragment": "new MutationObserver(capture)"}]},
            {"repository": {"full_name": "o/private", "private": True}}]}})
        hits, _ = discovery.search_endpoint(client, "MutationObserver", "code", 2)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["path"], "src/capture.js")
        self.assertIn("MutationObserver", hits[0]["excerpt"])
        merged = discovery.merge_hits([hit("o/r", 1, description="Web clipper"), *hits])
        self.assertEqual(merged[0]["metadata_state"], "available")
        self.assertEqual(set(merged[0]["sources"]), {"repo", "code"})

    def test_issue_and_pr_hits_are_not_labeled_implemented_features(self):
        client = FakeClient(lambda _: {"status": "ok", "data": {"total_count": 2, "items": [
            {"repository_url": discovery.API + "/repos/o/r", "title": "Please support clipping", "body": None},
            {"repository_url": discovery.API + "/repos/o/r", "pull_request": {"url": "pr"}, "title": "Add clipping"}]}})
        hits, _ = discovery.search_endpoint(client, "clipping", "issues", 2)
        self.assertEqual([item["kind"] for item in hits], ["issue", "pull_request"])

    def test_incomplete_and_failed_search_are_visible(self):
        client = FakeClient(lambda _: {"status": "ok", "data": {"total_count": 20, "items": [], "incomplete_results": True}})
        _, report = discovery.search_endpoint(client, "clip", "repo", 20)
        self.assertEqual(report["status"], "partial")
        failed = FakeClient(lambda _: {"status": "error", "message": "invalid query"})
        args = discovery.parser().parse_args(["--query", "clip", "--deep-limit", "0"])
        result = discovery.execute(args, failed)
        self.assertEqual(result["search_metadata"]["status"], "failed")
        self.assertEqual(result["count"], 0)

    def test_ranking_and_deep_selection_ignore_popularity_and_activity(self):
        good = discovery.merge_hits([hit("o/clip", 1, description="web clipper", stargazers_count=1)])[0]
        bad = discovery.merge_hits([hit("o/large", 2, description="enterprise resource planning", stargazers_count=100000)])[0]
        first = discovery.lexical_score(good, "web clipper", ["web clipper"])
        good.update(archived=True, stargazers_count=0)
        self.assertEqual(first, discovery.lexical_score(good, "web clipper", ["web clipper"]))
        ranked = discovery.rank_candidates([bad, good], "web clipper", ["web clipper"])
        self.assertEqual(discovery.select_deep(ranked, 1)[0]["full_name"], "o/clip")

    def test_null_metadata_and_qualifiers(self):
        item = {"name": None, "description": None, "topics": None}
        score, _ = discovery.lexical_score(item, "", ["clip in:readme repo:org/repo"])
        self.assertEqual(score, 0)
        self.assertEqual(discovery.terms("clip in:readme repo:org/repo"), {"clip"})
        self.assertIn("剪藏", discovery.terms("个人剪藏工具"))

    def test_readme_retrieves_relevant_tail_with_line_provenance(self):
        text = "\n".join(["Overview"] * 150 + ["Supports bookmark capture and export."])
        excerpt, truncated = discovery.readme_excerpt(text, {"bookmark", "capture"})
        self.assertIn("L151: Supports bookmark", excerpt)
        self.assertTrue(truncated)

    def test_no_readme_still_checks_license_and_distinguishes_release_error(self):
        client = FakeClient(lambda url: {"status": "rate_limited", "message": "quota"}
                            if "releases/latest" in url else {"status": "not_found", "http_status": 404})
        item = discovery.enrich(client, {"full_name": "o/r"}, set(), no_readme=True)
        self.assertFalse(any(url.endswith("/readme") for url in client.calls))
        self.assertEqual(item["release_evidence"]["status"], "rate_limited")
        self.assertEqual(item["license_evidence"]["status"], "not_found")
        self.assertNotIn("latest_release", item)

    def test_rate_limit_headers_stop_next_request_in_bucket(self):
        headers = Message()
        headers["X-RateLimit-Remaining"] = "0"
        headers["X-RateLimit-Reset"] = "12345"
        error = HTTPError(discovery.API + "/search/repositories?q=a", 403, "Forbidden", headers,
                          io.BytesIO(b'{"message":"API rate limit exceeded"}'))
        client = discovery.GitHub(max_requests=10)
        with patch.object(discovery, "urlopen", side_effect=error) as network:
            one = client.get(discovery.API + "/search/repositories?q=a")
            two = client.get(discovery.API + "/search/repositories?q=b")
        self.assertEqual(one["status"], "rate_limited")
        self.assertEqual(one["rate_limit"]["reset"], "12345")
        self.assertEqual(two["status"], "rate_limited")
        self.assertEqual(network.call_count, 1)

    def test_cache_and_request_budget(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status, response.headers = 200, {}
        response.read.return_value = b'{"id":1}'
        with tempfile.TemporaryDirectory() as directory:
            client = discovery.GitHub(cache_dir=directory, max_requests=1)
            with patch.object(discovery, "urlopen", return_value=response) as network:
                first = client.get(discovery.API + "/repos/o/r")
                cached = client.get(discovery.API + "/repos/o/r")
                skipped = client.get(discovery.API + "/repos/o/other")
            self.assertEqual(network.call_count, 1)
            self.assertEqual(first["fetched_at"], cached["fetched_at"])
            self.assertTrue(cached["from_cache"])
            self.assertEqual(skipped["status"], "budget_exhausted")


class EvaluationTests(unittest.TestCase):
    def test_unknown_labels_do_not_become_irrelevant_or_claim_precision(self):
        result = evaluation.evaluate({"repositories": ["o/a", "o/new"]},
                                     {"labels": {"o/a": 3, "o/b": 2}}, 2)
        self.assertIsNone(result["precision_at_k"])
        self.assertEqual(result["precision_lower_bound_at_k"], 0.5)
        self.assertEqual(result["precision_upper_bound_at_k"], 1)
        self.assertEqual(result["known_recall_at_k"], 0.5)
        self.assertTrue(result["direct_hit_at_3"])

    def test_alias_duplicates_and_partial_result_warning(self):
        result = evaluation.evaluate({"repositories": ["o/old", "o/new"], "search_metadata": {"status": "partial"}},
                                     {"aliases": {"o/old": "o/new"}, "labels": {"o/new": 3}}, 2)
        self.assertEqual(result["duplicate_count"], 1)
        self.assertEqual(result["precision_at_k"], 0.5)
        self.assertEqual(result["known_recall_at_k"], 1)
        self.assertTrue(any("partial" in warning for warning in result["warnings"]))

    def test_no_ground_truth_leaves_recall_and_claim_accuracy_unknown(self):
        result = evaluation.evaluate({"repositories": []}, {"labels": {}})
        self.assertIsNone(result["known_recall_at_k"])
        self.assertIsNone(result["unsupported_claim_rate_checked"])

    def test_invalid_labels_and_alias_cycles_fail(self):
        with self.assertRaises(ValueError):
            evaluation.evaluate({"repositories": []}, {"labels": {"o/a": "high"}})
        with self.assertRaises(ValueError):
            evaluation.evaluate({"repositories": ["o/a"]}, {"aliases": {"o/a": "o/b", "o/b": "o/a"}})


if __name__ == "__main__":
    unittest.main()
