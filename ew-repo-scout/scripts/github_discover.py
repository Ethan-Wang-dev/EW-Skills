#!/usr/bin/env python3
"""Bounded GitHub discovery. Scores aid retrieval, never assert product similarity."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.github.com"
ACCEPT = "application/vnd.github+json"
TEXT_ACCEPT = "application/vnd.github.text-match+json"
STOP = {"the", "and", "for", "with", "from", "that", "this", "open", "source",
        "tool", "tools", "app", "application", "project", "using", "based", "into", "or"}
FIELDS = ("id", "full_name", "name", "html_url", "description", "topics", "language",
          "homepage", "default_branch", "created_at", "pushed_at", "updated_at",
          "archived", "disabled", "fork", "stargazers_count", "forks_count",
          "open_issues_count", "license", "mirror_url", "private", "visibility")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def terms(text):
    text = re.sub(r"topic:([\w-]+)", r"\1", text or "")
    text = re.sub(r'\b[\w-]+:(?:"[^"]*"|\S+)', " ", text)
    tokens = re.findall(r"[a-z0-9][a-z0-9+#.-]*|[\u3400-\u9fff]+", text.lower())
    result = set()
    for token in tokens:
        if re.fullmatch(r"[\u3400-\u9fff]+", token):
            result.update(token[i:i + 2] for i in range(max(1, len(token) - 1)))
        elif len(token) > 1 and token not in STOP:
            result.add(token)
    return result


def repo_name(value):
    value = re.sub(r"^https://(?:api\.)?github\.com/(?:repos/)?", "", value or "")
    value = value.rstrip("/")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", value):
        raise ValueError("Expected owner/repo or a canonical GitHub repository URL")
    return value


def unique(values):
    return list(dict.fromkeys(values))


def compact_repo(data):
    result = {key: data[key] for key in FIELDS if key in data}
    for relation in ("parent", "source"):
        if isinstance(data.get(relation), dict):
            result[relation] = {k: data[relation].get(k) for k in ("id", "full_name", "html_url")}
    return result


class GitHub:
    """Record errors/cache age; bound calls; stop a rate-limited bucket without sleeping."""
    def __init__(self, token=None, cache_dir=None, max_requests=60, refresh=False):
        self.token = token
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.max_requests = max_requests
        self.refresh = refresh
        self.events = []
        self.requests = 0
        self.cache_hits = 0
        self.blocked = set()
        self.lock = threading.Lock()
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, url, accept=ACCEPT):
        if not url.startswith(API + "/"):
            raise ValueError("This client only requests api.github.com")
        bucket = "code_search" if "/search/code?" in url else "search" if "/search/" in url else "core"
        # Separate authenticated cache scopes without writing credentials to disk.
        scope = hashlib.sha256((self.token or "public").encode()).hexdigest()
        key = hashlib.sha256((url + accept + scope).encode()).hexdigest()
        path = self.cache_dir / (key + ".json") if self.cache_dir else None
        ttl = 900 if bucket != "core" else 3600
        if path and not self.refresh:
            try:
                saved = json.loads(path.read_text())
                if time.time() - saved["saved_at"] < ttl:
                    result = dict(saved["response"], from_cache=True)
                    with self.lock:
                        self.cache_hits += 1
                    return result
            except (OSError, ValueError, KeyError, TypeError):
                pass
        with self.lock:
            skipped = "rate_limited" if bucket in self.blocked else "budget_exhausted" if self.requests >= self.max_requests else None
            if skipped is None:
                self.requests += 1
        result = {"url": url, "status": skipped or "ok", "http_status": None,
                  "fetched_at": utc_now(), "from_cache": False, "rate_limit": {}}
        if skipped:
            result["message"] = "No request sent; narrow queries or retry with available quota."
            self._record(result)
            return result
        headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28",
                   "User-Agent": "ew-repo-scout"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        try:
            with urlopen(Request(url, headers=headers), timeout=20) as response:
                result["http_status"] = response.status
                result["rate_limit"] = self._rate(response.headers)
                result["data"] = json.loads(response.read())
        except HTTPError as exc:
            result["http_status"] = exc.code
            result["rate_limit"] = self._rate(exc.headers)
            try:
                message = json.loads(exc.read()).get("message", str(exc))
            except (ValueError, AttributeError):
                message = str(exc)
            limited = exc.code == 429 or (exc.code == 403 and (
                result["rate_limit"].get("remaining") == "0" or "rate limit" in message.lower()))
            result["status"] = "rate_limited" if limited else "not_found" if exc.code == 404 else "error"
            result["message"] = str(message)[:300]
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            result.update(status="error", message=str(exc)[:300])
        if result["status"] == "rate_limited" or result["rate_limit"].get("remaining") == "0":
            with self.lock:
                self.blocked.add(bucket)
        self._record(result)
        if path and result["status"] in ("ok", "not_found"):
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    json.dump({"saved_at": time.time(), "response": result}, stream, ensure_ascii=False)
                os.replace(temporary, path)
            except OSError:
                if temporary:
                    temporary.unlink(missing_ok=True)
        return result

    @staticmethod
    def _rate(headers):
        return {key: headers.get("X-RateLimit-" + header) for key, header in (
            ("remaining", "Remaining"), ("limit", "Limit"), ("reset", "Reset"), ("resource", "Resource"))
            if headers.get("X-RateLimit-" + header) is not None}

    def _record(self, response):
        event = {key: value for key, value in response.items() if key != "data"}
        with self.lock:
            self.events.append(event)


def search_endpoint(client, query, source, limit):
    report = {"source": source, "query": query, "status": "ok", "total_count": None,
              "incomplete_results": False, "fetched_count": 0, "pages": [], "limited": False}
    if source == "code" and not client.token:
        report.update(status="skipped_auth", message="GitHub Code Search requires authentication; no request sent.")
        return [], report
    endpoint = "repositories" if source == "repo" else source
    # Public repositories are the discovery scope even when authenticated.
    effective = query if source == "code" else query + " is:public"
    report["effective_query"] = effective
    per_page = min(limit, 100)
    hits = []
    for page in range(1, (limit + per_page - 1) // per_page + 1):
        url = API + "/search/" + endpoint + "?" + urlencode(
            {"q": effective, "per_page": per_page, "page": page})
        response = client.get(url, TEXT_ACCEPT)
        report["pages"].append({key: value for key, value in response.items() if key != "data"})
        if response["status"] != "ok":
            report.update(status="partial" if hits else response["status"],
                          message=response.get("message"))
            break
        data = response.get("data", {})
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            report.update(status="error", message="Unexpected GitHub search response")
            break
        report["total_count"] = data.get("total_count")
        report["incomplete_results"] |= bool(data.get("incomplete_results"))
        for offset, item in enumerate(data["items"]):
            metadata = item if source == "repo" else (item.get("repository") or {})
            if metadata.get("private") or metadata.get("visibility") == "internal":
                continue
            name = metadata.get("full_name")
            if not name:
                try:
                    name = repo_name(item.get("repository_url", ""))
                except ValueError:
                    continue
            fragments = [m.get("fragment", "") for m in (item.get("text_matches") or [])]
            excerpt = "\n".join(fragments) or item.get("body") or ""
            hits.append({"full_name": name, "metadata": compact_repo(metadata), "source": source,
                         "query": query, "rank": (page - 1) * per_page + offset + 1,
                         "url": item.get("html_url"), "title": item.get("title") or item.get("name"),
                         "path": item.get("path"), "excerpt": excerpt[:1200],
                         "kind": "pull_request" if item.get("pull_request") else "issue" if source == "issues" else source,
                         "fetched_at": response.get("fetched_at")})
            if len(hits) >= limit:
                break
        if len(hits) >= limit or len(data["items"]) < per_page:
            break
    report["fetched_count"] = len(hits)
    report["limited"] = (report["total_count"] or 0) > len(hits)
    if report["incomplete_results"] and report["status"] == "ok":
        report["status"] = "partial"
    return hits, report


def merge_candidates(candidates):
    merged, names, ids = [], {}, {}
    for incoming in candidates:
        key = incoming["full_name"].lower()
        target = ids.get(incoming.get("id")) if incoming.get("id") is not None else None
        if target is None:
            target = names.get(key)
        if target is None:
            target = dict(incoming)
            target.setdefault("aliases", [])
            target.setdefault("evidence_hits", [])
            merged.append(target)
        else:
            metadata_available = "available" in (target.get("metadata_state"), incoming.get("metadata_state"))
            aliases = unique(target.get("aliases", []) + incoming.get("aliases", []) +
                             ([target["full_name"]] if target["full_name"] != incoming["full_name"] else []))
            evidence = target.get("evidence_hits", []) + incoming.get("evidence_hits", [])
            target.update({k: v for k, v in incoming.items() if k not in ("evidence_hits", "aliases")})
            target.update(aliases=aliases, evidence_hits=evidence)
            if metadata_available:
                target["metadata_state"] = "available"
        names[key] = target
        if target.get("id") is not None:
            ids[target["id"]] = target
        seen, evidence = set(), []
        for hit in target["evidence_hits"]:
            signature = (hit["source"], hit["query"], hit.get("url"), hit.get("path"))
            if signature not in seen:
                evidence.append(hit)
                seen.add(signature)
        target["evidence_hits"] = evidence
        target["sources"] = sorted({hit["source"] for hit in evidence})
        target["matched_queries"] = sorted({hit["query"] for hit in evidence if hit["query"]})
    return merged


def merge_hits(hits):
    candidates = []
    for hit in hits:
        item = dict(hit.get("metadata") or {})
        item.setdefault("full_name", hit["full_name"])
        item.setdefault("name", item["full_name"].split("/")[-1])
        item.setdefault("html_url", "https://github.com/" + item["full_name"])
        item["evidence_hits"] = [{k: v for k, v in hit.items() if k not in ("metadata", "full_name")}]
        item["metadata_state"] = "available" if hit["source"] in ("repo", "seed") else "unverified"
        candidates.append(item)
    return merge_candidates(candidates)


def lexical_score(item, idea, queries):
    pools = [terms(q) for q in [idea, *queries] if terms(q)]
    def overlap(text):
        text_terms = terms(text)
        return max((len(pool & text_terms) / len(pool) for pool in pools), default=0.0)
    description = " ".join([item.get("description") or "", " ".join(item.get("topics") or [])])
    lexical = 0.15 * overlap(item.get("name") or "") + 0.55 * overlap(description)
    lexical += 0.20 * overlap(item.get("readme_excerpt") or "")
    ranks = {}
    for hit in item.get("evidence_hits", []):
        if hit.get("rank"):
            key = (hit["source"], hit["query"])
            ranks[key] = min(ranks.get(key, 10**6), hit["rank"])
    # Reciprocal rank fusion retains candidates discovered through different phrasing.
    fusion = min(1.0, sum(1 / (60 + rank) for rank in ranks.values()) / (1 / 61))
    return round(lexical + 0.10 * fusion, 6), {"lexical_overlap": round(lexical, 6),
                                              "rank_fusion": round(fusion, 6)}


def rank_candidates(candidates, idea, queries):
    for item in candidates:
        item["retrieval_score"], item["retrieval_score_components"] = lexical_score(item, idea, queries)
    return sorted(candidates, key=lambda item: (-item["retrieval_score"], item["full_name"].lower()))


def select_deep(candidates, limit):
    """Allocate part of a small budget to query/source diversity, without stars."""
    selected = list(candidates[:max(1, limit // 2)]) if limit else []
    lanes = sorted({(h["source"], h["query"]) for c in candidates for h in c.get("evidence_hits", [])})
    for lane in lanes:
        if len(selected) >= limit:
            break
        if any(any((h["source"], h["query"]) == lane for h in c.get("evidence_hits", [])) for c in selected):
            continue
        match = next((c for c in candidates if any(
            (h["source"], h["query"]) == lane for h in c.get("evidence_hits", []))), None)
        if match is not None and match not in selected:
            selected.append(match)
    for item in candidates:
        if len(selected) >= limit:
            break
        if item not in selected:
            selected.append(item)
    return selected


def provenance(response):
    return {k: response.get(k) for k in ("status", "url", "http_status", "fetched_at", "from_cache", "message")
            if k in response}


def decode_content(data):
    if data.get("encoding") != "base64" or not data.get("content"):
        return ""
    try:
        return base64.b64decode(data["content"]).decode("utf-8", "replace")
    except (ValueError, TypeError):
        return ""


def readme_excerpt(text, query_terms, budget=6000):
    lines = text.splitlines()
    chosen = set(range(min(24, len(lines))))
    windows = sorted(range(len(lines)), key=lambda i: (-len(terms(lines[i]) & query_terms), i))
    remaining = budget - sum(len(lines[i]) + 12 for i in chosen)
    for i in windows:
        if not (terms(lines[i]) & query_terms):
            break
        new = set(range(max(0, i - 1), min(len(lines), i + 3))) - chosen
        cost = sum(len(lines[j]) + 12 for j in new)
        if cost <= remaining:
            chosen.update(new)
            remaining -= cost
    excerpt = "\n".join(f"L{i + 1}: {lines[i]}" for i in sorted(chosen))[:budget]
    return excerpt, len(chosen) < len(lines) or len(text) > budget


def enrich(client, item, query_terms, no_readme=False, activity=False):
    base = API + "/repos/" + item["full_name"]
    item["enrichment_attempted"] = True
    if not no_readme:
        response = client.get(base + "/readme")
        evidence = provenance(response)
        if response["status"] == "ok":
            data = response.get("data") or {}
            text = decode_content(data)
            excerpt, truncated = readme_excerpt(text, query_terms)
            item["readme_excerpt"] = excerpt
            evidence.update(path=data.get("path"), html_url=data.get("html_url"),
                            blob_sha=data.get("sha"), excerpted=truncated)
            if not text:
                evidence["status"] = "unavailable_content"
            related = unique(re.findall(r"https://github\.com/([\w.-]+/[\w.-]+)", text))
            item["related_repositories"] = [name.rstrip(".") for name in related
                                            if name.lower() != item["full_name"].lower()][:20]
        item["readme_evidence"] = evidence
    for endpoint, key in (("releases/latest", "release_evidence"), ("license", "license_evidence")):
        response = client.get(base + "/" + endpoint)
        evidence = provenance(response)
        if response["status"] == "ok":
            data = response.get("data") or {}
            if endpoint == "license":
                evidence.update(spdx_id=(data.get("license") or {}).get("spdx_id"),
                                html_url=data.get("html_url"), path=data.get("path"),
                                excerpt=decode_content(data)[:1200])
            else:
                item["latest_release"] = {k: data.get(k) for k in ("tag_name", "published_at", "html_url")}
                evidence.update(item["latest_release"])
        item[key] = evidence
    if activity:
        for endpoint, key in (("commits?per_page=5", "recent_commits"),
                              ("issues?state=all&sort=updated&per_page=5", "recent_issues")):
            response = client.get(base + "/" + endpoint)
            evidence = provenance(response)
            if response["status"] == "ok":
                evidence["items"] = []
                for entry in response.get("data") or []:
                    if key == "recent_commits":
                        evidence["items"].append({"sha": entry.get("sha"), "url": entry.get("html_url"),
                            "date": ((entry.get("commit") or {}).get("committer") or {}).get("date"),
                            "message": ((entry.get("commit") or {}).get("message") or "")[:250]})
                    else:
                        evidence["items"].append({k: entry.get(k) for k in
                            ("html_url", "title", "state", "created_at", "updated_at", "comments", "pull_request")})
            item[key] = evidence
    return item


def health_signals(item):
    return {"archived": item.get("archived"), "last_push": item.get("pushed_at"),
            "stars": item.get("stargazers_count"), "forks": item.get("forks_count"),
            "license_spdx": (item.get("license") or {}).get("spdx_id"),
            "is_fork": item.get("fork"), "fork_parent": item.get("parent"),
            "fork_source": item.get("source"), "mirror_url": item.get("mirror_url")}


def execute(args, client):
    started, start_clock = utc_now(), time.monotonic()
    jobs = [(source, query, args.limit if source == "repo" else args.secondary_limit)
            for source in unique(args.sources.split(",")) for query in unique(args.query)]
    jobs += [("code", q, args.secondary_limit) for q in args.code_query]
    jobs += [("issues", q, args.secondary_limit) for q in args.issue_query]
    jobs += [("repo", "topic:" + q, args.limit) for q in args.topic]
    jobs = unique(jobs)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        searches = list(pool.map(lambda job: search_endpoint(client, job[1], job[0], job[2]), jobs))
    hits = [hit for batch, _ in searches for hit in batch]
    reports = [report for _, report in searches]
    seed_reports = []
    for name in unique(args.seed_repo):
        response = client.get(API + "/repos/" + name)
        seed_reports.append(provenance(response))
        data = response.get("data") or {}
        if response["status"] == "ok" and data.get("full_name") and not data.get("private"):
            hits.append({"full_name": name, "metadata": compact_repo(data), "source": "seed",
                         "query": "", "rank": None, "url": data.get("html_url")})
    candidates = merge_hits(hits)
    queries = unique([q for _, q, _ in jobs])
    candidates = rank_candidates(candidates, args.idea, queries)
    # Bound metadata hydration, preserving unverified candidates in output.
    hydrate = [c for c in candidates if c.get("metadata_state") != "available"][:args.metadata_limit]
    hydrate += [c for c in candidates[:args.deep_limit] if c.get("fork") and c not in hydrate]
    def metadata(item):
        response = client.get(API + "/repos/" + item["full_name"])
        item["metadata_evidence"] = provenance(response)
        data = response.get("data") or {}
        if response["status"] == "ok" and data.get("full_name"):
            previous = item["full_name"]
            item.update(compact_repo(data))
            item["metadata_state"] = "available"
            if previous != item["full_name"]:
                item.setdefault("aliases", []).append(previous)
        return item
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(metadata, hydrate))
    candidates = merge_candidates([c for c in candidates if not c.get("private") and c.get("visibility") != "internal"])
    candidates = rank_candidates(candidates, args.idea, queries)
    deep = select_deep(candidates, args.deep_limit)
    query_terms = terms(" ".join([args.idea, *queries]))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda c: enrich(client, c, query_terms, args.no_readme, args.activity), deep))
    candidates = rank_candidates(candidates, args.idea, queries)
    for candidate in candidates:
        candidate["health_signals"] = health_signals(candidate)
    failed = [r for r in reports if r["status"] != "ok"]
    errors = [e for e in client.events if e["status"] not in ("ok", "not_found")]
    usable = any(r["status"] in ("ok", "partial") for r in reports) or any(
        r["status"] == "ok" for r in seed_reports)
    status = "failed" if not usable else "partial" if failed or errors else "ok"
    result = {"schema_version": 2, "idea": args.idea, "queries": queries, "count": len(candidates),
              "search_metadata": {
                  "status": status, "started_at": started, "finished_at": utc_now(),
                  "elapsed_seconds": round(time.monotonic() - start_clock, 3),
                  "authenticated": bool(client.token), "sources": unique([j[0] for j in jobs]),
                  "query_runs": reports, "seed_runs": seed_reports, "seed_repositories": args.seed_repo,
                  "raw_hit_count": len(hits), "deduplicated_count": len(candidates),
                  "deep_attempted_count": len(deep),
                  "readme_verified_count": sum(c.get("readme_evidence", {}).get("status") == "ok" for c in candidates),
                  "network_requests": client.requests, "cache_hits": client.cache_hits,
                  "request_budget": client.max_requests,
                  "rate_limit_samples": [e for e in client.events if e.get("rate_limit")],
                  "errors": errors,
                  "limitations": [
                      "Scores are lexical/rank-fusion retrieval aids, not product-similarity probabilities.",
                      "Search results are capped and not exhaustive; query_runs record omissions/errors.",
                      "Issue/PR hits may describe requests or bugs, not implemented capabilities.",
                      "Different forks/mirrors are retained; only repository ID/name aliases are merged.",
                      "README excerpts and code-search fragments do not replace targeted implementation review."]},
              "repositories": candidates}
    return result


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--idea", default="")
    p.add_argument("--query", action="append", default=[], help="Repository query; repeatable")
    p.add_argument("--sources", default="repo", help="Search lanes to run: repo, code and/or issues")
    p.add_argument("--code-query", action="append", default=[], help="Targeted code query; requires token")
    p.add_argument("--issue-query", action="append", default=[], help="Issue/PR query (use is:issue to exclude PRs)")
    p.add_argument("--topic", action="append", default=[], help="Repository topic, e.g. web-clipper")
    p.add_argument("--seed-repo", action="append", default=[], help="Known owner/repo to verify; repeatable")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--secondary-limit", type=int, default=8)
    p.add_argument("--deep-limit", type=int, default=8)
    p.add_argument("--metadata-limit", type=int, default=20)
    p.add_argument("--max-requests", type=int, default=60)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--cache-dir", default=".github-oss-cache")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--refresh", action="store_true", help="Bypass cache for current verification")
    p.add_argument("--no-readme", action="store_true", help="Skip README only; release/license still verified")
    p.add_argument("--activity", action="store_true", help="Fetch recent commits and issue/PR samples for deep candidates")
    p.add_argument("--output", help="Write JSON to a file; otherwise stdout")
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    args.sources = ",".join(s.strip() for s in args.sources.split(",") if s.strip())
    if not args.sources or set(args.sources.split(",")) - {"repo", "code", "issues"}:
        p.error("--sources must contain repo, code and/or issues")
    if any(not q.strip() for q in args.query + args.code_query + args.issue_query):
        p.error("queries cannot be empty")
    if not any((args.query, args.code_query, args.issue_query, args.topic, args.seed_repo)):
        p.error("supply a query, topic or seed repository")
    if not (1 <= args.limit <= 1000 and 1 <= args.secondary_limit <= 1000):
        p.error("result limits must be between 1 and 1000")
    if args.deep_limit < 0 or args.metadata_limit < 0 or args.max_requests < 1 or not 1 <= args.workers <= 8:
        p.error("invalid depth, metadata, request or worker limit")
    try:
        args.seed_repo = [repo_name(name) for name in args.seed_repo]
    except ValueError as exc:
        p.error(str(exc))
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", t) for t in args.topic):
        p.error("topics must be lowercase GitHub topic slugs")
    client = GitHub(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
                    None if args.no_cache else Path(args.cache_dir),
                    args.max_requests, args.refresh)
    result = execute(args, client)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
        print(json.dumps({"output": str(path), "status": result["search_metadata"]["status"],
                          "count": result["count"]}))
    else:
        try:
            sys.stdout.write(rendered)
        except BrokenPipeError:
            return 0
    return 1 if result["search_metadata"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
