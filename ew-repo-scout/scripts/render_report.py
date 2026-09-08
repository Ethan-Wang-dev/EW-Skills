#!/usr/bin/env python3
"""Validate product-comparison fields and render readable project cards.

Formatting/coverage validation only; the agent must substantiate every claim.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

IDEA_FIELDS = ("original", "requester", "target_user", "scenario", "problem", "outcome",
               "current_alternative", "form_and_constraints", "confirmed", "assumptions", "unknowns")
PROJECT_FIELDS = ("repo", "relationship", "form", "target_user", "scenario", "problem",
                  "outcome", "maintenance", "maturity", "license", "takeaway")
RATINGS = (("product_match", "产品匹配"), ("functional_match", "功能覆盖"), ("technical_match", "技术匹配"))
CHECK_STATUSES = {"code_observed": "源码观察", "docs_only": "文档声明", "unknown": "未确认"}

# The report is intentionally complete, but each card must remain scannable.
# These are validation limits rather than truncation rules: the authoring agent
# must compress the source material before rendering so no evidence disappears.
LIST_LIMITS = {
    "idea.workflow": 5,
    "idea.core_capabilities": 6,
    "projects[].workflow": 5,
    "projects[].capabilities": 6,
    "projects[].overlap": 3,
    "projects[].differences": 3,
    "projects[].workflow_checks": 5,
}
MAX_PROJECTS = 5


def require_text(obj, key, path):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}.{key}: required nonempty text; use an explicit unknown when evidence is missing")
    return value.strip()


def require_list(obj, key, path):
    value = obj.get(key)
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{path}.{key}: required nonempty list of text")
    return value


def check_list_limit(value, limit, path):
    if len(value) > limit:
        raise ValueError(
            f"{path}: at most {limit} items; compress the content before rendering "
            "(the renderer never truncates evidence)"
        )


def stars_text(rating):
    value = rating["stars"]
    return "❔未确认" if value is None else "⭐️" * value + f"（{value}/5）"


def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("idea"), dict):
        raise ValueError("idea: required object")
    idea = data["idea"]
    for field in IDEA_FIELDS:
        require_text(idea, field, "idea")
    for field in ("workflow", "core_capabilities"):
        values = require_list(idea, field, "idea")
        check_list_limit(values, LIST_LIMITS[f"idea.{field}"], f"idea.{field}")
    projects = data.get("projects")
    if not isinstance(projects, list):
        raise ValueError("projects: required list; [] is allowed when no project was confirmed")
    if len(projects) > MAX_PROJECTS:
        raise ValueError(
            f"projects: at most {MAX_PROJECTS} recommended cards; move extra candidates to the raw artifact"
        )
    seen = set()
    for i, project in enumerate(projects):
        path = f"projects[{i}]"
        if not isinstance(project, dict):
            raise ValueError(path + ": required object")
        for field in PROJECT_FIELDS:
            require_text(project, field, path)
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", project["repo"]):
            raise ValueError(path + ".repo: expected owner/repo")
        if project["repo"].lower() in seen:
            raise ValueError(path + ".repo: duplicate project")
        seen.add(project["repo"].lower())
        for field in ("workflow", "capabilities", "overlap", "differences"):
            values = require_list(project, field, path)
            check_list_limit(values, LIST_LIMITS[f"projects[].{field}"], f"{path}.{field}")
        for key, _ in RATINGS:
            rating = project.get(key)
            if not isinstance(rating, dict) or "stars" not in rating:
                raise ValueError(path + "." + key + ": requires stars and reason")
            value = rating["stars"]
            if value is not None and (type(value) is not int or not 1 <= value <= 5):
                raise ValueError(path + "." + key + ".stars: use integer 1–5 or null")
            require_text(rating, "reason", path + "." + key)
        checks = project.get("workflow_checks")
        if not isinstance(checks, list) or not checks:
            raise ValueError(path + ".workflow_checks: required; explicitly mark unchecked steps unknown")
        check_list_limit(checks, LIST_LIMITS["projects[].workflow_checks"], path + ".workflow_checks")
        for j, check in enumerate(checks):
            cp = f"{path}.workflow_checks[{j}]"
            if not isinstance(check, dict) or check.get("status") not in CHECK_STATUSES:
                raise ValueError(cp + ".status: code_observed, docs_only or unknown")
            require_text(check, "step", cp)
            require_text(check, "evidence", cp)
    for key, fields in (("conclusion", ("closest", "common_ground", "unconfirmed", "next")),
                        ("retrieval", ("summary", "artifact"))):
        if not isinstance(data.get(key), dict):
            raise ValueError(key + ": required object")
        for field in fields:
            require_text(data[key], field, key)


def render(data):
    validate(data)
    idea = data["idea"]
    lines = ["**需求理解**", "", f"- 原始需求：{idea['original']}",
             f"- Skill 使用者：{idea['requester']}",
             f"- 用户与场景：{idea['target_user']}；{idea['scenario']}",
             f"- 要解决：{idea['problem']}",
             f"- 期望结果：{idea['outcome']}",
             f"- 当前替代：{idea['current_alternative']}",
             "- 工作流：" + " → ".join(idea["workflow"]),
             "- 核心能力：" + "；".join(idea["core_capabilities"]),
             f"- 形态与约束：{idea['form_and_constraints']}",
             f"- 口径：已明确「{idea['confirmed']}」；暂定「{idea['assumptions']}」；未知「{idea['unknowns']}」",
             "", "星级表示相对当前需求的匹配程度（5 星最高），不是 GitHub stars、项目质量或准确率；❔表示依据不足。", ""]
    for i, project in enumerate(data["projects"], 1):
        name = project["repo"]
        lines += [f"**{i}. [{name}](https://github.com/{name})**", "",
                  f"{project['relationship']} · {project['form']}", "",
                  f"- 用户与场景：{project['target_user']}；{project['scenario']}",
                  f"- 要解决：{project['problem']}",
                  f"- 结果：{project['outcome']}",
                  "- 工作流：" + " → ".join(project["workflow"]),
                  "- 核心能力：" + "；".join(project["capabilities"])]
        for key, label in RATINGS:
            rating = project[key]
            lines.append(f"- {label}：{stars_text(rating)} {rating['reason']}")
        lines += ["", "主要重合：", ""]
        lines += ["- " + value for value in project["overlap"]]
        lines += ["", "关键差异：", ""]
        lines += ["- " + value for value in project["differences"]]
        lines += ["", "工作流核验：", ""]
        for check in project["workflow_checks"]:
            lines.append(f"- {check['step']}：{CHECK_STATUSES[check['status']]} — {check['evidence']}")
        lines += ["", "项目状态：",
                  f"- 维护状态：{project['maintenance']}",
                  f"- 成熟度：{project['maturity']}",
                  f"- 许可证：{project['license']}",
                  f"- 为什么看：{project['takeaway']}"]
        if project.get("discovery"):
            lines.append("- 发现路径：" + project["discovery"])
        lines.append("")
    conclusion = data["conclusion"]
    lines += ["**判断**", "", f"- 最接近：{conclusion['closest']}",
              f"- 已有重合：{conclusion['common_ground']}",
              f"- 尚未确认：{conclusion['unconfirmed']}", f"- 优先研究：{conclusion['next']}",
              "", "**检索范围**", "", data["retrieval"]["summary"], "",
              "详细检索记录：" + data["retrieval"]["artifact"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Agent-authored evidence-based product report JSON")
    parser.add_argument("--output", help="Markdown output; stdout if omitted")
    args = parser.parse_args()
    try:
        output = render(json.loads(Path(args.input).read_text()))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
