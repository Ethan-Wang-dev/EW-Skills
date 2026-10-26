# Demand research source adapters

This reference defines how the skill should attempt to collect evidence from the sites commonly used in overseas-product research. It is a routing guide, not permission to bypass access controls or a guarantee that a site exposes every field.

## Adapter ladder

Use the least fragile adapter that can answer the question:

1. Public HTTP/API: use an official public API or a normal HTTP request for stable, public data.
2. Browser: use `agent-browser open`, `snapshot`, `click`, `scroll`, and `get text` when pagination, filters, lazy loading, or a public interactive view is required.
3. Authenticated browser/API: only when the user has an account and explicitly provides or completes authentication. Never request or store credentials in output.
4. Manual/user-supplied evidence: if the source is blocked, private, rate-limited, or requires a paid plan, ask the user to provide an export or screenshot and mark the limitation.

For a bounded one-page public fetch, `ew-demand-source-router/scripts/fetch_public.py` provides a dependency-free HTTP adapter with a byte cap, timeout, robots check, visible-text extraction, and an auditable `AdapterRun`. It is not a crawler and does not replace browser automation for JavaScript-only pages.

For a bounded multi-source run, `ew-demand-source-router/scripts/run_sources.py` uses the explicit `source_registry.py` catalog. It applies request/byte limits, stores one run record per source, emits `evidence.jsonl`, and reports manual/authenticated sources as coverage gaps instead of returning an empty success until an authorized session or export is supplied. If a high-priority source has an authorized user session, pass `--allow-authenticated-browser` with `--browser-profile` or `--browser-state`; the session is isolated and credentials are never requested or written to output. If the source is behind a plan or a browser flow is unsuitable, use `scripts/ingest_export.py` for a local CSV/JSON/JSONL/HTML export (or a request with `adapter: user_export`).

Always save the source URL, capture date, adapter used, and any query/filter state. A failed adapter is not evidence that the source contains no data.

For authenticated browser runs, the adapter record may include `auth_source: user_profile|user_state` and a redacted `browser_actions` audit list (action names/selectors only). It must not include passwords, cookies, state contents, profile paths, or entered values.

## Source matrix

| Source | Primary question | Preferred adapter | Fallback / limits |
|---|---|---|---|
| User knowledge base / research folder | what the requester has directly observed, assumed, or already collected | local filesystem read, supported document parser, or user export | record path/title and dates; copied claims need original URL; private material stays in scope and is not uploaded or treated as market-wide proof |
| Google Search | what pages and competitors exist for a query | browser or public HTTP | respect regional results; record query and date |
| Remotive / Arbeitnow | current remote or international job listings, locations, tags, salary where shown | public JSON API | bounded snapshot; listing presence is not hiring volume or success |
| Google Trends | trend, related queries, rising terms, countries | browser UI; `pytrends` only for low-rate experiments | `pytrends` is unofficial and rate-limited; DataForSEO requires credentials |
| Similarweb | traffic channels, countries, landing pages, competitors | authenticated browser or official export/API | use `--browser-profile`/`--browser-state` or export; plan/login limits; traffic is not revenue |
| Semrush / Ahrefs | keywords, KD, backlinks, pages | authenticated browser or official export/API | use a user-authorized dashboard URL or export; do not infer missing metrics; free views are partial |
| Reddit | repeated pain, workarounds, objections | public HTTP or browser for pagination | no private communities or login bypass; capture post URL and date |
| X / Twitter | early signals, user language, competitor posts | public HTTP or browser on public status/profile | login/rate limits; do not infer engagement beyond visible data |
| Discord | complaints, requests, member growth, feedback | browser on public web invite/server or user-authorized browser/export | private servers require user access; do not cold-DM or mass-post |
| Fiverr / Upwork | paid tasks, price, requirements, turnaround | public HTTP or browser filters | completed-order data may be hidden; capture visible counts only |
| Trustpilot | repeated complaints, trust signals, competitor gaps | public HTTP or browser | rating is not causation; distinguish one-off from repeated issue |
| Chrome Web Store / App Store | download/ratings/review pain | public HTTP or browser listing | review pagination and locale affect coverage |
| There's An AI For That Requests | explicit tool requests and votes | public HTTP or browser filters | vote count is a lead, not payment evidence |
| Product Hunt | launches, comments, early adoption signals | public HTTP or browser | popularity does not prove retention or revenue |
| Toolify / traffic.cv | rankings, growth, related tools | public pages or official endpoint where exposed | rankings are directional; record date and category |
| Google Ads Transparency | persistent competitor ads and messaging | browser search/filter | regional and account visibility varies; ad presence is not ROI proof |
| query.domains / searchsuggest.tips | domain and autocomplete expansion | normal HTTP or browser | treat results as leads; check trademark and domain history |
| PubSpy / Wappalyzer | related sites and technology stack | browser extension or public page | only use on public sites; do not claim ownership from shared IDs alone |
| Wayback Machine | site history, launch rhythm, page changes | browser public snapshots or HTTP | snapshots are incomplete and time-zone sensitive |
| VirusTotal | domain reputation/history | public page, authorized browser/API, or user-provided export | API may require a key; never upload private artifacts without consent |
| GitHub | open-source projects, issues, releases, activity | GitHub public API or browser | API rate limits; license must be verified, not inferred from public code |
| Hugging Face / arXiv | early model/project signals | public HTTP/API or browser | early signal ≠ user demand; seek downstream behavior |
| Stripe / Creem / TrustMRR | public payment or revenue clues | public pages/traffic analysis | never convert traffic into exact revenue without explicit assumptions |

## Adapter record

For every collection run, append this metadata to the evidence log:

```yaml
source_url: ""
adapter: http|api|browser|authenticated_browser|user_export|manual|local_read
query_or_filters: ""
captured_at: "YYYY-MM-DDTHH:MM:SSZ"
access_state: public|authenticated|blocked|rate_limited|partial|not_applicable
coverage_limit: ""
```

## Failure handling

- `403`, CAPTCHA, login wall, or paywall: stop escalating; use an allowed browser session or request an export.
- JavaScript-only or empty HTML: retry with browser automation; do not repeatedly hammer the site.
- Pagination/infinite scroll: record how many pages or scroll batches were collected and stop at a stated limit.
- Rate limit: back off, record the status, and switch to a lower-rate or user-supplied path.
- Conflicting values: preserve both observations with dates; do not average them silently.
- Missing field: write `unknown`, not zero.
