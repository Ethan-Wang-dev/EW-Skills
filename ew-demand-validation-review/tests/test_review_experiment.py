import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.review_experiment import review


class ReviewExperimentTests(unittest.TestCase):
    def test_payment_threshold_continues(self):
        plan = {
            "experiment_id": "X-test-001",
            "success_threshold": {"min_events": {"payment": 1}},
            "stop_condition": {},
        }
        result = {
            "experiment_id": "X-test-001",
            "observed_window": "2026-09-13",
            "audience_and_channel": "US / community",
            "events": [
                {"event": "qualified_view", "count": 50, "qualified_count": 40},
                {"event": "payment", "count": 1, "qualified_count": 1},
            ],
            "costs": {"ad_spend": 0, "delivery_cost": 3, "time_cost": 2},
            "sample_reached": True,
        }
        report = review(plan, result)
        self.assertEqual(report["threshold_result"], "met")
        self.assertEqual(report["decision"], "continue")
        self.assertEqual(report["evidence_records"][0]["source_type"], "validation")

    def test_missing_sample_is_inconclusive(self):
        plan = {
            "experiment_id": "X-test-002",
            "success_threshold": {"min_events": {"payment": 1}},
            "stop_condition": {},
        }
        result = {"experiment_id": "X-test-002", "events": [], "costs": {}, "sample_reached": False}
        report = review(plan, result)
        self.assertEqual(report["threshold_result"], "inconclusive")
        self.assertEqual(report["decision"], "run_another_test")

    def test_rate_and_stop_condition_are_explicit(self):
        plan = {
            "experiment_id": "X-test-003",
            "success_threshold": {"min_rates": [{"event": "payment", "denominator": "qualified_view", "min": 0.1}]},
            "stop_condition": {"max_spend": 20},
        }
        result = {
            "experiment_id": "X-test-003",
            "events": [
                {"event": "qualified_view", "count": 100, "qualified_count": 100},
                {"event": "payment", "count": 2, "qualified_count": 2},
            ],
            "costs": {"ad_spend": 20},
            "sample_reached": True,
        }
        report = review(plan, result)
        self.assertEqual(report["threshold_result"], "not_met")
        self.assertEqual(report["decision"], "stop")
        self.assertTrue(report["stop_triggered"])


if __name__ == "__main__":
    unittest.main()
