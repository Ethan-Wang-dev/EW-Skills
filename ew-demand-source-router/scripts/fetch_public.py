#!/usr/bin/env python3
"""Fetch one public HTTP page and save an auditable AdapterRun.

This helper intentionally handles only one public URL per invocation. It does
not authenticate, execute JavaScript, bypass robots rules, solve CAPTCHAs, or
retry aggressively. Use browser automation or a user export when a public
HTTP response cannot answer the evidence gap.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


USER_AGENT = "EW-Demand-Source-Router/1.0 (+public-research; contact user)"
DEFAULT_MAX_BYTES = 2_000_000


class VisibleTextParser(HTMLParser):
    """Small dependency-free extractor for readable text, not a site crawler."""

    SKIP = {"script", "style", "noscript", "svg", "template"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            value = re.sub(r"\s+", " ", data).strip()
            if value:
                self.parts.append(value)

    def text(self) -> str:
        return "\n".join(self.parts)


def validate_url(value: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("url: only an absolute http(s) URL is allowed")
    if parsed.username or parsed.password:
        raise ValueError("url: credentials in URLs are not allowed")
    return parsed


def robots_state(parsed: urllib.parse.ParseResult, timeout: float) -> tuple[str, bool]:
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(256_000).decode("utf-8", errors="replace")
        parser.parse(content.splitlines())
        allowed = parser.can_fetch(USER_AGENT, parsed.geturl())
        return ("allowed" if allowed else "disallowed", allowed)
    except (OSError, urllib.error.URLError, ValueError):
        return "unavailable", True


def fetch(url: str, output_dir: Path, *, max_bytes: int, timeout: float, query_or_filters: str, source_type: str) -> dict[str, Any]:
    parsed = validate_url(url)
    output_dir.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat()
    run: dict[str, Any] = {
        "id": f"A-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "source_url": url,
        "source_name": parsed.hostname,
        "source_type": source_type,
        "adapter": "http",
        "query_or_filters": query_or_filters,
        "captured_at": captured_at,
        "access_state": "public",
        "batch_limit": "one URL",
        "budget_limit": "no paid API credits",
        "coverage_limit": f"response body capped at {max_bytes} bytes; no JavaScript rendering or pagination",
        "fallback_used": "",
        "raw_observation_ids": [],
        "robots": "unknown",
    }
    robots, allowed = robots_state(parsed, timeout)
    run["robots"] = robots
    if not allowed:
        run["access_state"] = "blocked"
        run["error"] = "robots.txt disallows this URL for the EW user agent"
        (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise PermissionError(run["error"])

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            content_type = response.headers.get_content_type()
            declared_length = response.headers.get("Content-Length")
            if declared_length and declared_length.isdigit() and int(declared_length) > max_bytes:
                run.update({"access_state": "partial", "http_status": status, "content_type": content_type, "error": "Content-Length exceeds max_bytes"})
                (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                raise ValueError(run["error"])
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                run.update({"access_state": "partial", "http_status": status, "content_type": content_type, "error": "response exceeded max_bytes"})
                (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                raise ValueError(run["error"])
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        state = "rate_limited" if exc.code in {403, 429} else "blocked" if exc.code in {401, 402, 407} else "partial"
        run.update({"access_state": state, "http_status": exc.code, "error": f"HTTP {exc.code}; use an allowed fallback instead of retrying aggressively"})
        (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    except urllib.error.URLError as exc:
        run.update({"access_state": "partial", "error": str(exc.reason)})
        (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise

    text = body.decode(charset, errors="replace")
    if "html" in content_type:
        parser = VisibleTextParser()
        parser.feed(text)
        visible_text = parser.text()
        (output_dir / "response.html").write_text(text, encoding="utf-8")
        (output_dir / "response.txt").write_text(visible_text + "\n", encoding="utf-8")
    else:
        visible_text = text
        (output_dir / "response.txt").write_text(text, encoding="utf-8")
    run.update({"http_status": status, "content_type": content_type, "bytes": len(body), "text_characters": len(visible_text), "saved_files": ["response.html", "response.txt"] if "html" in content_type else ["response.txt"]})
    (output_dir / "adapter-run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-type", default="search", choices=["community", "search", "marketplace", "review", "competitor", "trend", "internal_kb"])
    parser.add_argument("--query-or-filters", default="")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.max_bytes <= 0 or args.timeout <= 0:
        parser.error("max-bytes and timeout must be positive")
    try:
        run = fetch(args.url, Path(args.output_dir), max_bytes=args.max_bytes, timeout=args.timeout, query_or_filters=args.query_or_filters, source_type=args.source_type)
    except (OSError, PermissionError, ValueError, urllib.error.URLError) as exc:
        parser.error(str(exc))
    print(json.dumps(run, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
