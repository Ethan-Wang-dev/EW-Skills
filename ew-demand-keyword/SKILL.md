---
name: ew-demand-keyword
description: "用搜索词、趋势、相关查询和竞争数据判断出海需求信号，不把流量指标当成验证。"
---

# EW Demand Keyword

## Workflow

1. Start from the `SeedSet` produced from user language; expand result, pain, scenario, role, alternative, purchase, and platform terms.
2. Use Google Search/Trends first for public discovery; use Similarweb, Semrush, or Ahrefs only with authorized access/export when the question needs estimates, KD, CPC, landing pages, or country data.
3. Compare with a stable baseline and record country, language, window, query, related/rising terms, search intent, and visible competitors.
4. For SEO feasibility, inspect `site:`, `intitle:`, `allintitle:`, `inurl:`, `after:` and `before:` results; treat KGR/KD as heuristics, not conclusions.
5. Route raw observations to `ew-demand-evidence` and state what they do not prove.

## Output

```yaml
seed: ""
queries: []
market_and_locale: ""
time_window: ""
trend_and_related_terms: []
volume_cpc_kd: "unknown or sourced values"
competitor_pages: []
intent: informational|commercial|transactional|navigational|mixed|unknown
evidence_ids: []
limitations: []
next_gap: ""
```

## Guardrails

- Search data supports existence, intent, trend, or SEO feasibility—not willingness to pay or retention.
- A high volume in a low-purchasing-power market is not automatically attractive.
- Do not repeatedly hit unofficial endpoints; record rate limits and use a user export when needed.
