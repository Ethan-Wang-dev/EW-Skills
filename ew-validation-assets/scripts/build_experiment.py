#!/usr/bin/env python3
"""Build a local, honest validation asset and an event log template.

The script is deliberately local-only: it does not publish, send outreach, run
ads, charge a payment method, or call an analytics service. A user may opt in
to a form action or event endpoint in the input spec; those values are copied
to the generated artifact and are never guessed by this script.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ASSET_TYPES = {
    "landing_page",
    "preorder_page",
    "service_listing",
    "outreach_script",
    "prototype",
    "demo",
    "community_post",
    "ad_set",
    "pilot_one_pager",
    "followup",
}
EVENTS = {
    "qualified_view",
    "reply",
    "lead",
    "task_submitted",
    "demo_completed",
    "quote_accepted",
    "deposit",
    "payment",
    "repeat_use",
    "referral",
}
PAGE_TYPES = {"landing_page", "preorder_page"}


def text(value: Any, field: str, *, default: str = "") -> str:
    if value is None:
        value = default
    if not isinstance(value, str) or not value.strip():
        if default:
            return default
        raise ValueError(f"{field}: expected non-empty text")
    return value.strip()


def optional_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def string_list(value: Any, field: str, *, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field}: expected a list of non-empty strings")
    return [item.strip() for item in value]


def validate_destination(value: str, field: str) -> str:
    """Allow relative paths, fragments, and explicit HTTP(S) destinations only."""
    if not value:
        return value
    if value.startswith("//"):
        raise ValueError(f"{field}: protocol-relative destinations are not allowed")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"", "http", "https"}:
        raise ValueError(f"{field}: only relative, http, or https destinations are allowed")
    return value


def validate_spec(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("input: expected a JSON object")
    asset_type = text(raw.get("asset_type"), "asset_type")
    if asset_type not in ASSET_TYPES:
        raise ValueError(f"asset_type: expected one of {', '.join(sorted(ASSET_TYPES))}")

    spec: dict[str, Any] = {
        "experiment_id": text(raw.get("experiment_id"), "experiment_id"),
        "opportunity_id": optional_text(raw.get("opportunity_id")),
        "asset_type": asset_type,
        "audience": text(raw.get("audience") or raw.get("target_user"), "audience"),
        "scenario": text(raw.get("scenario"), "scenario", default="unknown"),
        "problem": text(raw.get("problem"), "problem"),
        "promise": text(raw.get("promise") or raw.get("desired_outcome"), "promise"),
        "headline": optional_text(raw.get("headline")) or text(raw.get("promise") or raw.get("desired_outcome"), "promise"),
        "how_it_works": string_list(raw.get("how_it_works"), "how_it_works", default=["提交一个真实任务", "获得一次可检查的结果", "反馈是否值得继续使用"]),
        "example": optional_text(raw.get("example")) or "尚未提供真实样例；请在发布前替换为标注清楚的样例或 Mockup。",
        "offer": text(raw.get("offer"), "offer", default="先用一个小范围任务验证结果"),
        "price": text(raw.get("price"), "price", default="待测试"),
        "cta_label": text(raw.get("cta_label"), "cta_label", default="提交真实任务"),
        "cta_url": optional_text(raw.get("cta_url")),
        "channel": text(raw.get("channel"), "channel", default="待选择"),
        "turnaround": text(raw.get("turnaround"), "turnaround", default="待确认"),
        "requirements": string_list(raw.get("requirements"), "requirements"),
        "faq": raw.get("faq", []),
        "privacy_note": text(raw.get("privacy_note"), "privacy_note", default="只收集完成本次实验所需的信息，不会在未说明的情况下出售或转交。"),
        "delivery_terms": text(raw.get("delivery_terms"), "delivery_terms", default="这是验证实验，不代表完整产品承诺；交付范围和时间以页面说明为准。"),
        "refund_terms": text(raw.get("refund_terms"), "refund_terms", default="如涉及预售或押金，请在发布前补充明确的退款和履约条款。"),
        "form_action": optional_text(raw.get("form_action")),
        "event_endpoint": optional_text(raw.get("event_endpoint")),
        "events": string_list(raw.get("events"), "events", default=["qualified_view", "lead", "task_submitted", "payment"]),
        "success_threshold": raw.get("success_threshold", {}),
        "stop_condition": raw.get("stop_condition", {}),
        "time_window": text(raw.get("time_window"), "time_window", default="待填写"),
    }
    if len(spec["events"]) == 0 or any(event not in EVENTS for event in spec["events"]):
        raise ValueError(f"events: use only {', '.join(sorted(EVENTS))}")
    if not isinstance(spec["faq"], list) or any(not isinstance(item, dict) for item in spec["faq"]):
        raise ValueError("faq: expected a list of objects with question and answer")
    for item in spec["faq"]:
        text(item.get("question"), "faq.question")
        text(item.get("answer"), "faq.answer")
    for key in ("success_threshold", "stop_condition"):
        if not isinstance(spec[key], dict):
            raise ValueError(f"{key}: expected a JSON object")
    if len(spec["how_it_works"]) > 5:
        raise ValueError("how_it_works: keep the experiment to at most five steps")
    validate_destination(spec["cta_url"], "cta_url")
    validate_destination(spec["form_action"], "form_action")
    validate_destination(spec["event_endpoint"], "event_endpoint")
    return spec


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_list(items: list[str]) -> str:
    return "\n".join(f"<li>{esc(item)}</li>" for item in items) or "<li>待填写</li>"


def render_faq(items: list[dict[str, Any]]) -> str:
    if not items:
        return "<p>暂无 FAQ；发布前补充交付、退款和隐私说明。</p>"
    return "\n".join(
        f"<details><summary>{esc(item['question'].strip())}</summary><p>{esc(item['answer'].strip())}</p></details>"
        for item in items
    )


def render_page(spec: dict[str, Any]) -> str:
    preorder = spec["asset_type"] == "preorder_page"
    form_action = f' action="{esc(spec["form_action"])}" method="post"' if spec["form_action"] else ""
    endpoint = json.dumps(spec["event_endpoint"] or "")
    experiment_id = json.dumps(spec["experiment_id"])
    cta_url = spec["cta_url"] or "#cta-form"
    page_label = "预售验证" if preorder else "需求验证"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(spec['headline'])} · {page_label}</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; color: #172033; background: #f7f8fb; line-height: 1.6; }}
    main {{ max-width: 760px; margin: 0 auto; padding: 32px 20px 72px; }}
    .tag {{ display: inline-block; color: #3857d6; font-weight: 700; font-size: .85rem; letter-spacing: .04em; text-transform: uppercase; }}
    h1 {{ font-size: clamp(2rem, 7vw, 4rem); line-height: 1.08; margin: 12px 0 20px; }}
    h2 {{ margin-top: 40px; }}
    .lede {{ font-size: 1.2rem; color: #4c5870; }}
    .card {{ background: white; border: 1px solid #e3e7ef; border-radius: 16px; padding: 24px; margin-top: 24px; box-shadow: 0 8px 24px rgb(30 45 80 / 5%); }}
    .steps {{ padding-left: 24px; }}
    .cta {{ display: grid; gap: 12px; }}
    label {{ font-weight: 600; }}
    input, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #c8cfdd; border-radius: 8px; padding: 12px; font: inherit; margin-top: 5px; }}
    textarea {{ min-height: 100px; resize: vertical; }}
    button, .button {{ display: inline-block; border: 0; border-radius: 999px; padding: 12px 20px; background: #3857d6; color: white; font-weight: 700; text-decoration: none; cursor: pointer; }}
    .note {{ color: #68748b; font-size: .9rem; }}
    details {{ padding: 12px 0; border-bottom: 1px solid #e7eaf0; }}
    summary {{ cursor: pointer; font-weight: 600; }}
    .success {{ display: none; color: #11643b; background: #e8f6ee; padding: 12px; border-radius: 8px; }}
  </style>
</head>
<body>
<main>
  <span class="tag">{page_label} · pre-launch</span>
  <h1>{esc(spec['headline'])}</h1>
  <p class="lede">{esc(spec['promise'])}</p>
  <p class="note">适用人群：{esc(spec['audience'])} · 场景：{esc(spec['scenario'])}</p>
  <p><a class="button" href="{esc(cta_url)}">{esc(spec['cta_label'])}</a></p>
  <section class="card">
    <h2>你现在遇到的问题</h2>
    <p>{esc(spec['problem'])}</p>
    <h2>怎么验证</h2>
    <ol class="steps">{render_list(spec['how_it_works'])}</ol>
    <h2>这次提供什么</h2>
    <p>{esc(spec['offer'])}</p>
    <p><strong>价格/条件：</strong>{esc(spec['price'])}</p>
    <p><strong>交付：</strong>{esc(spec['turnaround'])}</p>
    <p><strong>样例：</strong>{esc(spec['example'])}</p>
  </section>
  <section class="card cta" id="cta-form">
    <h2>{esc(spec['cta_label'])}</h2>
    <form{form_action}>
      <label for="email">联系邮箱（可选）</label>
      <input id="email" name="email" type="email" autocomplete="email" placeholder="you@example.com">
      <label for="task">请描述一个最近发生的真实任务</label>
      <textarea id="task" name="task" required placeholder="发生了什么？你现在怎么解决？"></textarea>
      <button type="submit">{esc(spec['cta_label'])}</button>
    </form>
    <p id="success" class="success" role="status">已记录。若这是人工验证，我们会按页面承诺联系你。</p>
    <p class="note">{esc(spec['privacy_note'])}</p>
  </section>
  <section class="card">
    <h2>说明</h2>
    <p>{esc(spec['delivery_terms'])}</p>
    <p>{esc(spec['refund_terms'])}</p>
    <h2>常见问题</h2>
    {render_faq(spec['faq'])}
  </section>
</main>
<script>
const experimentId = {experiment_id};
const eventEndpoint = {endpoint};
const eventKey = "ew-experiment-events";
function logEvent(event, properties = {{}}) {{
  const row = {{ experiment_id: experimentId, event, occurred_at: new Date().toISOString(), ...properties }};
  const current = JSON.parse(localStorage.getItem(eventKey) || "[]");
  current.push(row);
  localStorage.setItem(eventKey, JSON.stringify(current));
  if (eventEndpoint && navigator.sendBeacon) {{
    navigator.sendBeacon(eventEndpoint, new Blob([JSON.stringify(row)], {{type: "application/json"}}));
  }}
}}
logEvent("qualified_view");
document.querySelector("form").addEventListener("submit", (event) => {{
  logEvent("task_submitted", {{ has_email: Boolean(document.querySelector("#email").value) }});
  if (!event.currentTarget.action || event.currentTarget.action === window.location.href) {{
    event.preventDefault();
    document.querySelector("#success").style.display = "block";
  }}
}});
document.querySelectorAll("a[href^='#']").forEach((link) => link.addEventListener("click", () => logEvent("lead", {{ target: link.getAttribute("href") }})));
</script>
</body>
</html>
"""


