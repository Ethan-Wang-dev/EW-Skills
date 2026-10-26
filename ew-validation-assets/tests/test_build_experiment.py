import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_experiment import build


class BuildExperimentTests(unittest.TestCase):
    def spec(self):
        return {
            "experiment_id": "X-test-001",
            "asset_type": "landing_page",
            "audience": "独立出海开发者",
            "scenario": "每周需要整理用户反馈",
            "problem": "反馈分散在多个地方，难以形成可执行任务",
            "promise": "在一天内得到一份可检查的反馈摘要",
            "offer": "人工处理一批真实反馈",
            "price": "首批测试价 $19",
            "cta_label": "提交真实任务",
            "events": ["qualified_view", "task_submitted", "payment"],
            "success_threshold": {"min_events": {"payment": 1}},
        }

    def test_builds_local_page_and_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            result = build(self.spec(), Path(directory) / "asset")
            output = Path(directory) / "asset"
            self.assertEqual(result["asset_type"], "landing_page")
            self.assertTrue((output / "index.html").exists())
            self.assertTrue((output / "events.csv").read_text().startswith("occurred_at,event"))
            metadata = json.loads((output / "experiment.json").read_text())
            self.assertEqual(metadata["experiment_id"], "X-test-001")
            self.assertIn("task_submitted", [item["event"] for item in metadata["event_map"]])

    def test_refuses_existing_directory_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "asset"
            output.mkdir()
            (output / "keep.txt").write_text("user file")
            with self.assertRaises(ValueError):
                build(self.spec(), output)

    def test_rejects_script_destinations(self):
        spec = self.spec()
        spec["cta_url"] = "javascript:alert(1)"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                build(spec, Path(directory) / "asset")


if __name__ == "__main__":
    unittest.main()
