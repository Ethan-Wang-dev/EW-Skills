import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import render_report


def fixture():
    return {
        "idea": {**{k: "用户明确或未确认" for k in render_report.IDEA_FIELDS},
                 "workflow": ["输入", "处理", "输出"], "core_capabilities": ["剪藏"]},
        "projects": [{**{k: "有依据的描述" for k in render_report.PROJECT_FIELDS},
                      "repo": "sample/clipper", "workflow": ["点击", "保存"],
                      "capabilities": ["捕获网页"], "overlap": ["同样捕获网页"],
                      "differences": ["没有确认移动端"],
                      "product_match": {"stars": 4, "reason": "主要工作流一致"},
                      "functional_match": {"stars": 3, "reason": "部分能力覆盖"},
                      "technical_match": {"stars": None, "reason": "未指定技术基线"},
                      "workflow_checks": [{"step": "保存", "status": "unknown", "evidence": "尚未核验源码"}]}],
        "conclusion": {"closest": "sample/clipper", "common_ground": "捕获", "unconfirmed": "移动端", "next": "保存流程"},
        "retrieval": {"summary": "部分检索，未运行候选程序", "artifact": "[记录](/tmp/example.json)"},
    }


class ReportTests(unittest.TestCase):
    def test_requester_and_product_user_are_distinct_in_output(self):
        data = fixture()
        data["idea"]["requester"] = "AI 实践者"
        data["idea"]["target_user"] = "内容研究者"
        report = render_report.render(data)
        self.assertIn("Skill 使用者：AI 实践者", report)
        self.assertIn("用户与场景：内容研究者", report)

    def test_renders_reasoned_stars_and_unknown_separately(self):
        report = render_report.render(fixture())
        self.assertIn("⭐️⭐️⭐️⭐️（4/5） 主要工作流一致", report)
        self.assertIn("❔未确认 未指定技术基线", report)
        self.assertIn("工作流：点击 → 保存", report)

    def test_overlap_and_differences_are_separate_bullet_groups(self):
        report = render_report.render(fixture())
        self.assertIn("主要重合：\n\n- 同样捕获网页", report)
        self.assertIn("关键差异：\n\n- 没有确认移动端", report)
        self.assertIn("维护状态：", report)
        self.assertIn("成熟度：", report)
        self.assertIn("许可证：", report)

    def test_each_recommended_project_requires_all_product_fields(self):
        for key in ("target_user", "scenario", "workflow", "maintenance", "maturity", "functional_match"):
            data = fixture()
            del data["projects"][0][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                render_report.render(data)

    def test_invalid_star_values_rejected(self):
        for stars in (0, 6, 3.5, "高", True):
            data = fixture()
            data["projects"][0]["product_match"]["stars"] = stars
            with self.subTest(stars=stars), self.assertRaises(ValueError):
                render_report.render(data)

    def test_missing_code_evidence_cannot_render_as_verified(self):
        data = fixture()
        data["projects"][0]["workflow_checks"] = [{"step": "保存", "status": "code_observed", "evidence": ""}]
        with self.assertRaises(ValueError):
            render_report.render(data)

    def test_empty_shortlist_allowed_and_duplicates_rejected(self):
        data = fixture()
        data["projects"].append(copy.deepcopy(data["projects"][0]))
        with self.assertRaises(ValueError):
            render_report.render(data)
        data["projects"] = []
        self.assertIn("检索范围", render_report.render(data))

    def test_card_limits_fail_instead_of_silent_truncation(self):
        data = fixture()
        data["projects"][0]["overlap"] = ["a", "b", "c", "d"]
        with self.assertRaisesRegex(ValueError, "compress"):
            render_report.render(data)

    def test_recommendation_limit_is_explicit(self):
        data = fixture()
        data["projects"] = [copy.deepcopy(data["projects"][0]) for _ in range(6)]
        for i, project in enumerate(data["projects"]):
            project["repo"] = f"sample/clipper-{i}"
        with self.assertRaisesRegex(ValueError, "raw artifact"):
            render_report.render(data)


if __name__ == "__main__":
    unittest.main()
