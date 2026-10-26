---
name: ew-demand-community
description: "从 Reddit、Discord、X 和公开论坛提取重复抱怨、绕路方案、用户请求与可触达社群。"
---

# EW Demand Community

## Workflow

1. Define the user/scenario and search terms before opening a community.
2. Use public pages or an explicitly authorized session. Search complaints, help requests, alternatives, pricing, broken workflows, and workarounds.
3. Capture independent occurrences with URL, date, role, market, exact wording, and whether a real recent task is described.
4. Count repeated specific problems; three independent occurrences are a useful discovery threshold, not payment proof.
5. For Discord, record public server size/growth only as a heat signal, identify channels where feedback is allowed, and note community rules.
6. Return evidence and an ethical outreach/feedback opportunity to the validation skill; do not cold-DM or mass-post.

## Output

```yaml
communities: [{name: "", url: "", access_state: "", rules: ""}]
repeated_problems: []
workarounds: []
requests_or_alternatives: []
heat_signals: []
evidence_ids: []
outreach_constraints: []
next_gap: ""
```
