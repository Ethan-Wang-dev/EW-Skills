---
name: ew-overseas-product-discovery
description: "端到端帮助出海创业者分析产品机会、选择最小验证方式、生成验证材料并复盘真实结果。"
---

# EW Overseas Product Discovery

## User-facing promise

Give the user one of three simple outcomes:

1. **分析机会**：这个需求是什么、证据在哪里、值不值得继续看；
2. **设计验证**：当前最大未知是什么，最便宜的验证方式是什么；
3. **复盘结果**：真实用户行为说明了什么，下一步继续、调整还是停止。

The internal workflow may be complex, but the user-facing answer must lead with one recommended next action and link to supporting evidence.

Use the shared handoff fields in [references/data-contracts.md](references/data-contracts.md). In particular, keep the chain `ResearchBrief → EvidenceGap → AdapterRun/EvidenceRecord → OpportunityCard → ValueAssessment/ValidationPlan → ValidationAsset → ExperimentRun → DecisionRecord` intact so a later experiment can update, rather than overwrite, the original opportunity.

## End-to-end workflow

1. Run `ew-demand-intake` to identify the entry mode: idea, knowledge base, keyword/audience, or monitoring.
2. If the user supplied a folder or notes, run `ew-demand-kb` before external research.
3. Use `ew-demand-source-router` to choose only the sources needed for the current evidence gap. Use public HTTP/API, allowed browser automation, user-authorized access, or user exports; never bypass access controls.
4. Route the selected source to the smallest specialist: `ew-demand-keyword`, `ew-demand-community`, `ew-demand-marketplace`, `ew-demand-reviews`, or `ew-demand-trend`. These modules collect source-shaped observations; they do not make the final opportunity decision. If the selected gap is internal knowledge, stay with `ew-demand-kb`.
5. Pass observations to `ew-demand-evidence` and preserve first-party versus external evidence, dates, locators, strength, conflicts, and coverage limits. If the gap is still open, return to step 3 with a new small batch.
6. Run `ew-demand-opportunity` to cluster by user, trigger, job, and desired result.
7. Run `ew-demand-value` to assess pain, value, payment, and delivery assumptions and identify the largest uncertainty.
8. For a candidate cluster with open competition, channel, or geography gaps, run `ew-demand-competitor` and `ew-demand-geo` to fill them; do not run a broad crawl before a cluster exists. Merge their evidence back into the value assessment.
9. Run `ew-demand-score` to rank dimensions and expose fatal gaps without averaging them away.
10. If the user asks for an actionable next step, run `ew-demand-validation`. Choose a mode based on the largest uncertainty; do not default to a Landing Page.
11. Run `ew-validation-assets` to create the smallest honest test asset: concierge offer, marketplace listing, landing/pre-sale page, prototype/demo, community/outreach copy, ad set, or B2B pilot one-pager.
12. After the user supplies results, run `ew-demand-validation-review` and append new evidence to the opportunity history, then route any new gap back to step 3.

## Routing rules

- No clear problem or recent incident → interview/community test.
- User can perform the outcome manually → concierge or marketplace test.
- Clear promise and price → transparent pre-sale or paid pilot, optionally with a Landing Page.
- Workflow or output quality is uncertain → prototype, demo, or sample delivery.
- Demand is plausible but reachability is uncertain → one capped channel test: community, personalized outreach, partner/referral, directory, or paid traffic.
- First users exist → repeat task, renewal, or referral test.

## Required final response

Lead with:

```yaml
status: lead|evidence-backed|ready-for-validation|validated_for_next_stage|stop
one_sentence_answer: ""
strongest_evidence: []
largest_uncertainty: ""
recommended_next_action: ""
success_threshold: ""
stop_condition: ""
```

Then provide, as relevant:

- concise opportunity card;
- evidence table with source links/locators and strength;
- missing evidence and access limitations;
- validation mode and why it fits;
- generated asset links or contents;
- result interpretation and decision history.

## Evidence and authorization boundaries

- Do not claim a market is validated from search volume, likes, votes, traffic, rankings, or competitor existence.
- Do not claim a product is validated without behavior such as a real task, payment, repeat use, referral, or equivalent commitment.
- Do not auto-publish pages, connect user payment credentials, spend ad budget, send mass outreach, or modify external accounts without explicit authorization.
- Do not use Firecrawl or add it as a dependency.
- If a site is blocked, paywalled, private, rate-limited, or unavailable, report the limitation and use an allowed fallback or request an export.
- If the blocked source is decision-critical (for example keyword/traffic estimates, private community language, or payment/revenue evidence), do not silently drop the gap: offer the user-authorized browser profile/state path or local export ingestion, keep the gap high priority, and state exactly what remains unknown.
