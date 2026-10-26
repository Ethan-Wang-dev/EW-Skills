# Validation asset templates

## Landing or pre-sale page

```text
Audience: [one narrowly defined user]
Problem: [specific recent situation]
Promise: [measurable or observable result]
How it works: [three short steps]
Example/sample: [truthful sample or clearly marked mockup]
Offer and price: [price, pilot or pre-sale terms]
Primary CTA: [submit task / join waitlist / reserve / buy pilot]
FAQ: [delivery date, limits, privacy, refund]
Events: view → CTA click → form/task → checkout/deposit → payment
```

## Concierge or marketplace service

```text
Service title: [result + audience]
Who it is for: [specific buyer]
Input required: [files/data/access]
Delivered result: [format and quality bar]
Turnaround: [honest time]
Price: [one test price]
Example: [sample]
Buyer question: [ask for a real task, not a hypothetical opinion]
```

## Community or direct outreach

```text
Context: [show you understand the user's situation]
Question: [ask about a recent instance or workaround]
Offer: [offer a small sample or manual help]
CTA: [reply / submit a task / join a short interview]
Follow-up fields: role, scenario, current alternative, frequency, cost, willingness to try/pay
```

## Prototype or demo

```text
Task: [one job to complete]
Input: [realistic sample]
Expected output: [visible result]
Test script: [3–5 actions]
Observe: completion, hesitation, correction, output acceptance, repeat intent
```

## B2B pilot one-pager

```text
Buyer and workflow: [team + recurring job]
Current cost/risk: [specific]
Pilot scope: [one workflow and duration]
Success metric: [time, quality, cost, revenue, or risk]
Price and decision maker: [explicit]
Next commitment: [paid pilot / procurement step / signed intent]
```

## Local builder input

`ew-validation-assets/scripts/build_experiment.py` accepts a small JSON file. Keep the promise, audience, price, CTA, channel, threshold, and stop condition consistent with the `ValidationPlan`; the script does not invent missing market or payment evidence.

```json
{
  "experiment_id": "X-2026-001",
  "opportunity_id": "O-001",
  "asset_type": "landing_page",
  "audience": "一个明确的目标用户群",
  "scenario": "最近发生的具体任务",
  "problem": "现在的替代方案为什么不够好",
  "promise": "一次可检查的结果",
  "offer": "人工完成一批真实任务",
  "price": "首批测试价 $19",
  "cta_label": "提交真实任务",
  "channel": "一个具体社群或定向触达渠道",
  "events": ["qualified_view", "task_submitted", "payment"],
  "success_threshold": {"min_events": {"payment": 1}},
  "stop_condition": {"max_total_cost": 100},
  "time_window": "7 days"
}
```

运行后，在输出目录执行 `python3 -m http.server 8000` 可本地预览页面。打开浏览器开发者工具即可查看 `localStorage` 中的 `ew-experiment-events`；将合格事件人工去重后填入 `ExperimentRun.events`，再交给 `ew-demand-validation-review`。
