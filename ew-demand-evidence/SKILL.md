---
name: ew-demand-evidence
description: "整理出海产品研究中的需求证据，区分事实、推断和待验证线索，并输出可直接进入机会卡片的结构化结果。"
---

# EW Demand Evidence

## Purpose

Use this skill when a user has网页、搜索结果、社区讨论、竞品资料、用户评价、交易页面、自己的知识库或零散笔记，希望判断其中是否存在值得进一步研究的出海产品需求。

This is an evidence-normalization skill. It does not declare an opportunity “validated” merely because traffic, likes, search volume, or an AI summary looks positive. It turns raw material into traceable evidence and makes the next missing proof explicit.

## Scope and boundaries

- Keep the requester, target user, market, problem, and proposed product separate.
- Use public pages or user-supplied material only; do not bypass login, CAPTCHA, paywalls, robots controls, or platform restrictions.
- Do not fabricate metrics, quotes, prices, users, countries, or competitor capabilities.
- If browsing tools are unavailable, work from the material supplied by the user and mark unsupported fields as unknown.
- Discovery evidence is not validation evidence. Payment, repeat use, referral, or a committed real task are stronger than opinions or page views.
- Treat the user's knowledge base as first-party input, not as market proof. Preserve the difference between direct experience, copied source observations, interpretations, and hypotheses.
- Do not turn this skill into a complete competitor report, market-size report, or product recommendation unless the user asks for those next steps.

## Input

Accept one or more of the following:

- a product idea, keyword, audience, or market;
- URLs or exported pages;
- community posts, reviews, ad copy, marketplace listings, or notes;
- an existing research folder, knowledge base, or evidence table.

If the user has not specified the target audience or geography, keep them as unknown and ask only when the ambiguity changes what evidence should be collected. Otherwise proceed and label the assumption.

## Workflow

Before collecting external evidence, read [references/source-adapters.md](references/source-adapters.md). Read the user's supplied knowledge base or research folder first, then use its gaps to choose external sources. Route each source through its least-fragile available adapter, and record the adapter, query/filter state, access state, and coverage limits in the evidence log. Never bypass login, CAPTCHA, paywalls, robots controls, or rate limits.

### 1. Ingest the first-party knowledge base

If a folder, notes export, document, transcript, spreadsheet, or prior evidence table is supplied, inventory it before searching the web. For each item record its path or title, author/owner when known, created or captured date, and whether it is `direct_experience`, `source_observation`, `interpretation`, or `hypothesis`. Convert only checkable observations into evidence records. Keep first-party records separately addressable from external records (for example, `internal_kb` versus `community` or `search`). A first-party note can be strong evidence of the user's context, but it cannot by itself establish market frequency or willingness to pay.

### 2. Write the research brief

Start with one sentence:

> For [target user] in [market], investigate whether [problem] occurs often enough and is valuable enough to support [desired outcome].

Record separately:

- requester and intended end user;
- target country/language/currency, if known;
- trigger situation and desired outcome;
- current alternative or workaround;
- constraints such as budget, time, technical stack, or compliance;
- unknowns and assumptions.

Do not fill unknowns with typical SaaS defaults.

### 3. Classify each source

Assign one primary source type:

| Type | What it can support |
|---|---|
| `internal_kb` | user's direct experience, prior observations, assumptions, evidence gaps |
| `community` | user language, repeated pain, workarounds, objections |
| `search` | existence of search behavior, trend, intent, geography |
| `marketplace` | paid task, price range, delivery expectations |
| `review` | dissatisfaction, missing feature, reliability or pricing gap |
| `competitor` | positioning, workflow, pricing, channel, visible adoption signal |
| `trend` | early signal from a new model, platform, project, or topic |
| `validation` | experiment events such as real tasks, payments, repeat use, and referrals |

One source can produce several records when it contains independent observations, but do not split one sentence into artificial “evidence.”

### 4. Extract atomic observations

For every observation, preserve:

- exact or faithful quote, metric, page title, or visible behavior;
- source URL and capture date;
- market, language, and persona context;
- what the observation supports;
- what it does not prove.

Prefer the smallest statement that can be checked. “Three users independently asked for bulk export in the same community during May” is evidence; “the market needs bulk export” is a conclusion.

### 5. Rate evidence strength

Use one of these labels and explain the choice:

- `direct_payment`: a real payment, order, paid subscription, or completed pre-sale;
- `behavior`: repeat use, return visit, committed task, active workaround, or user referral;
- `repeated_quote`: the same pain independently appears at least three times;
- `metric`: search, traffic, price, rating, member count, or trend metric without a conversion link;
- `inference`: a reasoned interpretation of observed evidence;
- `lead`: an unverified hint worth investigating.

