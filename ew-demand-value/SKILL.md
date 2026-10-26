---
name: ew-demand-value
description: "评估出海产品机会的痛点、价值、付费、国家、竞争、渠道和投入回报，不用单一指标替代判断。"
---

# EW Demand Value

## Purpose

Use this skill after an opportunity card exists and before choosing a validation experiment. It answers “值得不值得投入，以及先验证哪一个假设”，not “一定能赚钱”。

## Workflow

1. Rate the pain context: entertainment, interest, efficiency, money-making, or must-have. Explain what users save, earn, or risk losing.
2. Assess payment evidence separately: direct payment/pre-sale, paid service, repeat use/referral, real task, intent, metric, or lead.
3. Assess market quality: country, language, currency, payment method, purchasing power, and likely buyer—not global traffic alone.
4. Assess competition and channel: competitor offer/pricing, persistent ads, search difficulty, referral/social sources, and whether the user can be reached.
5. Assess delivery: API/model cost, speed, quality, privacy, copyright, platform policy, review/approval, rate limits, and manual fallback.
6. Record assumptions and run a simple unit-economics sanity check: expected contribution per qualified user minus acquisition, delivery, and operating cost. Use ranges when values are estimates.
7. Identify the single largest uncertainty and hand it to `ew-demand-validation`.

## Output

```yaml
pain_assessment: {level: "", reason: "", evidence_ids: []}
value_proposition: ""
payment_assessment: {signal: none|weak|possible|direct|unknown, evidence_ids: [], missing: ""}
market_assessment: {markets: [], buyer: "", purchasing_power: "", payment_notes: "", evidence_ids: []}
competition_and_channel: {gap: "", channels: [], acquisition_hypothesis: "", evidence_ids: []}
delivery_assessment: {cost_range: "", constraints: [], fallback: "", evidence_ids: []}
roi_sanity_check: ""
largest_uncertainty: ""
decision: investigate|validate|adjust|stop
```

## Guardrails

- CPC, competitor price, ad persistence, revenue dashboards, and traffic are useful context; they are not your revenue or proof of product-market fit.
- A third-party wrapper can win through reach, aggregation, price, limits, workflow, or adjacent service. State which mechanism is being tested.
- Do not give a high score merely because a market is large. Keep value, reachability, delivery, and evidence strength separate.
