---
name: ew-demand-marketplace
description: "从 Fiverr、Upwork 等服务市场判断真实任务、价格、交付要求，并设计服务先行验证。"
---

# EW Demand Marketplace

## Workflow

1. Convert the opportunity into a result-based service phrase, not an implementation phrase.
2. Search Fiverr, Upwork, or another authorized marketplace and record visible listings/tasks, price, delivery time, buyer requirements, reviews, and completed orders where shown.
3. Separate listing volume from actual orders and self-reported claims.
4. Identify a narrow service offer that can be delivered manually or semi-manually.
5. For validation, prepare a transparent service listing or personalized offer with one price and ask for a real task; record acceptance, payment, revisions, delivery time, and repeat request.

## Output

```yaml
marketplace: ""
search_phrase: ""
visible_demand: ""
price_range: ""
turnaround: ""
buyer_requirements: []
service_offer: ""
evidence_ids: []
validation_mode: concierge_service|marketplace_offer
limits: []
```

## Guardrails

- A marketplace count is not your demand and a listing is not a completed sale.
- Do not misrepresent automation or AI output; promise the result and disclose material limitations.
- Respect marketplace rules and do not spam buyers.
