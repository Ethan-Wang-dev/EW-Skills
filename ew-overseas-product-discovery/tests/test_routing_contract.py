import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RoutingContractTests(unittest.TestCase):
    def test_total_skill_routes_every_discovery_module(self):
        text = (ROOT / "ew-overseas-product-discovery" / "SKILL.md").read_text()
        modules = [
            "ew-demand-intake",
            "ew-demand-kb",
            "ew-demand-source-router",
            "ew-demand-keyword",
            "ew-demand-community",
            "ew-demand-marketplace",
            "ew-demand-reviews",
            "ew-demand-trend",
            "ew-demand-evidence",
            "ew-demand-opportunity",
            "ew-demand-competitor",
            "ew-demand-geo",
            "ew-demand-value",
            "ew-demand-score",
            "ew-demand-validation",
            "ew-validation-assets",
            "ew-demand-validation-review",
        ]
        self.assertEqual([module for module in modules if module not in text], [])

    def test_shared_contract_and_executable_handoffs_exist(self):
        self.assertTrue((ROOT / "ew-overseas-product-discovery/references/data-contracts.md").exists())
        self.assertTrue((ROOT / "ew-demand-source-router/scripts/fetch_public.py").exists())
        self.assertTrue((ROOT / "ew-validation-assets/scripts/build_experiment.py").exists())
        self.assertTrue((ROOT / "ew-demand-validation-review/scripts/review_experiment.py").exists())


if __name__ == "__main__":
    unittest.main()
