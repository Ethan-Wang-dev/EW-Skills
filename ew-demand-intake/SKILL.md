---
name: ew-demand-intake
description: "把出海产品想法、关键词、用户或知识库整理成明确的研究入口、目标用户、市场边界和待确认假设。"
---

# EW Demand Intake

## Purpose

Use this skill at the start of overseas-product research. Turn an ambiguous request into a short `ResearchBrief` without pretending that unknown users, countries, budgets, or technologies are known.

## Input

Accept an idea, keyword, audience, market, existing research folder, or monitoring request. Keep the Skill requester separate from the product's end user.

## Workflow

1. Identify the entry mode: `idea`, `knowledge_base`, `keyword_or_audience`, or `monitoring`.
2. Extract the intended user, triggering situation, problem, desired outcome, target market, current alternative, and constraints.
3. Ask at most one focused question only if the ambiguity would change the research direction. Otherwise mark the field `unknown` and proceed.
4. State confirmed facts, assumptions, and non-critical unknowns separately.
5. Write the first evidence gaps: frequency, value/payment, distribution, geography, competitive gap, or delivery risk.

## Output

```yaml
research_mode: idea|knowledge_base|keyword_or_audience|monitoring
requester: ""
target_user: ""
scenario: ""
problem: ""
desired_outcome: ""
target_markets: []
current_alternative: ""
constraints: []
confirmed: []
assumptions: []
unknowns: []
evidence_gaps: [frequency|value_or_payment|distribution|geography|competition|delivery]
seed_phrases: []
next_action: ""
```

## Guardrails

- Do not start with a feature or model capability when the user gave a problem.
- Do not turn a user's preferred country or price into market evidence.
- Do not start a full web crawl from this skill; pass the brief to the source router.
- For monitoring, preserve the baseline date and the exact change the user wants to detect.
