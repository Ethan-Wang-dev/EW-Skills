---
name: ew-demand-opportunity
description: "把多源证据按人群、场景和任务聚类成出海产品机会卡片，明确证据、缺口和下一步。"
---

# EW Demand Opportunity

## Purpose

Use this skill after evidence records have been normalized. It turns observations into opportunity hypotheses without silently upgrading a signal into validation.

## Workflow

1. Deduplicate records and keep conflicting values with dates and scope.
2. Cluster by `persona + trigger + job_to_be_done + desired_outcome`, not by tool name or keyword.
3. Separate first-party evidence from external evidence. A cluster needs a clear recurring problem and a plausible reachable user before it is `evidence-backed`.
4. Summarize current alternatives, failure cost, apparent value, strongest evidence, and missing proof.
5. Write one opportunity card per materially different user/scenario/market. Do not merge countries, languages, or payment contexts that change the decision.

## Output

```yaml
opportunity_name: ""
persona: ""
scenario: ""
problem: ""
desired_outcome: ""
current_alternatives: []
knowledge_base_evidence_ids: []
external_evidence_ids: []
evidence_summary: ""
pain_level: entertainment|interest|efficiency|money_making|must_have|unknown
value_created: "time, labor, money, risk, or revenue"
payment_signal: none|weak|possible|direct|unknown
target_markets: []
likely_channels: []
competitive_gap: ""
delivery_risks: []
unanswered_questions: []
minimum_test: ""
status: lead|evidence-backed|ready-for-validation|unvalidated
next_action: ""
```

## Guardrails

- Search volume, likes, traffic, rankings, server size, and competitor existence are discovery signals, not product validation.
- “Ready for validation” means the next experiment is well-defined; it does not mean the product is validated.
- Keep copied claims linked to their original source and label self-reported revenue or estimates.
