#!/usr/bin/env python3
"""Run a bounded multi-source demand-research batch.

The runner turns source-specific responses into EvidenceRecord-compatible JSONL
and a machine-readable summary. It is deliberately human-in-the-loop at the
authorization boundary: public browser collection is opt-in with
``--allow-browser``; authenticated collection requires an explicit user
profile/state and ``--allow-authenticated-browser``. Manual sources remain
explicit gaps until a user-authorized browser or local export is supplied.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Works both as a sibling script and when imported by tests.
    from fetch_public import robots_state, validate_url
    from ingest_export import build_records
    from source_registry import REGISTRY, SourceSpec, generic_visible_parser, get_source
except ImportError:  # pragma: no cover - package-style import fallback
    from .fetch_public import robots_state, validate_url
    from .ingest_export import build_records
    from .source_registry import REGISTRY, SourceSpec, generic_visible_parser, get_source


DEFAULT_MAX_BYTES = 2_000_000
DEFAULT_TIMEOUT = 20.0
DEFAULT_DELAY = 0.35
DEFAULT_MAX_BROWSER_ACTIONS = 12
MAX_BROWSER_SCROLL_PIXELS = 5000
MAX_REQUEST_BYTES = 20_000_000


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")[:80] or "source"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_input(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("input: expected a JSON object")
    brief = raw.get("brief", raw)
    requests = raw.get("sources", raw.get("source_requests", []))
    if not isinstance(brief, dict):
        raise ValueError("brief: expected an object")
    if not isinstance(requests, list) or not requests:
        raise ValueError("sources: expected a non-empty list")
    if any(not isinstance(item, dict) for item in requests):
        raise ValueError("sources: each item must be an object")
    return brief, requests


def request_url(spec: SourceSpec, item: dict[str, Any]) -> str:
    explicit = item.get("url")
    if isinstance(explicit, str) and explicit.startswith(("http://", "https://")):
        return explicit
    if spec.url_builder is None:
        return ""
    return spec.url_builder(item)


def requested_adapter(spec: SourceSpec, item: dict[str, Any]) -> str:
    """Return the adapter selected for a request, allowing explicit fallbacks.

    Manual registry entries (for example Semrush and Ahrefs) can be collected
    when a user supplies a dashboard URL plus an authorized browser session.
    The override is intentionally narrow; arbitrary transports are rejected.
    """
    override = item.get("adapter")
    if override is None:
        # A manual/authorized registry entry may still point at a public page.
        # Treat an explicit HTTP URL as a public browser request (still opt-in)
        # rather than silently discarding it; query-only requests remain manual.
        if spec.transport == "manual":
            explicit_url = item.get("url")
            return "browser" if isinstance(explicit_url, str) and explicit_url.startswith(("http://", "https://")) else "manual"
        return "browser" if spec.transport == "browser" else "http"
    value = str(override).strip().lower().replace("-", "_")
    allowed = {"http", "api", "browser", "authenticated_browser", "user_export", "manual"}
    if value not in allowed:
        raise ValueError(f"unsupported adapter override: {override}")
    if value in {"http", "api"} and spec.transport in {"browser", "manual"}:
        raise ValueError(f"{spec.name} cannot use {value}; use browser/authenticated_browser or a user export")
    return value


def auth_options(item: dict[str, Any], browser_profile: str | None, browser_state: str | None) -> tuple[str | None, str | None]:
    """Resolve auth paths without ever reading or writing their contents."""
    profile = item.get("browser_profile", browser_profile)
    state = item.get("browser_state", browser_state)
    if profile is not None and not isinstance(profile, str):
        raise ValueError("browser_profile must be a path or profile name")
    if state is not None and not isinstance(state, str):
        raise ValueError("browser_state must be a JSON path")
    if profile and state:
        raise ValueError("provide only one of browser_profile or browser_state per request")
    if profile:
        profile_path = Path(profile).expanduser()
        # A profile name such as `Default` is allowed; paths must exist so a
        # typo cannot silently start an unauthenticated browser.
        if ("/" in profile or "\\" in profile or profile.startswith(".")) and not profile_path.exists():
            raise ValueError("browser profile path does not exist (path is omitted from run output)")
        return profile, None
    if state:
        state_path = Path(state).expanduser()
        if not state_path.is_file():
            raise ValueError("browser state file does not exist (path is omitted from run output)")
        return None, state
    return None, None


def request_max_bytes(item: dict[str, Any], default: int) -> int:
    value = item.get("max_bytes", default)
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_bytes must be an integer") from exc
    if limit <= 0 or limit > MAX_REQUEST_BYTES:
        raise ValueError(f"max_bytes must be between 1 and {MAX_REQUEST_BYTES}")
    return limit


def browser_action_command(action: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Translate one bounded, non-script browser action to CLI arguments.

    JavaScript/eval, uploads, downloads, auth forms, and arbitrary navigation
    are intentionally not accepted.  The summary returned here contains no
    entered text, so query values and filter values do not leak into run logs.
    """
    if not isinstance(action, dict):
        raise ValueError("browser actions must be objects")
    kind = str(action.get("action") or action.get("command") or "").strip().lower()
    if kind == "wait":
        if "ms" in action:
            ms = int(action["ms"])
            if ms < 0 or ms > 30_000:
                raise ValueError("browser wait ms must be between 0 and 30000")
            return ["wait", str(ms)], {"action": "wait", "ms": ms}
        selector = str(action.get("selector") or "").strip()
        if not selector or len(selector) > 300:
            raise ValueError("browser wait requires a selector or bounded ms")
        return ["wait", selector], {"action": "wait", "selector": selector}
    if kind == "scroll":
        direction = str(action.get("direction", "down")).lower()
        if direction not in {"up", "down", "left", "right"}:
            raise ValueError("scroll direction must be up/down/left/right")
        pixels = int(action.get("pixels", 800))
        if pixels < 0 or pixels > MAX_BROWSER_SCROLL_PIXELS:
            raise ValueError(f"scroll pixels must be between 0 and {MAX_BROWSER_SCROLL_PIXELS}")
        return ["scroll", direction, str(pixels)], {"action": "scroll", "direction": direction, "pixels": pixels}
    if kind in {"click", "fill", "select"}:
        selector = str(action.get("selector") or "").strip()
        if not selector or len(selector) > 300:
            raise ValueError(f"{kind} requires a bounded selector")
        lowered = selector.lower()
        risky_terms = ("password", "passwd", "token", "secret", "credit", "checkout", "purchase", "buy", "order", "confirm", "delete", "unsubscribe", "logout", "signout", "sign-out", "sign in", "sign-in", "signin", "subscribe", "add to cart", "send", "post", "follow", "like")
        if any(term in lowered for term in risky_terms):
            raise ValueError(f"refusing potentially mutating or credential selector: {selector}")
        if kind == "click":
            return ["click", selector], {"action": "click", "selector": selector}
        value = action.get("text") if kind == "fill" else action.get("value")
        if not isinstance(value, str) or not value:
            raise ValueError(f"{kind} requires non-empty text/value")
        if len(value) > 500:
            raise ValueError(f"{kind} value is too long")
        if kind == "fill":
            return ["fill", selector, value], {"action": "fill", "selector": selector, "value_provided": True}
        return ["select", selector, value], {"action": "select", "selector": selector, "value_provided": True}
    if kind == "press":
        key = str(action.get("key") or "").strip()
        if key not in {"Tab", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "PageUp", "PageDown", "Home", "End", "Escape"}:
            raise ValueError("press only permits navigation keys; form submission keys are disabled")
        return ["press", key], {"action": "press", "key": key}
    raise ValueError("unsupported browser action; use wait, scroll, click, fill, select or a navigation key")