def section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def render_markdown(spec: dict[str, Any]) -> str:
    title = spec["headline"]
    common = [
        f"# {title}",
        f"> 验证实验：`{spec['experiment_id']}`（pre-launch）",
        section("适用对象", spec["audience"]),
        section("最近场景", spec["scenario"]),
        section("问题", spec["problem"]),
        section("承诺的结果", spec["promise"]),
        section("提供什么", spec["offer"]),
        section("价格/条件", spec["price"]),
        section("交付时间", spec["turnaround"]),
    ]
    if spec["asset_type"] == "service_listing":
        common.extend([
            section("需要买方提供", "\n".join(f"- {item}" for item in spec["requirements"]) or "- 一个真实任务和必要输入"),
            section("行动邀请", f"{spec['cta_label']}（渠道：{spec['channel']}）"),
        ])
    elif spec["asset_type"] in {"outreach_script", "community_post", "followup"}:
        common.extend([
            section("可直接发送的文案", f"我在帮助 {spec['audience']} 处理这个问题：{spec['problem']}。\n\n你最近一次遇到它是什么时候？你现在怎么解决？如果你愿意，我可以用一个真实任务做一次小范围验证。"),
            section("跟进问题", "角色、最近任务、当前替代、发生频率、失败代价、愿意尝试/付费的条件"),
        ])
    elif spec["asset_type"] in {"prototype", "demo"}:
        common.extend([
            section("测试任务", "让用户用一个真实样例完成一次完整流程。"),
            section("观察点", "完成时间、卡住的位置、主动纠正次数、结果是否被接受、是否愿意再次使用"),
        ])
    elif spec["asset_type"] == "pilot_one_pager":
        common.extend([
            section("试点范围", "一个团队、一个工作流、一个明确周期；不要把试点写成完整产品承诺。"),
            section("成功指标", "时间、质量、成本、收入或风险中选择一个主指标，并在实验前写出基线。"),
            section("下一承诺", f"{spec['cta_label']}；决策人和采购步骤需在执行前确认。"),
        ])
    elif spec["asset_type"] == "ad_set":
        common.extend([
            section("广告变体", f"A：{spec['promise']}\n\nB：{spec['problem']} → {spec['promise']}"),
            section("投放边界", f"渠道：{spec['channel']}；预算和停止条件必须以 ValidationPlan 为准。"),
        ])
    common.extend([
        section("样例", spec["example"]),
        section("隐私与履约", f"{spec['privacy_note']}\n\n{spec['delivery_terms']}\n\n{spec['refund_terms']}"),
        section("事件记录", " → ".join(spec["events"])),
    ])
    return "\n".join(common).rstrip() + "\n"