Never upgrade a metric or inference to payment evidence. A competitor's existence indicates possible demand, not your product-market fit.

### 6. Normalize into evidence records

Output one YAML or JSON record per observation:

```yaml
id: E-001
source_url: "https://example.com/..."
source_type: community
captured_at: "YYYY-MM-DD"
market: "US / English"
persona: ""
quote_or_observation: ""
supports: pain|frequency|demand|willingness_to_pay|distribution|competition|risk
evidence_strength: repeated_quote
confidence: 1-5
does_not_prove: ""
notes: ""
source_origin: first_party|external|experiment
source_locator: "file path, note title, or external page section"
source_created_at: "YYYY-MM-DD or unknown"
claim_kind: direct_experience|source_observation|interpretation|hypothesis|external_observation|experiment_observation
conflicts_with: []
collection: first_party|external
adapter: http|api|browser|authenticated_browser|user_export|local_read
query_or_filters: ""
access_state: public|authenticated|blocked|rate_limited|partial|not_applicable
coverage_limit: ""
```

`confidence` measures how faithfully the record represents the source, not how attractive the opportunity is.

### 7. Choose the next evidence source by gap

Do not collect every source category by default. After the first pass, write the missing proof explicitly: frequency, payment, distribution, geography, competitive gap, or delivery risk. Select the cheapest source likely to answer that gap and collect a small batch. Repeat until the opportunity has enough independent support or the lead is stopped. Reuse existing first-party records when they answer a gap; do not duplicate them as external evidence.

When GitHub tools, Skills, or source adapters may help, inspect or invoke them only after the required source types and output fields are known. Tool availability does not determine the research sequence. Record the chosen adapter or reusable component and its license/credit constraints separately from the evidence itself.

### 8. Cluster by user and job

Group records by:

> user + trigger situation + job to be done + desired result

Do not merge records merely because they contain the same tool or keyword. Keep geography, language, willingness to pay, and workflow differences visible. For each cluster, summarize:

- repeated problem statement;
- current workaround;
- frequency and failure cost;
- apparent value (time, labor, money, risk, or revenue);
- strongest evidence and missing evidence.

### 9. Produce an opportunity handoff

For each cluster, output a compact handoff:

```yaml
opportunity_name: ""
persona: ""
scenario: ""
problem: ""
desired_outcome: ""
evidence_ids: []
knowledge_base_evidence_ids: []
external_evidence_ids: []
evidence_summary: ""
payment_signal: "none|weak|possible|direct|unknown"
target_markets: []
likely_channels: []
current_alternatives: []
unanswered_questions: []
next_low_cost_test: ""
status: lead|evidence-backed|ready-for-validation
```

Use `ready-for-validation` only when there is evidence of a recurring problem plus a plausible user/channel; it still does not mean the product is validated.

## Source-specific guidance

- Knowledge base: preserve file/note location and dates; distinguish direct experience from interpretation; treat copied claims as external with their original URL; never silently overwrite conflicting notes or later observations.
- Community: count independent occurrences, capture user wording, and note whether people describe a workaround or ask for an alternative.
- Search: record country, language, trend window, intent modifiers, and a comparison term. Search volume alone is a `metric`.
- Marketplace: capture task count, completed orders where visible, price, turnaround time, and buyer requirements. This is often the clearest pre-product payment signal.
- Reviews: prioritize high-download/high-review-volume products with repeated low ratings; separate a one-off complaint from a systemic gap.
- Competitors: record traffic channels, landing-page promise, pricing, free limits, and visible user journey. Never infer revenue from traffic without a stated assumption.
- Trends: record first source, timestamp, adoption signal, and whether the signal has crossed into user behavior or transactions.

## Quality gate

Before finishing, check:

- every non-trivial claim links to at least one evidence ID;
- important opportunities use at least two independent source types where possible;
- facts, inferences, assumptions, and unknowns are visibly separated;
- target country and purchasing power are not inferred from global traffic;
- no duplicate records inflate frequency;
- every promising cluster has one next test and one unanswered question;
- conflicting first-party and external observations remain visible with scope/date and a follow-up question;
- the handoff does not claim validation without payment, repeat-use, referral, or equivalent behavior evidence.

## Output format

Return, in this order:

1. one-sentence research brief;
2. evidence table with source links/locators, `first_party` versus `external`, claim kind, and strength labels;
3. clustered opportunity handoffs;
4. missing evidence and risks;
5. the lowest-cost next validation test;
6. a short note describing coverage limits and collection date.
