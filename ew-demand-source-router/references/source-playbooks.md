# Source playbooks for overseas-product demand research

These are compact operating recipes. Always follow the adapter ladder and limits in `ew-demand-evidence/references/source-adapters.md`. A playbook defines what a source can help answer; it does not guarantee access or prove the conclusion by itself.

## Search and trend

### Public job APIs (Remotive / Arbeitnow)

- Use these as a stable first pass for role, location, remote eligibility, tags/skills, salary (when present), and publication date.
- Keep the query, snapshot date, returned count, and local sample limit. A listing proves that a role was visible in that snapshot; it does not prove hiring volume, hiring completion, or candidate success.
- For a CV-fit analysis, normalize repeated skills across at least two independent queries or snapshots, then manually inspect the original job description before recommending a gap.

### Google Search

- Use a seed plus intent modifiers: `for`, `alternative`, `not working`, `bulk`, `API`, `template`, `price`, or a role/scenario.
- Use `site:`, `intitle:`, `allintitle:`, `inurl:`, `after:` and `before:` to bound the corpus or find new pages.
- Record locale, date, result type, and the first useful pages. Search volume is not available from ordinary result pages and should not be invented.

### Google Trends

- Compare a seed with a stable baseline, then record window, country, category, rising queries, and related queries.
- Treat relative interest and a sudden rise as `metric` or `lead`; seek user behavior or transactions next.
- `pytrends` is unofficial and rate-limited. Use browser UI or a user export when it is safer.

### Similarweb / Semrush / Ahrefs

- Use only an authorized account/export when the field is behind a plan.
- Ask one question at a time: country, landing page, keyword, traffic channel, paid keyword, or backlinks.
- Record whether a value is estimated, its date and locale, and never convert traffic to exact revenue.
- If the source is decision-critical, provide a dashboard URL plus `adapter: authenticated_browser` and run with `--allow-authenticated-browser --browser-profile ...` or `--browser-state ...`; otherwise export CSV/JSON/HTML and use `ingest_export.py`.
- Keep the exported query, date range, country and plan/permission scope next to the evidence. Missing columns remain `unknown`.

Suggested export fields when a protected source is decision-critical:

| Source | Keep these fields (if present) | Caution |
| --- | --- | --- |
| Semrush / Ahrefs | keyword, country, volume/clicks, KD, CPC, URL, date range | estimates and plan coverage are bounded; do not fill missing rows |
| Similarweb | domain, visits, country, channel, top page, date/window | traffic is directional and is not revenue |
| Discord | message, channel, author role (not identity), timestamp, thread URL | export only channels the user is allowed to inspect; remove personal data when possible |
| Stripe / Creem | product, amount, currency, status, date, refund flag | use aggregate/redacted exports; never share card or customer secrets |
| TrustMRR | reported MRR/ARR, date, source URL, self-reported label | self-reported numbers remain a lead/metric, not verified payment |
| VirusTotal / Wappalyzer / PubSpy | domain, technology/reputation field, timestamp, public locator | context for risk/competition, not ownership or demand proof |

## User language and requests

### Reddit / X / Discord

- Search a role, problem, workaround, alternative, or competitor rather than a product name alone.
- Capture independent posts, dates, context, and whether the user describes a recent real task.
- For Discord, distinguish public server information from private channels. Do not cold-DM or mass-post.
- For a private but authorized Discord server, use a user-provided browser profile/state or export only the channels the user is permitted to inspect; do not automate invitations, posting, or direct messages.
- Three independent, specific complaints support a repeated-quote signal; they still do not prove payment.

### There's An AI For That Requests / Product Hunt

- Capture request text, date, votes/comments, and any linked product or follow-up behavior.
- Votes and launch popularity are leads. Look for a real task, payment, repeat use, or referral before upgrading strength.

## Transactions, reviews, and monetization

### Fiverr / Upwork

- Search the job/service phrase and record visible task count, price, turnaround, requirements, reviews, and completed orders where shown.
- For validation, publish a transparent service offer or contact a qualified buyer; do not claim the marketplace count equals your demand.

### Trustpilot / Chrome Web Store / App Store

- Select a product with meaningful review volume, then sample recent and repeated low-rating complaints.
- Record exact complaint, product/version/date and whether it is a one-off or systemic.
- Trust signals can support conversion research; a rating alone does not establish causation.

### Toolify / Stripe / Creem / TrustMRR

- Treat rankings, payment-domain referral traffic, self-reported revenue, and public dashboards as directional clues.
- Label self-reported or estimated revenue separately from direct payment. Never infer exact revenue from traffic alone.

## Competitor, channel, and timing

### Ads Transparency / Similarweb channels / backlinks / outbound traffic

- Record competitor, message, country, date, destination page, and visible persistence.
- Use persistent ads, high-quality referral traffic, and outbound links to form a channel hypothesis, then test the channel with a small authorized campaign or outreach.

### Wayback Machine

- Compare dated snapshots, sitemap/page additions, launch cadence, and page changes. Snapshots are incomplete and do not prove why growth happened.

### query.domains / PubSpy / Wappalyzer

- Use domain registration or shared publisher/technology identifiers to generate leads for further review.
- Do not infer ownership, revenue, or intent from a shared identifier alone. Wappalyzer supports feasibility/competitor context, not demand proof.

## Early technical signals

### GitHub / Hugging Face / arXiv

- Record first source, timestamp, release/activity and downstream examples.
- New code, models, or papers are opportunity timing signals. Confirm a user problem, workflow or transaction before treating them as demand.