def write_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["occurred_at", "event", "qualified", "actor_ref", "market", "notes"])
        writer.writeheader()


def build(raw: Any, output_dir: Path, *, force: bool = False) -> dict[str, Any]:
    spec = validate_spec(raw)
    if output_dir.exists() and any(output_dir.iterdir()):
        if not force:
            raise ValueError(f"output directory is not empty: {output_dir} (use --force only to replace generated files)")
        for child in output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    if spec["asset_type"] in PAGE_TYPES:
        (output_dir / "index.html").write_text(render_page(spec), encoding="utf-8")
        generated.append("index.html")
    else:
        filename = "service-listing.md" if spec["asset_type"] == "service_listing" else "message-or-brief.md"
        (output_dir / filename).write_text(render_markdown(spec), encoding="utf-8")
        generated.append(filename)
    write_csv(output_dir / "events.csv")
    generated.append("events.csv")

    generated.append("experiment.json")
    metadata = {
        "experiment_id": spec["experiment_id"],
        "opportunity_id": spec["opportunity_id"],
        "asset_type": spec["asset_type"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": generated,
        "event_map": [
            {"event": event, "definition": "按实验前定义记录；不要把未授权或不合格流量计入 qualified_count", "evidence_strength": "metric" if event == "qualified_view" else "behavior" if event in {"task_submitted", "demo_completed", "repeat_use", "referral", "quote_accepted"} else "direct_payment" if event in {"deposit", "payment"} else "lead"}
            for event in spec["events"]
        ],
        "preview_or_use_instructions": "网页：在输出目录运行 python3 -m http.server 8000，然后打开 http://localhost:8000/；其他材料：先人工检查承诺、价格、渠道和停止条件，再按规则发布。",
        "authorization_needed": ["发布到外部平台", "连接真实表单/支付/分析服务", "投放广告", "批量发送外联"],
        "known_limits": ["本地 events.csv 只是空白记录模板；浏览器事件默认保存在 localStorage，不会自动上传。", "页面和文案不能证明需求，必须结合 ExperimentRun 和预注册阈值复盘。"],
        "spec": spec,
    }
    (output_dir / "experiment.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"experiment_id": spec["experiment_id"], "asset_type": spec["asset_type"], "output_dir": str(output_dir), "files": generated}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="ValidationPlan-like JSON spec")
    parser.add_argument("--output-dir", required=True, help="Directory for local experiment assets")
    parser.add_argument("--force", action="store_true", help="Replace an existing non-empty generated directory")
    args = parser.parse_args()
    try:
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = build(raw, Path(args.output_dir), force=args.force)
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
