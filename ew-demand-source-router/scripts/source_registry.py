"""Registry and parsers for the public sources used by EW demand research.

The registry is intentionally explicit. A source can be ``json``, ``xml``,
``html``, ``browser`` or ``manual``; unsupported/authenticated sources are
reported as coverage gaps rather than silently treated as empty data.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Callable


Observation = dict[str, Any]
Parser = Callable[[str, str, dict[str, Any]], list[Observation]]


@dataclass(frozen=True)
class SourceSpec:
    name: str
    source_type: str
    transport: str
    supports: tuple[str, ...]
    url_builder: Callable[[dict[str, Any]], str] | None = None
    parser: Parser | None = None
    note: str = ""


def query_value(request: dict[str, Any]) -> str:
    query = request.get("query") or request.get("url") or ""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("source request requires a non-empty query or url")
    return query.strip()


def qurl(base: str, request: dict[str, Any], *, parameter: str = "q") -> str:
    query = query_value(request)
    params = {parameter: query}
    if request.get("limit") is not None:
        params["limit"] = str(request["limit"])
    return base + "?" + urllib.parse.urlencode(params)


def google_search_url(request: dict[str, Any]) -> str:
    query = query_value(request)
    limit = min(max(int(request.get("limit", 10)), 1), 10)
    locale = request.get("locale") or "en"
    return "https://www.google.com/search?" + urllib.parse.urlencode({"q": query, "num": limit, "hl": locale})


def google_trends_url(request: dict[str, Any]) -> str:
    params = {"q": query_value(request)}
    if request.get("geo"):
        params["geo"] = str(request["geo"])
    return "https://trends.google.com/trends/explore?" + urllib.parse.urlencode(params)


def reddit_url(request: dict[str, Any]) -> str:
    params = {"q": query_value(request), "limit": min(max(int(request.get("limit", 25)), 1), 100), "sort": request.get("sort", "relevance"), "raw_json": "1"}
    if request.get("subreddit"):
        params["restrict_sr"] = "on"
        params["q"] = f"{params['q']} subreddit:{request['subreddit']}"
    return "https://www.reddit.com/search.json?" + urllib.parse.urlencode(params)


def github_url(request: dict[str, Any]) -> str:
    params = {"q": query_value(request), "per_page": min(max(int(request.get("limit", 30)), 1), 100), "sort": request.get("sort", "stars"), "order": "desc"}
    return "https://api.github.com/search/repositories?" + urllib.parse.urlencode(params)


def huggingface_url(request: dict[str, Any]) -> str:
    params = {"search": query_value(request), "limit": min(max(int(request.get("limit", 20)), 1), 100), "full": "true"}
    return "https://huggingface.co/api/models?" + urllib.parse.urlencode(params)


def arxiv_url(request: dict[str, Any]) -> str:
    params = {"search_query": f"all:{query_value(request)}", "start": "0", "max_results": min(max(int(request.get("limit", 10)), 1), 50), "sortBy": "submittedDate", "sortOrder": "descending"}
    return "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)


def app_store_url(request: dict[str, Any]) -> str:
    params = {"term": query_value(request), "entity": "software", "limit": min(max(int(request.get("limit", 50)), 1), 200), "country": request.get("country", "us")}
    return "https://itunes.apple.com/search?" + urllib.parse.urlencode(params)


def remotive_url(request: dict[str, Any]) -> str:
    params = {"search": query_value(request)}
    if request.get("category"):
        params["category"] = str(request["category"])
    if request.get("limit") is not None:
        params["limit"] = str(min(max(int(request["limit"]), 1), 100))
    return "https://remotive.com/api/remote-jobs?" + urllib.parse.urlencode(params)


def arbeitnow_url(request: dict[str, Any]) -> str:
    # The public endpoint returns a bounded page; query filtering is applied
    # locally by arbeitnow_parser because the API does not reliably filter all
    # deployments on a query parameter.
    return "https://www.arbeitnow.com/api/job-board-api"


def wayback_url(request: dict[str, Any]) -> str:
    target = query_value(request)
    if not urllib.parse.urlparse(target).scheme:
        target = "*" + target + "*"
    params = {"url": target, "output": "json", "filter": "statuscode:200", "fl": "timestamp,original,statuscode", "collapse": "urlkey", "limit": min(max(int(request.get("limit", 50)), 1), 1000)}
    return "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params)


def html_search_url(base: str, request: dict[str, Any]) -> str:
    return qurl(base, request)


def chrome_store_url(request: dict[str, Any]) -> str:
    return "https://chromewebstore.google.com/search/" + urllib.parse.quote(query_value(request))


def upwork_url(request: dict[str, Any]) -> str:
    return "https://www.upwork.com/nx/search/jobs/?" + urllib.parse.urlencode({"q": query_value(request)})


def fiverr_url(request: dict[str, Any]) -> str:
    return "https://www.fiverr.com/search/gigs?" + urllib.parse.urlencode({"query": query_value(request)})


def trustpilot_url(request: dict[str, Any]) -> str:
    return "https://www.trustpilot.com/search?" + urllib.parse.urlencode({"query": query_value(request)})


def product_hunt_url(request: dict[str, Any]) -> str:
    return "https://www.producthunt.com/search?" + urllib.parse.urlencode({"q": query_value(request)})


def toolify_url(request: dict[str, Any]) -> str:
    return "https://www.toolify.ai/search?" + urllib.parse.urlencode({"query": query_value(request)})


def traffic_cv_url(request: dict[str, Any]) -> str:
    return "https://traffic.cv/search?" + urllib.parse.urlencode({"q": query_value(request)})


def searchsuggest_url(request: dict[str, Any]) -> str:
    return "https://searchsuggest.tips/?" + urllib.parse.urlencode({"q": query_value(request)})


def ads_transparency_url(request: dict[str, Any]) -> str:
    return "https://adstransparency.google.com/?" + urllib.parse.urlencode({"query": query_value(request)})


def similarweb_url(request: dict[str, Any]) -> str:
    domain = query_value(request).replace("https://", "").replace("http://", "").split("/", 1)[0]
    return f"https://www.similarweb.com/website/{urllib.parse.quote(domain)}/"


def generic_visible_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.I | re.S)
    title = html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else ""
    clean = re.sub(r"<(script|style|noscript|svg|template)\b[^>]*>.*?</\1>", " ", body, flags=re.I | re.S)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = html.unescape(re.sub(r"\s+", " ", clean)).strip()
    if not clean and not title:
        return []
    excerpt = clean[:1000] or title
    return [{"quote_or_observation": f"{title}: {excerpt}" if title else excerpt, "supports": "demand", "evidence_strength": "lead", "notes": "generic visible-text extraction; inspect the page before treating fields as structured"}]


def google_search_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    observations: list[Observation] = []
    # Google markup changes frequently; retain title/link/snippet candidates without claiming complete coverage.
    for match in re.finditer(r'<a[^>]+href="(/url\?q=|)(https?://[^"&]+)[^>]*>(.*?)</a>', body, flags=re.I | re.S):
        link = html.unescape(match.group(2))
        title = re.sub(r"<[^>]+>", " ", match.group(3))
        title = html.unescape(re.sub(r"\s+", " ", title)).strip()
        if title and not link.startswith("https://www.google."):
            observations.append({"quote_or_observation": title, "source_locator": link, "supports": "demand", "evidence_strength": "lead", "notes": "search result title; result set is locale- and time-dependent"})
    return observations[: min(max(int(request.get("limit", 10)), 1), 10)]


def reddit_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    observations: list[Observation] = []
    for child in data.get("data", {}).get("children", []):
        item = child.get("data", {})
        title = str(item.get("title", "")).strip()
        selftext = str(item.get("selftext", "")).strip()
        if not title and not selftext:
            continue
        permalink = item.get("permalink", "")
        observations.append({"quote_or_observation": (title + (" — " + selftext if selftext else ""))[:2000], "source_locator": "https://www.reddit.com" + permalink if permalink.startswith("/") else permalink, "supports": "pain", "evidence_strength": "lead", "metric": {"score": item.get("score"), "comments": item.get("num_comments")}, "notes": "public Reddit JSON result; one post is not proof of frequency or payment"})
    return observations


def github_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    return [{"quote_or_observation": f"{item.get('full_name', '')}: {item.get('description') or 'no description'}", "source_locator": item.get("html_url", ""), "supports": "competition", "evidence_strength": "metric", "metric": {"stars": item.get("stargazers_count"), "forks": item.get("forks_count"), "updated_at": item.get("updated_at")}, "notes": "GitHub repository metadata; stars/forks do not prove users or demand"} for item in data.get("items", [])]


def huggingface_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    return [{"quote_or_observation": f"{item.get('id', '')}: model/project signal", "source_locator": "https://huggingface.co/" + str(item.get("id", "")), "supports": "trend", "evidence_strength": "metric", "metric": {"downloads": item.get("downloads"), "likes": item.get("likes"), "last_modified": item.get("lastModified")}, "notes": "Hugging Face metadata; model popularity is an early signal, not user demand"} for item in data if item.get("id")]


def app_store_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    return [{"quote_or_observation": f"{item.get('trackName', '')}: {item.get('description', '')[:500]}", "source_locator": item.get("trackViewUrl", ""), "supports": "competition", "evidence_strength": "metric", "metric": {"rating": item.get("averageUserRating"), "rating_count": item.get("userRatingCount"), "price": item.get("price")}, "notes": "Apple Search API listing metadata; rating is not causation or payment proof"} for item in data.get("results", [])]


def _visible_job_description(value: Any, limit: int = 900) -> str:
    clean = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>", " ", str(value or ""), flags=re.I | re.S)
    clean = re.sub(r"<[^>]+>", " ", clean)
    return html.unescape(re.sub(r"\s+", " ", clean)).strip()[:limit]


def _job_observation(item: dict[str, Any], *, source: str) -> Observation:
    title = str(item.get("title") or "").strip()
    company = str(item.get("company_name") or item.get("company") or "").strip()
    location = item.get("candidate_required_location") or item.get("location") or "unknown"
    tags = item.get("tags") or []
    if not isinstance(tags, list):
        tags = [tags]
    created = item.get("publication_date") or item.get("created_at") or "unknown"
    if isinstance(created, (int, float)):
        created = datetime.fromtimestamp(created, tz=timezone.utc).date().isoformat()
    description = _visible_job_description(item.get("description"))
    quote = f"{title} — {company}; location: {location}; skills/tags: {', '.join(str(tag) for tag in tags[:30])}"
    if description:
        quote += f". {description}"
    metric = {
        "company": company,
        "location": location,
        "remote": item.get("remote") if "remote" in item else str(location).lower() in {"worldwide", "anywhere", "remote"},
        "job_type": item.get("job_type") or item.get("job_types"),
        "salary": item.get("salary"),
        "tags": tags[:50],
        "published_at": created,
    }
    return {
        "quote_or_observation": quote[:2500],
        "source_locator": item.get("url") or item.get("link") or "",
        "source_created_at": str(created),
        "supports": "demand",
        "evidence_strength": "metric",
        "metric": metric,
        "notes": f"{source} public job listing snapshot; listing presence does not establish total market frequency, hiring completion, or candidate success",
    }


def remotive_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    rows = data.get("jobs", []) if isinstance(data, dict) else []
    return [_job_observation(item, source="Remotive") for item in rows[: min(max(int(request.get("limit", 25)), 1), 100)] if isinstance(item, dict) and item.get("title")]


def arbeitnow_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    rows = data.get("data", []) if isinstance(data, dict) else []
    query = query_value(request).lower()
    terms = [term for term in re.split(r"\s+", query) if term]
    primary_matches: list[dict[str, Any]] = []
    full_matches: list[dict[str, Any]] = []

    def contains_term(text: str, term: str) -> bool:
        # Avoid treating `product` as a match for `production`, which creates
        # noisy results in job titles and tags.
        return bool(re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text))

    for item in rows:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        primary = " ".join([str(item.get("title", "")), " ".join(str(tag) for tag in item.get("tags", []))]).lower()
        haystack = " ".join([primary, str(item.get("company_name", "")), str(item.get("location", "")), _visible_job_description(item.get("description"), 500)]).lower()
        if not terms or all(contains_term(primary, term) for term in terms):
            primary_matches.append(item)
        if not terms or all(contains_term(haystack, term) for term in terms):
            full_matches.append(item)
    filtered = primary_matches or full_matches
    return [_job_observation(item, source="Arbeitnow") for item in filtered[: min(max(int(request.get("limit", 25)), 1), 100)]]


def wayback_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    data = json.loads(body)
    rows = data[1:] if isinstance(data, list) and data and isinstance(data[0], list) else data
    return [{"quote_or_observation": f"snapshot {row[0]}: {row[1]}", "source_locator": f"https://web.archive.org/web/{row[0]}/{row[1]}", "supports": "trend", "evidence_strength": "metric", "metric": {"status": row[2] if len(row) > 2 else "unknown"}, "notes": "Wayback snapshot; incomplete snapshots do not explain why a site grew"} for row in rows if isinstance(row, list) and len(row) >= 2]


def arxiv_parser(body: str, url: str, request: dict[str, Any]) -> list[Observation]:
    root = ET.fromstring(body)
    observations: list[Observation] = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = " ".join((entry.findtext("{http://www.w3.org/2005/Atom}title") or "").split())
        summary = " ".join((entry.findtext("{http://www.w3.org/2005/Atom}summary") or "").split())
        link = entry.find("{http://www.w3.org/2005/Atom}id")
        observations.append({"quote_or_observation": f"{title}: {summary[:700]}", "source_locator": link.text if link is not None else "", "supports": "trend", "evidence_strength": "lead", "notes": "arXiv publication signal; a paper does not prove a customer workflow"})
    return observations


def unsupported_url(request: dict[str, Any]) -> str:
    value = request.get("url") or ""
    if value:
        return str(value)
    return ""


def _spec(name: str, source_type: str, transport: str, supports: tuple[str, ...], url_builder: Callable[[dict[str, Any]], str] | None = None, parser: Parser | None = None, note: str = "") -> SourceSpec:
    return SourceSpec(name, source_type, transport, supports, url_builder, parser, note)


REGISTRY: dict[str, SourceSpec] = {
    "google_search": _spec("google_search", "search", "html", ("demand", "distribution"), google_search_url, google_search_parser),
    "google_trends": _spec("google_trends", "trend", "browser", ("frequency", "trend"), google_trends_url, generic_visible_parser, "动态页面；优先使用浏览器，普通 HTTP 只保留覆盖限制"),
    "similarweb": _spec("similarweb", "competitor", "browser", ("distribution", "competition"), similarweb_url, generic_visible_parser, "估算流量；需要公开页面或用户授权账户"),
    "semrush": _spec("semrush", "search", "manual", ("frequency", "competition"), None, None, "需要用户授权账户或导出；不自动绕过计划限制"),
    "ahrefs": _spec("ahrefs", "search", "manual", ("frequency", "competition"), None, None, "需要用户授权账户或导出；不自动绕过计划限制"),
    "reddit": _spec("reddit", "community", "json", ("pain", "frequency"), reddit_url, reddit_parser),
    "x": _spec("x", "community", "browser", ("pain", "trend"), lambda r: "https://x.com/search?" + urllib.parse.urlencode({"q": query_value(r)}), generic_visible_parser, "公开搜索页面；登录/限流时转用户导出"),
    "discord": _spec("discord", "community", "manual", ("pain", "frequency"), None, None, "私有服务器需要用户授权；不自动私信或批量发帖"),
    "fiverr": _spec("fiverr", "marketplace", "html", ("willingness_to_pay", "demand"), fiverr_url, generic_visible_parser),
    "upwork": _spec("upwork", "marketplace", "html", ("willingness_to_pay", "demand"), upwork_url, generic_visible_parser),
    "trustpilot": _spec("trustpilot", "review", "html", ("pain", "competition"), trustpilot_url, generic_visible_parser),
    "chrome_store": _spec("chrome_store", "review", "browser", ("pain", "competition"), chrome_store_url, generic_visible_parser, "动态页面；评价分页和地区会影响覆盖"),
    "app_store": _spec("app_store", "review", "json", ("pain", "competition"), app_store_url, app_store_parser),
    "remotive": _spec("remotive", "marketplace", "json", ("demand", "frequency", "geography"), remotive_url, remotive_parser, "公开远程岗位 API；结果是当前列表快照，不等于总招聘量或录用"),
    "arbeitnow": _spec("arbeitnow", "marketplace", "json", ("demand", "frequency", "geography"), arbeitnow_url, arbeitnow_parser, "公开岗位 API；查询在本地按标题/标签/描述过滤"),
    "there_is_an_ai_for_that": _spec("there_is_an_ai_for_that", "community", "html", ("demand", "frequency"), lambda r: html_search_url("https://theresanaiforthat.com/search/", r, ), generic_visible_parser),
    "product_hunt": _spec("product_hunt", "trend", "browser", ("trend", "demand"), product_hunt_url, generic_visible_parser, "动态页面；投票不等于付款"),
    "toolify": _spec("toolify", "trend", "html", ("trend", "competition"), toolify_url, generic_visible_parser, "榜单是线索，不是收入证明"),
    "traffic_cv": _spec("traffic_cv", "trend", "html", ("trend", "competition"), traffic_cv_url, generic_visible_parser, "排名/流量是方向性线索"),
    "stripe": _spec("stripe", "marketplace", "manual", ("willingness_to_pay",), None, None, "公开支付域名/流量只作线索；不自动访问账户"),
    "creem": _spec("creem", "marketplace", "manual", ("willingness_to_pay",), None, None, "需要用户提供公开页面或导出"),
    "trustmrr": _spec("trustmrr", "marketplace", "manual", ("willingness_to_pay",), None, None, "自报收入需要单独标注，不能当作直接付款"),
    "ads_transparency": _spec("ads_transparency", "competitor", "browser", ("distribution", "competition"), ads_transparency_url, generic_visible_parser, "广告存在是渠道线索，不是 ROI 证明"),
    "wayback": _spec("wayback", "trend", "json", ("trend", "competition"), wayback_url, wayback_parser),
    "query_domains": _spec("query_domains", "trend", "html", ("trend", "distribution"), lambda r: html_search_url("https://query.domains/search", r), generic_visible_parser),
    "searchsuggest_tips": _spec("searchsuggest_tips", "search", "html", ("frequency", "trend"), searchsuggest_url, generic_visible_parser, "自动补全结果是线索，不是付款证明"),
    "pubspy": _spec("pubspy", "competitor", "manual", ("competition",), None, None, "共享标识只能产生线索，不能推断所有权或收入"),
    "wappalyzer": _spec("wappalyzer", "competitor", "manual", ("competition", "risk"), None, None, "技术栈上下文，不是需求证明"),
    "virustotal": _spec("virustotal", "competitor", "manual", ("risk", "competition"), None, None, "API 可能需要 key；不得上传私有样本或推断收入"),
    "github": _spec("github", "trend", "json", ("trend", "competition"), github_url, github_parser),
    "huggingface": _spec("huggingface", "trend", "json", ("trend",), huggingface_url, huggingface_parser),
    "arxiv": _spec("arxiv", "trend", "xml", ("trend",), arxiv_url, arxiv_parser),
}


def get_source(name: str) -> SourceSpec:
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in REGISTRY:
        raise KeyError(f"unknown source: {name}; choose one of {', '.join(sorted(REGISTRY))}")
    return REGISTRY[key]
