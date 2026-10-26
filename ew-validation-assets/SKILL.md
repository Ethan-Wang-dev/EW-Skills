---
name: ew-validation-assets
description: "把需求验证计划转成最小可用的 Landing Page、预售页、服务页、原型、社群文案或广告素材。"
---

# EW Validation Assets

## Purpose

Use this skill only after `ew-demand-validation` selects a test mode. Generate the smallest artifact that exposes one offer to one audience and records one meaningful action.

Read [references/asset-templates.md](references/asset-templates.md) for the relevant template. Do not generate a full production product unless explicitly requested.

For a local, previewable artifact, use [scripts/build_experiment.py](scripts/build_experiment.py) with a JSON `ValidationPlan`-like spec:

```bash
python3 <skill-dir>/scripts/build_experiment.py \
  --input validation-spec.json \
  --output-dir ./experiments/<experiment-id>
```

The helper creates `index.html` for a landing/pre-sale page or Markdown for the other asset types, plus `experiment.json` and an empty `events.csv`. It is local-only by default; browser events stay in `localStorage` unless the user explicitly supplies an endpoint. Read [../ew-overseas-product-discovery/references/data-contracts.md](../ew-overseas-product-discovery/references/data-contracts.md) when a downstream Skill needs the exact `ValidationAsset` or `ExperimentRun` fields.

## Workflow

1. Read the hypothesis, target user, scenario, promise, offer, price, CTA, channel, events, threshold, and stop condition.
2. Select the asset matching the mode: static landing/pre-sale page, marketplace service listing, outreach/interview script, community post, clickable prototype brief, demo/sample output, ad variants, or B2B pilot one-pager.
3. Keep one audience, one problem, one promise, one primary CTA, and one price or pricing test.
4. Include truthful pre-launch status, delivery scope, refund/fulfillment terms when money is requested, and privacy/consent language for forms.
5. Produce files that can be previewed locally. Publishing, connecting credentials, spending ad budget, or charging users requires explicit user authorization.
6. Include an event map and a simple result log so behavior can be sent to `ew-demand-validation-review`.

## Output

```yaml
asset_type: landing_page|preorder_page|service_listing|outreach_script|prototype|demo|community_post|ad_set|pilot_one_pager|followup
files: []
preview_or_use_instructions: ""
primary_cta: ""
event_map: [{event: "", definition: "", evidence_strength: ""}]
experiment_id: ""
authorization_needed: []
known_limits: []
```

## Guardrails

- A generated page is an experiment asset, not proof of demand.
- Do not use fake testimonials, invented usage, false scarcity, or hidden charges.
- Do not auto-publish, configure payment, or launch ads without explicit authorization.
- If no credible audience/channel is available, return an outreach or interview asset instead of an isolated page.