def http_fetch(url: str, *, max_bytes: int, timeout: float) -> tuple[str, dict[str, Any], bytes]:
    parsed = validate_url(url)
    robots, allowed = robots_state(parsed, timeout)
    run = {"robots": robots, "adapter": "http", "source_url": url}
    if not allowed:
        run.update({"access_state": "blocked", "error": "robots.txt disallows this URL for the EW user agent"})
        raise PermissionError(run["error"])
    request = urllib.request.Request(url, headers={"User-Agent": "EW-Demand-Source-Router/1.0 (+public-research)", "Accept": "application/json,application/xml,text/html,text/plain;q=0.9,*/*;q=0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        content_type = response.headers.get_content_type()
        declared_length = response.headers.get("Content-Length")
        if declared_length and declared_length.isdigit() and int(declared_length) > max_bytes:
            raise ValueError(f"Content-Length exceeds max_bytes ({max_bytes})")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(f"response exceeded max_bytes ({max_bytes})")
        charset = response.headers.get_content_charset() or "utf-8"
    run.update({"access_state": "public", "http_status": status, "content_type": content_type, "bytes": len(body), "charset": charset})
    return body.decode(charset, errors="replace"), run, body


def browser_fetch(
    url: str,
    *,
    timeout: float,
    session_name: str,
    profile: str | None = None,
    state: str | None = None,
    actions: list[dict[str, Any]] | None = None,
    max_actions: int = DEFAULT_MAX_BROWSER_ACTIONS,
    authenticated: bool = False,
) -> tuple[str, dict[str, Any], bytes]:
    if shutil.which("agent-browser") is None:
        raise FileNotFoundError("agent-browser is not installed; use HTTP/API or provide a user export")
    if max_actions <= 0:
        raise ValueError("max_actions must be positive")
    selected_actions = actions or []
    if len(selected_actions) > max_actions:
        raise ValueError(f"browser action count exceeds max_actions ({max_actions})")
    validate_url(url)
    # --session creates an isolated, non-persistent session.  Auth state is
    # supplied only through the user-selected profile/state and is not copied
    # into a named cookie vault by this runner.
    command = ["agent-browser", "--session", session_name]
    if profile:
        command += ["--profile", profile]
    if state:
        command += ["--state", state]
    opened = subprocess.run(command + ["open", url], capture_output=True, text=True, timeout=timeout, check=False)
    if opened.returncode:
        raise RuntimeError(opened.stderr.strip() or opened.stdout.strip() or "browser open failed")
    applied_actions: list[dict[str, Any]] = []
    try:
        for action in selected_actions:
            args, audit = browser_action_command(action)
            result = subprocess.run(command + args, capture_output=True, text=True, timeout=timeout, check=False)
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"browser action failed: {audit['action']}")
            applied_actions.append(audit)
        # agent-browser requires a selector for get text; body covers the rendered page.
        result = subprocess.run(command + ["get", "text", "body"], capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "browser text extraction failed")
        text = result.stdout
    finally:
        subprocess.run(command + ["close"], capture_output=True, text=True, timeout=min(timeout, 10), check=False)
    lower_text = text.lower()
    auth_challenge = any(marker in lower_text for marker in (
        "verify you are human",
        "captcha",
        "access denied",
        "security verification",
        "protect against malicious bots",
        "ray id:",
        "please log in to continue",
        "please sign in to continue",
        "sign in to view",
        "upgrade your plan to",
    ))
    return text, {
        "adapter": "authenticated_browser" if authenticated else "browser",
        "access_state": "authenticated" if authenticated else "public",
        "browser_session": session_name,
        "auth_source": "user_profile" if profile else "user_state" if state else "none",
        "browser_actions": applied_actions,
        "auth_challenge_detected": auth_challenge,
        "bytes": len(text.encode("utf-8")),
        "text_characters": len(text),
    }, text.encode("utf-8")


def base_run(spec: SourceSpec, item: dict[str, Any], index: int, adapter: str | None = None) -> dict[str, Any]:
    adapter = adapter or requested_adapter(spec, item)
    return {
        "id": f"A-{index:03d}",
        "source_name": spec.name,
        "source_type": spec.source_type,
        "source_url": "",
        "adapter": adapter,
        "query_or_filters": item.get("query") or item.get("url") or "",
        "captured_at": now(),
        "access_state": "partial",
        "batch_limit": str(item.get("limit", "source default")),
        "budget_limit": "runner request/byte budget",
        "coverage_limit": spec.note or "one bounded request; parser coverage is source-specific",
        "fallback_used": "",
        "raw_observation_ids": [],
    }


def evidence_records(observations: list[dict[str, Any]], run: dict[str, Any], brief: dict[str, Any], run_index: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for offset, observation in enumerate(observations, 1):
        quote = observation.get("quote_or_observation")
        if not isinstance(quote, str) or not quote.strip():
            continue
        evidence_id = f"E-{run_index:03d}-{offset:03d}"
        strength = observation.get("evidence_strength", "lead")
        records.append({
            "id": evidence_id,
            "source_url": run.get("source_url", ""),
            "source_type": run.get("source_type", ""),
            "source_origin": "external",
            "source_locator": observation.get("source_locator", run.get("source_url", "")),
            "source_created_at": observation.get("source_created_at", "unknown"),
            "captured_at": run.get("captured_at", now()),
            "market": brief.get("market") or brief.get("target_market") or "unknown",
            "persona": brief.get("target_user") or brief.get("persona") or "unknown",
            "claim_kind": "external_observation",
            "quote_or_observation": quote.strip(),
            "supports": observation.get("supports", "demand"),
            "evidence_strength": strength,
            "metric": observation.get("metric", {}),
            "confidence": 4 if run.get("adapter") in {"http", "browser", "authenticated_browser", "user_export"} and observation.get("metric") is not None else 3,
            "does_not_prove": observation.get("does_not_prove", "单个来源或指标不能单独证明全市场需求、付款或留存。"),
            "conflicts_with": [],
            "adapter": run.get("adapter", "http"),
            "query_or_filters": run.get("query_or_filters", ""),
            "access_state": run.get("access_state", "partial"),
            "coverage_limit": run.get("coverage_limit", ""),
            "notes": observation.get("notes", ""),
        })
        run.setdefault("raw_observation_ids", []).append(evidence_id)
    return records


def run_one(
    spec: SourceSpec,
    item: dict[str, Any],
    index: int,
    brief: dict[str, Any],
    *,
    max_bytes: int,
    timeout: float,
    allow_browser: bool,
    allow_authenticated_browser: bool = False,
    browser_profile: str | None = None,
    browser_state: str | None = None,
    max_browser_actions: int = DEFAULT_MAX_BROWSER_ACTIONS,
    output_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    adapter = requested_adapter(spec, item)
    run = base_run(spec, item, index, adapter=adapter)
    url = request_url(spec, item)
    run["source_url"] = url
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    run_file = output_dir / "adapter-runs" / f"{index:03d}-{slug(spec.name)}.json"
    try:
        effective_max_bytes = request_max_bytes(item, max_bytes)
    except ValueError as exc:
        run.update({"access_state": "partial", "error": str(exc), "fallback_used": "use a positive bounded max_bytes value"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    run["byte_limit"] = effective_max_bytes

    if adapter == "user_export":
        export_path = item.get("path") or item.get("export_path")
        if not isinstance(export_path, str) or not export_path.strip():
            run.update({"access_state": "not_applicable", "fallback_used": "provide path for a local CSV/JSON/HTML export", "coverage_limit": "no export path supplied"})
            run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return run, []
        try:
            export_file = Path(export_path).expanduser()
            export_records, export_run = build_records(
                export_file,
                source_name=spec.name,
                source_type=spec.source_type,
                source_url=url or str(item.get("source_url") or ""),
                market=str(brief.get("market") or brief.get("target_market") or ""),
                persona=str(brief.get("target_user") or brief.get("persona") or ""),
                query_or_filters=str(item.get("query") or item.get("filters") or ""),
                max_records=min(max(int(item.get("limit", 500)), 1), 5000),
                input_format=str(item.get("format", "auto")),
                max_bytes=effective_max_bytes,
            )
            run.update(export_run)
            run["id"] = f"A-{index:03d}"
            run["adapter"] = "user_export"
            run["source_url"] = export_run.get("source_url") or run["source_url"]
            run["access_state"] = "authenticated"
            run["export_file_name"] = export_file.name
            records: list[dict[str, Any]] = []
            for n, record in enumerate(export_records, 1):
                record["id"] = f"E-{index:03d}-{n:03d}"
                record["adapter"] = "user_export"
                if run["source_url"]:
                    record["source_url"] = run["source_url"]
                record["access_state"] = "authenticated"
                records.append(record)
            run["raw_observation_ids"] = [record["id"] for record in records]
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            run.update({"access_state": "partial", "error": str(exc), "fallback_used": "provide a supported local export and verify its encoding/format"})
            records = []
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, records

    if adapter == "manual":
        run.update({"access_state": "not_applicable", "fallback_used": spec.note or "request a user export or authorized evidence", "coverage_limit": spec.note or "manual source"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    if not url:
        run.update({"access_state": "partial", "fallback_used": "provide a public url or a query supported by this source"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []

    is_browser = adapter in {"browser", "authenticated_browser"}
    try:
        profile, state = auth_options(item, browser_profile, browser_state) if is_browser else (None, None)
        is_authenticated = adapter == "authenticated_browser" or bool(profile or state)
    except ValueError as exc:
        run.update({"access_state": "partial", "error": str(exc), "fallback_used": "provide one valid profile/state path or use a user export"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    if adapter == "authenticated_browser" and not (profile or state):
        run.update({"access_state": "partial", "error": "authenticated_browser requires a user browser profile or state file", "fallback_used": "provide --browser-profile/--browser-state or use adapter=user_export"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    if is_authenticated and not allow_authenticated_browser:
        run.update({"access_state": "partial", "fallback_used": "rerun with --allow-authenticated-browser after explicitly providing a user profile/state, or provide a user export", "coverage_limit": "authenticated browser access is opt-in; no request was made"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    if is_browser and not is_authenticated and not allow_browser:
        run.update({"access_state": "partial", "fallback_used": "rerun with --allow-browser for a public browser session, or provide a user export", "coverage_limit": "browser access is opt-in; no request was made"})
        run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return run, []
    try:
        if is_browser:
            actions = item.get("actions", [])
            if actions is None:
                actions = []
            if not isinstance(actions, list):
                raise ValueError("actions must be a list")
            body_text, transport_run, raw = browser_fetch(
                url,
                timeout=timeout,
                session_name=f"ew-source-run-{index:03d}",
                profile=profile,
                state=state,
                actions=actions,
                max_actions=max_browser_actions,
                authenticated=is_authenticated,
            )
            body_for_parser = body_text
            extension = "txt"
        else:
            body_text, transport_run, raw = http_fetch(url, max_bytes=effective_max_bytes, timeout=timeout)
            body_for_parser = body_text
            extension = "json" if spec.transport == "json" else "xml" if spec.transport == "xml" else "html"
        run.update(transport_run)
        if transport_run.get("auth_challenge_detected"):
            run.update({"access_state": "partial", "fallback_used": "browser returned a login/CAPTCHA/paywall challenge; use an authorized session or local export; challenge text was not promoted to evidence"})
            observations = []
        else:
            parser = spec.parser or generic_visible_parser if is_browser else spec.parser
            if parser is None:
                observations = []
            else:
                observations = parser(body_for_parser, url, item)
        raw_path = raw_dir / f"{index:03d}-{slug(spec.name)}.{extension}"
        raw_path.write_bytes(raw)
        run["saved_raw"] = str(raw_path.relative_to(output_dir))
        records = evidence_records(observations, run, brief, index)
    except urllib.error.HTTPError as exc:
        run.update({"http_status": exc.code, "access_state": "rate_limited" if exc.code in {403, 429} else "blocked" if exc.code in {401, 402, 407} else "partial", "error": f"HTTP {exc.code}", "fallback_used": "use browser/user export or wait for the documented limit; do not retry aggressively"})
        records = []
    except (OSError, PermissionError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        run.update({"access_state": "blocked" if isinstance(exc, PermissionError) else "partial", "error": str(exc), "fallback_used": "record the limitation and switch to an allowed adapter"})
        records = []
    run_file.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run, records


def analyze(runs: list[dict[str, Any]], evidence: list[dict[str, Any]], brief: dict[str, Any]) -> dict[str, Any]:
    source_totals: dict[str, int] = {}
    status_totals: dict[str, int] = {}
    supports_totals: dict[str, int] = {}
    strength_totals: dict[str, int] = {}
    for run in runs:
        source_totals[run["source_name"]] = source_totals.get(run["source_name"], 0) + 1
        status = run.get("access_state", "partial")
        status_totals[status] = status_totals.get(status, 0) + 1
    for record in evidence:
        supports = str(record.get("supports", "unknown"))
        strength = str(record.get("evidence_strength", "lead"))
        supports_totals[supports] = supports_totals.get(supports, 0) + 1
        strength_totals[strength] = strength_totals.get(strength, 0) + 1
    gap_kinds = set(brief.get("evidence_gaps", [])) if isinstance(brief.get("evidence_gaps", []), list) else set()
    if not (set(strength_totals) & {"direct_payment", "behavior"}):
        gap_kinds.add("value_or_payment")
    if not (set(strength_totals) & {"repeated_quote", "behavior"}):
        gap_kinds.add("frequency")
    if not any(record.get("supports") == "competition" for record in evidence):
        gap_kinds.add("competition")
    if not any(record.get("source_type") == "community" for record in evidence):
        gap_kinds.add("distribution")
    return {
        "status": "evidence-backed" if set(strength_totals) & {"direct_payment", "behavior"} else "lead",
        "brief": brief,
        "source_totals": source_totals,
        "access_status_totals": status_totals,
        "supports_totals": supports_totals,
        "evidence_strength_totals": strength_totals,
        "evidence_count": len(evidence),
        "open_gaps": sorted(gap_kinds),
        "strongest_evidence": sorted(strength_totals, key=lambda name: {"direct_payment": 5, "behavior": 4, "repeated_quote": 3, "metric": 2, "inference": 1, "lead": 0}.get(name, -1), reverse=True)[:3],
        "limitations": [run.get("error") or run.get("fallback_used") for run in runs if run.get("access_state") not in {"public", "authenticated"}],
    }


def render_summary(analysis: dict[str, Any], runs: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> str:
    lines = ["# Automated source research run", "", f"Status: **{analysis['status']}**", f"Evidence records: **{analysis['evidence_count']}**", "", "## Access summary", ""]
    for name, count in sorted(analysis["source_totals"].items()):
        status = next((run.get("access_state") for run in runs if run["source_name"] == name), "unknown")
        lines.append(f"- `{name}`: {count} run(s), access `{status}`")
    lines += ["", "## Evidence summary", ""]
    if evidence:
        for record in evidence[:30]:
            lines.append(f"- `{record['id']}` [{record['evidence_strength']}] {record['quote_or_observation'][:240]} ({record['source_locator']})")
    else:
        lines.append("- No observations were extracted; inspect adapter-run limitations before drawing a conclusion.")
    lines += ["", "## Open gaps", ""]
    lines.extend(f"- `{gap}`" for gap in analysis["open_gaps"])
    lines += ["", "## Limits", "", "- This is bounded collection and deterministic aggregation, not proof of product-market fit.", "- Inspect each AdapterRun and source page before using an observation in a recommendation."]
    for limitation in analysis["limitations"]:
        if limitation:
            lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def run_batch(
    brief: dict[str, Any],
    requests: list[dict[str, Any]],
    output_dir: Path,
    *,
    max_requests: int,
    max_bytes: int,
    timeout: float,
    delay: float,
    allow_browser: bool,
    allow_authenticated_browser: bool = False,
    browser_profile: str | None = None,
    browser_state: str | None = None,
    max_browser_actions: int = DEFAULT_MAX_BROWSER_ACTIONS,
    force: bool = False,
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        if not force:
            raise ValueError(f"output directory is not empty: {output_dir} (use --force to replace generated files)")
        for child in output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "adapter-runs").mkdir(exist_ok=True)
    runs: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    selected = requests[:max_requests]
    for index, item in enumerate(selected, 1):
        source_name = item.get("source") or item.get("source_name")
        if not isinstance(source_name, str) or not source_name.strip():
            raise ValueError(f"sources[{index - 1}].source: required")
        spec = get_source(source_name)
        run, records = run_one(
            spec,
            item,
            index,
            brief,
            max_bytes=max_bytes,
            timeout=timeout,
            allow_browser=allow_browser,
            allow_authenticated_browser=allow_authenticated_browser,
            browser_profile=browser_profile,
            browser_state=browser_state,
            max_browser_actions=max_browser_actions,
            output_dir=output_dir,
        )
        runs.append(run)
        evidence.extend(records)
        if delay and index < len(selected):
            time.sleep(delay)
    deferred = max(0, len(requests) - len(selected))
    analysis = analyze(runs, evidence, brief)
    analysis["deferred_source_requests"] = deferred
    (output_dir / "evidence.jsonl").write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in evidence), encoding="utf-8")
    (output_dir / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(render_summary(analysis, runs, evidence), encoding="utf-8")
    result = {"generated_at": now(), "brief": brief, "runs": runs, "evidence": evidence, "analysis": analysis}
    (output_dir / "research-run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON with brief and sources list")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-requests", type=int, default=10)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--allow-browser", action="store_true", help="Allow public agent-browser sessions for browser sources")
    parser.add_argument("--allow-authenticated-browser", action="store_true", help="Allow a user-provided browser profile/state for authorized research")
    parser.add_argument("--browser-profile", help="Chrome profile name or existing directory; never copied to output")
    parser.add_argument("--browser-state", help="Existing agent-browser auth state JSON; never copied to output")
    parser.add_argument("--max-browser-actions", type=int, default=DEFAULT_MAX_BROWSER_ACTIONS, help="Maximum read-only browser actions per source request")
    parser.add_argument("--force", action="store_true", help="Replace an existing non-empty generated directory")
    args = parser.parse_args()
    if args.max_requests <= 0 or args.max_bytes <= 0 or args.timeout <= 0 or args.delay < 0 or args.max_browser_actions <= 0:
        parser.error("max-requests, max-bytes, timeout, max-browser-actions must be positive and delay cannot be negative")
    if args.browser_profile and args.browser_state:
        parser.error("use only one of --browser-profile or --browser-state")
    try:
        brief, requests = load_input(Path(args.input))
        result = run_batch(
            brief,
            requests,
            Path(args.output_dir),
            max_requests=args.max_requests,
            max_bytes=args.max_bytes,
            timeout=args.timeout,
            delay=args.delay,
            allow_browser=args.allow_browser,
            allow_authenticated_browser=args.allow_authenticated_browser,
            browser_profile=args.browser_profile,
            browser_state=args.browser_state,
            max_browser_actions=args.max_browser_actions,
            force=args.force,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output_dir": args.output_dir, "runs": len(result["runs"]), "evidence": len(result["evidence"]), "status": result["analysis"]["status"], "open_gaps": result["analysis"]["open_gaps"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
