#!/usr/bin/env python3
"""Convert an allowed user export into auditable EvidenceRecord JSONL.

This helper deliberately reads local files only.  It does not log in to a
source, upload data, or attempt to reconstruct fields that are not present in
the export.  CSV, JSON and HTML exports are supported because these are the
formats commonly offered by authenticated research tools.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


TEXT_FIELDS = (
    "quote_or_observation",
    "quote",
    "observation",
    "text",
    "comment",
    "review",
    "body",
    "content",
    "request",
    "message",
    "description",
    "title",
    "name",
    "keyword",
    "query",
)
LOCATOR_FIELDS = ("source_locator", "url", "link", "permalink", "source_url", "id")
DATE_FIELDS = ("source_created_at", "created_at", "created", "date", "timestamp", "published_at", "updated_at")
NON_METRIC_FIELDS = set(TEXT_FIELDS + LOCATOR_FIELDS + DATE_FIELDS + ("supports", "evidence_strength", "notes"))
DEFAULT_MAX_BYTES = 20_000_000


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"\s+", " ", str(value)).strip()


def _first(row: dict[str, Any], names: Iterable[str]) -> str:
    lowered = {str(key).lower().strip(): value for key, value in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return ""


def _rows_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item if isinstance(item, dict) else {"text": item} for item in value]
    if isinstance(value, dict):
        for key in ("items", "results", "data", "rows", "records", "reviews", "keywords", "requests"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item if isinstance(item, dict) else {"text": item} for item in nested]
        return [value]
    return [{"text": value}]


class ExportHTMLParser(HTMLParser):
    """Collect readable blocks from a saved HTML export without executing it."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._buffer: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self._skip_depth += 1
        if tag.lower() in {"p", "li", "tr", "article", "section", "h1", "h2", "h3", "div"} and self._buffer:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"} and self._skip_depth:
            self._skip_depth -= 1
        if tag.lower() in {"p", "li", "tr", "article", "section", "h1", "h2", "h3", "div"}:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            value = _clean(html.unescape(data))
            if value:
                self._buffer.append(value)

    def _flush(self) -> None:
        value = _clean(" ".join(self._buffer))
        self._buffer.clear()
        if value and (not self.blocks or self.blocks[-1] != value):
            self.blocks.append(value)

    def finish(self) -> list[str]:
        self._flush()
        return self.blocks


def load_rows(path: Path, *, input_format: str = "auto", max_bytes: int = DEFAULT_MAX_BYTES) -> tuple[list[dict[str, Any]], str]:
    if not path.is_file():
        raise FileNotFoundError(f"export file does not exist: {path}")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"export exceeds max_bytes ({max_bytes})")
    suffix = path.suffix.lower().lstrip(".")
    fmt = suffix if input_format == "auto" else input_format.lower()
    if input_format == "auto" and fmt not in {"json", "jsonl", "ndjson", "csv", "html", "htm"}:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:200].lstrip()
        if sample.startswith(("{", "[")):
            fmt = "json"
        elif sample.startswith("<"):
            fmt = "html"
        else:
            fmt = "csv"
    if fmt in {"json", "jsonl", "ndjson"}:
        if fmt == "jsonl":
            rows = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.extend(_rows_from_json(json.loads(line)))
        else:
            rows = _rows_from_json(json.loads(path.read_text(encoding="utf-8")))
        return rows, "json"
    if fmt == "csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)], "csv"
    if fmt in {"html", "htm"}:
        parser = ExportHTMLParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        return [{"text": block} for block in parser.finish()], "html"
    raise ValueError("unsupported export format; use CSV, JSON, JSONL or HTML")


def default_supports(source_type: str) -> str:
    return {
        "community": "pain",
        "review": "pain",
        "marketplace": "willingness_to_pay",
        "competitor": "competition",
        "trend": "trend",
        "search": "demand",
    }.get(source_type, "demand")


