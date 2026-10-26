---
name: ew-demand-source-router
description: "根据需求证据缺口选择专业网站、访问方式和最小采集批次，并把访问限制记录下来。"
---

# EW Demand Source Router

## Purpose

Use this skill after a `ResearchBrief` and `EvidenceGap[]` exist. It chooses the cheapest allowed source and adapter that can answer the current gap. It does not crawl every website by default and does not treat tool availability as evidence.

Read [references/source-playbooks.md](references/source-playbooks.md) for source-specific methods when a listed site is selected. Read the existing evidence adapter rules in [../ew-demand-evidence/references/source-adapters.md](../ew-demand-evidence/references/source-adapters.md) for the access ladder and failure handling.

For a single public HTML/JSON/text page, the repository includes [scripts/fetch_public.py](scripts/fetch_public.py):

```bash
python3 <skill-dir>/scripts/fetch_public.py \
  --url "https://example.com/public-page" \
  --source-type search \
  --query-or-filters "country=US; window=30d" \
  --output-dir ./adapter-runs/example-001
```

It saves a capped response and `adapter-run.json`, checks `robots.txt`, and never logs credentials. It intentionally does not render JavaScript, paginate, authenticate, or retry a blocked/rate-limited site; switch to an allowed browser session or user export and keep the limitation in the run record.

For JavaScript-only public pages, use an available browser automation capability (for example `$browser-automation`) only for the defined page/filter batch, and record the snapshot date, actions, and coverage in the same `AdapterRun`. The HTTP adapter enforces `robots.txt`; browser automation is separately opt-in, low-rate, and must follow the site's terms (do not use it to evade a login, CAPTCHA, paywall, or an explicit prohibition on automated access). A browser tool is a transport, not evidence by itself.

For an automatic bounded batch across the registered sources, use [scripts/run_sources.py](scripts/run_sources.py). It invokes the source registry, writes one `AdapterRun` per request, converts parsed observations to `evidence.jsonl`, and produces `analysis.json`/`summary.md` with access status and open evidence gaps:

```json
{
  "brief": {"target_user": "indie developers", "market": "US", "evidence_gaps": ["frequency", "value_or_payment"]},
  "sources": [
    {"source": "reddit", "query": "manual feedback workflow", "limit": 10},
    {"source": "github", "query": "feedback collection", "limit": 10},
    {"source": "app_store", "query": "feedback tracker", "limit": 10},
    {"source": "semrush", "query": "feedback workflow"}
  ]
}
```

```bash
python3 <skill-dir>/scripts/run_sources.py \
  --input research-run.json \
  --output-dir ./research-runs/2026-09-13-feedback \
  --max-requests 4
```

Add `--allow-browser` only when public dynamic pages are required. The registry currently has direct public adapters for Remotive and Arbeitnow job JSON, Reddit JSON, GitHub API, Hugging Face API, Apple Search API, arXiv Atom, and Wayback CDX; Google Search and other listed pages have bounded HTML/browser adapters where public access permits. Similarweb, Semrush, Ahrefs, Discord, Stripe, Creem, TrustMRR, VirusTotal, PubSpy, and Wappalyzer remain explicit gaps for query-only requests, while an explicit public URL can opt into a bounded browser request and an authorized profile/state or export can supply protected fields.

### Important sources that need an account or export

Do not stop at an empty manual result when a source is important to the decision. There are two supported, auditable fallbacks:

1. **User-authorized browser session.** The user supplies an existing Chrome profile directory or an `agent-browser` state JSON, and explicitly opts in:

```bash
python3 <skill-dir>/scripts/run_sources.py \
  --input research-run.json \
  --output-dir ./research-runs/semrush \
  --allow-authenticated-browser \
  --browser-profile "/path/to/user/profile"
```

Use a request with an explicit dashboard URL and (at most) a small list of bounded filter/navigation actions. Manual registry sources can opt into this path with `"adapter": "authenticated_browser"`:

```json
{"source":"semrush","adapter":"authenticated_browser","url":"https://www.semrush.com/analytics/keywordoverview/?q=example.com","actions":[{"action":"wait","ms":1500},{"action":"scroll","direction":"down","pixels":800}]}
```

The runner uses an isolated session, does not receive a password, and does not copy the profile/state or entered values into output. Actions are bounded and exclude `eval`, uploads, downloads, credential selectors, and form-submission keys. If the rendered page contains a strong login/CAPTCHA/paywall challenge, its text is not promoted to evidence. A user must already be authorized; the challenge remains a recorded limitation.

Supported action objects are `{"action":"wait","ms":...}` (or a selector), `scroll` with a bounded direction/pixel count, `click`, `fill`, `select`, and non-submitting navigation keys (`Tab`, arrows, `PageUp/Down`, `Home`, `End`, `Escape`). Keep actions to filters and pagination needed for the stated gap; the runner rejects credential or clearly mutating selectors and does not accept arbitrary JavaScript.

2. **User export ingestion.** When browser access is unavailable or a paid plan is required, export CSV/JSON/JSONL/HTML from the source and let the runner normalize it:

```bash
python3 <skill-dir>/scripts/ingest_export.py \
  --input ./exports/semrush-keywords.csv \
  --output-dir ./research-runs/semrush-export \
  --source semrush --source-type search --market US \
  --query-or-filters "keyword=feedback;country=US;window=30d"
```

The same path can be embedded in a multi-source batch with `"adapter":"user_export","path":"..."`; its records are merged into `evidence.jsonl` and its access state is `authenticated` (user-provided export). The export file is read locally, hashed for traceability, and never copied to the generated run directory. Missing fields stay `unknown`; an export sample does not prove market-wide frequency or payment.

## Workflow

1. State one gap to answer and the decision it affects.
2. Choose one primary source and, only when useful, one independent cross-check. Prefer first-party or public structured data over fragile extraction.
3. Choose the least-fragile adapter: public HTTP/API → public browser → user-authorized browser/API → user export/manual evidence. For a high-priority gap, prefer an authorized browser or export fallback over silently dropping a source.
4. Define a small batch: query, filters, date range, page/scroll limit, fields, budget/credit limit, and stop condition.
5. Invoke an available browser/API/tool only within authorization and platform rules. Never bypass login, CAPTCHA, paywalls, or rate limits; the HTTP adapter must not bypass robots controls, and browser use remains subject to the site's terms even when explicitly enabled.
6. Return raw observations plus `AdapterRun`; pass them to `ew-demand-evidence` for normalization.
7. If blocked or rate-limited, record that state and switch to the documented fallback. A failed collection is not evidence of absence.

## Output

```yaml
gap: frequency|value_or_payment|distribution|geography|competition|delivery|trend
source: ""
source_type: community|search|marketplace|review|competitor|trend|internal_kb
adapter: http|api|browser|authenticated_browser|user_export|manual|local_read
query_or_filters: ""
captured_at: "YYYY-MM-DDTHH:MM:SSZ"
access_state: public|authenticated|partial|blocked|rate_limited|not_applicable
coverage_limit: ""
budget_limit: ""
stop_condition: ""
raw_observations: []
next_gap: ""
```

## Safety and quality

- Keep the research question ahead of the website name.
- Do not use a search result count, community size, traffic estimate, or ad presence as payment proof.
- Do not spend paid API credits until the gap and required fields are explicit.
- Keep source date, locale, query, filters, and coverage limits attached to every run.
