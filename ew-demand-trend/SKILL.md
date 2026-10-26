---
name: ew-demand-trend
description: "监测新词、新模型、新项目、新页面和新广告，把早期趋势转成可验证的机会线索。"
---

# EW Demand Trend

## Workflow

1. Define a monitoring scope, baseline date, source list, cadence, and change threshold.
2. Trace early sources such as X accounts, Hugging Face, arXiv, GitHub releases/issues, Product Hunt, new domains, new pages, ads, and community requests.
3. Record first source, timestamp, change, downstream adoption signal, and likely user/workflow affected.
4. Use scheduled tasks or monitoring tools only when the user has authorized the account and cadence. Preserve a prior snapshot for comparison.
5. Turn a trend into a demand hypothesis and route it to keyword, community, marketplace, or validation evidence. New technology alone is not demand.

## Output

```yaml
monitoring_scope: ""
baseline_at: ""
sources: []
signals: [{source: "", observed_at: "", change: "", downstream_behavior: ""}]
new_terms: []
opportunity_hypotheses: []
evidence_ids: []
next_gap: ""
limits: []
```
