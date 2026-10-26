---
name: ew-demand-score
description: "按证据和不确定性对出海机会排序，区分需求、付费、获客和交付，不用总分代替验证。"
---

# EW Demand Score

## Workflow

1. Score only after an opportunity card, value assessment, and known evidence gaps exist.
2. Rate 1–5 with a short evidence-linked reason: demand reality, frequency, pain/value, payment ability, market quality, reachability, competitive gap, and delivery/operations feasibility.
3. Keep score dimensions separate; do not average away a fatal gap such as no reachable buyer or unacceptable unit cost.
4. Mark `unvalidated` whenever payment, repeat use, referral, or an equivalent commitment is missing.
5. Select the next validation action based on the lowest-confidence/highest-impact dimension.

## Output

```yaml
opportunity_id: ""
scores:
  demand_reality: {score: 1, reason: "", evidence_ids: []}
  frequency: {score: 1, reason: "", evidence_ids: []}
  pain_or_value: {score: 1, reason: "", evidence_ids: []}
  payment_ability: {score: 1, reason: "", evidence_ids: []}
  market_quality: {score: 1, reason: "", evidence_ids: []}
  reachability: {score: 1, reason: "", evidence_ids: []}
  competitive_gap: {score: 1, reason: "", evidence_ids: []}
  delivery_feasibility: {score: 1, reason: "", evidence_ids: []}
confidence: low|medium|high
fatal_gaps: []
decision: investigate|validate|adjust|stop|unvalidated
next_action: ""
```