def row_to_evidence(
    row: dict[str, Any],
    *,
    index: int,
    source_name: str,
    source_type: str,
    source_url: str,
    market: str,
    persona: str,
    query_or_filters: str,
    captured_at: str,
    max_quote_chars: int = 3000,
) -> dict[str, Any] | None:
    quote = _first(row, TEXT_FIELDS)
    if not quote:
        # Preserve a non-empty row as an observation instead of silently
        # treating a missing text field as proof that the export is empty.
        compact = {key: value for key, value in row.items() if _clean(value)}
        quote = _clean(compact)
    if not quote:
        return None
    locator = _first(row, LOCATOR_FIELDS) or source_url or f"{source_name} export row {index}"
    created = _first(row, DATE_FIELDS) or "unknown"
    supports = _first(row, ("supports",)) or default_supports(source_type)
    strength = _first(row, ("evidence_strength",)) or "lead"
    metric: dict[str, Any] = {}
    for key, value in row.items():
        if str(key).lower().strip() in NON_METRIC_FIELDS:
            continue
        if _clean(value):
            metric[str(key)] = value
    # A supplied quantitative column is a metric signal, not payment proof.
    # Keep an explicitly provided strength unchanged so users can downgrade
    # noisy exports or preserve a stronger, separately audited label.
    if not _first(row, ("evidence_strength",)) and metric:
        strength = "metric"
    record: dict[str, Any] = {
        "id": f"E-EXP-{index:04d}",
        "source_url": source_url or _first(row, ("source_url", "url")),
        "source_type": source_type,
        "source_origin": "external",
        "source_locator": locator,
        "source_created_at": created,
        "captured_at": captured_at,
        "market": market or "unknown",
        "persona": persona or "unknown",
        "claim_kind": "external_observation",
        "quote_or_observation": quote[:max_quote_chars],
        "supports": supports,
        "evidence_strength": strength,
        "confidence": 3,
        "does_not_prove": "用户导出是有限时间、账户权限和筛选条件下的样本；不能单独证明全市场需求、付款或留存。",
        "conflicts_with": [],
        "adapter": "user_export",
        "query_or_filters": query_or_filters,
        "access_state": "authenticated",
        "coverage_limit": "仅覆盖用户导出的记录、字段、日期范围和账户权限；未导出的字段写 unknown。",
        "notes": f"local {source_name} export; no credentials or raw file contents copied to the adapter run",
    }
    if metric:
        record["metric"] = metric
    return record


def build_records(
    path: Path,
    *,
    source_name: str,
    source_type: str = "search",
    source_url: str = "",
    market: str = "",
    persona: str = "",
    query_or_filters: str = "",
    max_records: int = 500,
    input_format: str = "auto",
    max_bytes: int = DEFAULT_MAX_BYTES,
    captured_at: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, detected_format = load_rows(path, input_format=input_format, max_bytes=max_bytes)
    captured = captured_at or now()
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows[:max_records], 1):
        record = row_to_evidence(
            row,
            index=index,
            source_name=source_name,
            source_type=source_type,
            source_url=source_url,
            market=market,
            persona=persona,
            query_or_filters=query_or_filters,
            captured_at=captured,
        )
        if record:
            records.append(record)
    run = {
        "id": "A-EXP-001",
        "source_name": source_name,
        "source_type": source_type,
        "source_url": source_url,
        "adapter": "user_export",
        "query_or_filters": query_or_filters,
        "captured_at": captured,
        "access_state": "authenticated",
        "batch_limit": max_records,
        "coverage_limit": f"{detected_format} export; {len(rows)} rows read, capped at {max_records} and {max_bytes} bytes; empty/missing fields are not inferred",
        "fallback_used": "",
        "raw_observation_ids": [record["id"] for record in records],
        "input_format": detected_format,
        "input_file_name": path.name,
        "input_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return records, run


def write_output(records: list[dict[str, Any]], run: dict[str, Any], output_dir: Path, *, force: bool = False) -> None:
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
    (output_dir / "evidence.jsonl").write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    (output_dir / "adapter-runs" / "001-user-export.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    analysis = {
        "status": "lead",
        "evidence_count": len(records),
        "source_totals": {run["source_name"]: 1},
        "access_status_totals": {"authenticated": 1},
        "evidence_strength_totals": {},
        "open_gaps": ["value_or_payment", "frequency"],
        "limitations": [run["coverage_limit"]],
    }
    for record in records:
        strength = record["evidence_strength"]
        analysis["evidence_strength_totals"][strength] = analysis["evidence_strength_totals"].get(strength, 0) + 1
    (output_dir / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(
        "# User export ingestion\n\n"
        f"- Source: `{run['source_name']}`\n- Format: `{run['input_format']}`\n"
        f"- Evidence records: **{len(records)}**\n- Access: `authenticated` (user-provided export)\n\n"
        "The export is a bounded sample. It does not by itself prove market-wide frequency, payment, or retention.\n",
        encoding="utf-8",
    )
    (output_dir / "export-run.json").write_text(json.dumps({"run": run, "evidence": records, "analysis": analysis}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="local CSV/JSON/JSONL/HTML export")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source", required=True, dest="source_name")
    parser.add_argument("--source-type", default="search")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--market", default="")
    parser.add_argument("--persona", default="")
    parser.add_argument("--query-or-filters", default="")
    parser.add_argument("--format", default="auto", choices=["auto", "csv", "json", "jsonl", "html"])
    parser.add_argument("--max-records", type=int, default=500)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.max_records <= 0 or args.max_bytes <= 0:
        parser.error("max-records and max-bytes must be positive")
    try:
        records, run = build_records(Path(args.input), source_name=args.source_name, source_type=args.source_type, source_url=args.source_url, market=args.market, persona=args.persona, query_or_filters=args.query_or_filters, max_records=args.max_records, input_format=args.format, max_bytes=args.max_bytes)
        write_output(records, run, Path(args.output_dir), force=args.force)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"output_dir": args.output_dir, "evidence": len(records), "source": args.source_name}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
