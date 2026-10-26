---
name: ew-demand-reviews
description: "从竞品和插件/应用评价中提取重复不满、缺失功能、可靠性和价格缺口。"
---

# EW Demand Reviews

## Workflow

1. Choose products with meaningful download, review, or usage evidence and define the user/scenario under study.
2. Sample recent and repeated low-rating reviews from Trustpilot, Chrome Web Store, App Store, or the product's public feedback area.
3. Capture exact complaint, date/version, user context, requested workaround, and whether the problem is systemic or one-off.
4. Cluster complaints by job and failure cost. Do not infer causation from rating alone.
5. Send repeated gaps to `ew-demand-opportunity`; send a proposed fix and sample output to `ew-demand-validation`.

## Output

```yaml
product: ""
review_source: ""
sample_scope: ""
complaints: []
repeated_gaps: []
positive_trust_signals: []
evidence_ids: []
validation_question: ""
limitations: []
```
