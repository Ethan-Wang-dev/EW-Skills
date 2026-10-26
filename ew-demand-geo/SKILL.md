---
name: ew-demand-geo
description: "评估出海机会的目标国家、语言、购买力、支付和本地化适配，不从全球流量直接推断价值。"
---

# EW Demand Geo

## Workflow

1. Start from a named persona and job; do not compare countries without a common scenario.
2. Record source date, language, currency, payment method, buyer type, purchasing-power proxy, and relevant regulation or platform restrictions.
3. Compare search/traffic geography, marketplace buyer locations, competitor pricing, checkout availability, and user language. Mark estimated or unknown fields.
4. Identify one primary market and one fallback market only when the evidence supports the distinction.
5. Hand localization, price, and payment assumptions to validation for a country-specific offer or checkout test.

## Output

```yaml
persona_and_job: ""
market_comparison: [{market: "", language: "", currency: "", payment: "", buyer: "", purchasing_power: "", evidence_ids: []}]
localization_needs: []
regulatory_or_platform_risks: []
primary_market: ""
fallback_market: ""
price_test: ""
unknowns: []
```
