#!/usr/bin/env python3
"""Measure retrieval against human labels; never invent ground truth or global recall."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def canonical(name, aliases):
    name = name.strip().lower().removeprefix("https://github.com/").rstrip("/")
    seen = set()
    while name in aliases:
        if name in seen:
            raise ValueError("Alias cycle in labels")
        seen.add(name)
        name = aliases[name]
    return name


def evaluate(result, judgments, k=10):
    if k < 1:
        raise ValueError("k must be positive")
    aliases = {key.lower(): value.lower() for key, value in judgments.get("aliases", {}).items()}
    labels = {}
    for name, grade in judgments.get("labels", {}).items():
        if type(grade) is not int or grade not in (0, 1, 2, 3):
            raise ValueError("Labels must be integer grades 0, 1, 2, 3")
        name = canonical(name, aliases)
        if name in labels and labels[name] != grade:
            raise ValueError("Conflicting labels for the same canonical repository")
        labels[name] = grade
    ranked, duplicates = [], 0
    for item in result.get("repositories", []):
        name = canonical(item["full_name"] if isinstance(item, dict) else item, aliases)
        if name not in ranked:
            ranked.append(name)
        else:
            duplicates += 1
    top = ranked[:k]
    relevant = {name for name, grade in labels.items() if grade >= 2}
    matched = set(top) & relevant
    unjudged = [name for name in top if name not in labels]
    direct = any(labels.get(name) == 3 for name in ranked[:3])
    top3_unknown = any(name not in labels for name in ranked[:3])
    ideal_grades = sorted(labels.values(), reverse=True)[:k]
    idcg = sum((2 ** grade - 1) / math.log2(i + 2) for i, grade in enumerate(ideal_grades))
    dcg = sum((2 ** labels.get(name, 0) - 1) / math.log2(i + 2) for i, name in enumerate(top))
    claim_judgments = judgments.get("claim_judgments", [])
    if any(value not in ("supported", "unsupported", "unknown") for value in claim_judgments):
        raise ValueError("Claim labels must be supported, unsupported or unknown")
    checked_claims = [value for value in claim_judgments if value != "unknown"]
    search = result.get("search_metadata", {})
    warnings = ["Recall is relative to the labeled pool, not all of GitHub.",
                "Precision uses K slots; missing slots count as no result.",
                "Grades: 3 direct, 2 adjacent/relevant, 1 component/reference, 0 irrelevant."]
    if unjudged:
        warnings.append("Unjudged returned repositories prevent a point estimate of precision/NDCG.")
    if search.get("status") in ("partial", "failed"):
        warnings.append("Retrieval was partial/failed; compare quota and source coverage before comparing scores.")
    if search.get("seed_repositories"):
        warnings.append("Seed repositories were supplied; label whether this run is assisted to avoid recall leakage.")
    return {
        "case_id": judgments.get("case_id"), "k": k,
        "intent_correct": judgments.get("intent_correct"),
        "clarification_appropriate": judgments.get("clarification_appropriate"),
        "unique_returned": len(ranked), "returned_at_k": len(top),
        "duplicate_count": duplicates, "known_relevant_count": len(relevant),
        "judgment_coverage_at_k": (len(top) - len(unjudged)) / len(top) if top else None,
        "precision_at_k": len(matched) / k if not unjudged else None,
        "precision_lower_bound_at_k": len(matched) / k,
        "precision_upper_bound_at_k": (len(matched) + len(unjudged)) / k,
        "known_recall_at_k": len(matched) / len(relevant) if relevant else None,
        "known_recall_all": len(set(ranked) & relevant) / len(relevant) if relevant else None,
        "direct_hit_at_3": True if direct else None if top3_unknown else False,
        "ndcg_at_k_over_labeled_pool": dcg / idcg if idcg and not unjudged else None,
        "unjudged_at_k": unjudged,
        "known_relevant_missing_at_k": sorted(relevant - set(top)),
        "unsupported_claim_rate_checked": checked_claims.count("unsupported") / len(checked_claims) if checked_claims else None,
        "claim_judgment_coverage": len(checked_claims) / len(claim_judgments) if claim_judgments else None,
        "retrieval_status": search.get("status"),
        "elapsed_seconds": search.get("elapsed_seconds"),
        "network_requests": search.get("network_requests"),
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, help="Discovery JSON or final ordered repositories JSON")
    parser.add_argument("--labels", required=True, help="Human judgments JSON")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(Path(args.results).read_text()),
                          json.loads(Path(args.labels).read_text()), args.k)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
