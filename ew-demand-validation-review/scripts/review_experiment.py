#!/usr/bin/env python3
"""Review a pre-registered validation plan against an ExperimentRun JSON.

This is a transparent calculator, not a product-market-fit oracle. Thresholds
must be written before the experiment, and unsupported threshold fields remain
explicitly unknown instead of being silently treated as zero.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STRENGTH = {
    "qualified_view": "metric",
    "reply": "lead",
    "lead": "lead",
    "task_submitted": "behavior",
    "demo_completed": "behavior",
    "quote_accepted": "behavior",
    "deposit": "direct_payment",
    "payment": "direct_payment",
    "repeat_use": "behavior",
    "referral": "behavior",
}
SUPPORTS = {
    "qualified_view": "distribution",
    "reply": "demand",
    "lead": "demand",
    "task_submitted": "demand",
    "demo_completed": "demand",
    "quote_accepted": "willingness_to_pay",
    "deposit": "willingness_to_pay",
    "payment": "willingness_to_pay",
    "repeat_use": "demand",
    "referral": "distribution",
}


def nonnegative_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{field}: expected a non-negative number")
    return float(value)


def load_bundle(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("plan"), dict) or not isinstance(raw.get("result"), dict):
        raise ValueError("input: expected {\"plan\": {...}, \"result\": {...}}")
    plan, result = raw["plan"], raw["result"]
    experiment_id = plan.get("experiment_id") or result.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("plan.experiment_id: required")
    if result.get("experiment_id") and result["experiment_id"] != experiment_id:
        raise ValueError("result.experiment_id: must match plan.experiment_id")
    if not isinstance(plan.get("success_threshold", {}), dict) or not isinstance(plan.get("stop_condition", {}), dict):
        raise ValueError("plan.success_threshold and plan.stop_condition: expected objects")
    events = result.get("events", [])
    if not isinstance(events, list):
        raise ValueError("result.events: expected a list")
    for index, item in enumerate(events):
        if not isinstance(item, dict) or not isinstance(item.get("event"), str) or not item["event"].strip():
            raise ValueError(f"result.events[{index}]: requires event")
        nonnegative_number(item.get("count", 0), f"result.events[{index}].count")
        nonnegative_number(item.get("qualified_count", item.get("count", 0)), f"result.events[{index}].qualified_count")
    costs = result.get("costs", {})
    if not isinstance(costs, dict):
        raise ValueError("result.costs: expected an object")
    for key, value in costs.items():
        nonnegative_number(value, f"result.costs.{key}")
    if "limitations" in result and not isinstance(result["limitations"], list):
        raise ValueError("result.limitations: expected a list")
    return plan, result


def event_counts(result: dict[str, Any]) -> tuple[dict[str, float], dict[str, float], dict[str, str]]:
    counts: dict[str, float] = {}
    qualified: dict[str, float] = {}
    notes: dict[str, str] = {}
    for item in result.get("events", []):
        name = item["event"].strip()
        counts[name] = counts.get(name, 0.0) + float(item.get("count", 0))
        qualified[name] = qualified.get(name, 0.0) + float(item.get("qualified_count", item.get("count", 0)))
        if item.get("notes"):
            notes[name] = str(item["notes"])
    return counts, qualified, notes


def check_thresholds(threshold: dict[str, Any], counts: dict[str, float], qualified: dict[str, float]) -> tuple[list[dict[str, Any]], list[str]]:
    criteria: list[dict[str, Any]] = []
    limitations: list[str] = []
    min_events = threshold.get("min_events", {})
    if min_events is not None and not isinstance(min_events, dict):
        limitations.append("success_threshold.min_events 不是对象，无法计算")
        min_events = {}
    for event, minimum in min_events.items():
        try:
            minimum_value = nonnegative_number(minimum, f"success_threshold.min_events.{event}")
        except ValueError as exc:
            limitations.append(str(exc))
            continue
        actual = qualified.get(event, 0.0)
        criteria.append({"kind": "min_events", "event": event, "required": minimum_value, "actual": actual, "met": actual >= minimum_value})

    rates = threshold.get("min_rates", [])
    if rates is not None and not isinstance(rates, list):
        limitations.append("success_threshold.min_rates 不是列表，无法计算")
        rates = []
    for index, rule in enumerate(rates):
        if not isinstance(rule, dict) or not isinstance(rule.get("event"), str) or not isinstance(rule.get("denominator"), str):
            limitations.append(f"success_threshold.min_rates[{index}] 缺少 event/denominator")
            continue
        try:
            minimum = nonnegative_number(rule.get("min"), f"success_threshold.min_rates[{index}].min")
        except ValueError as exc:
            limitations.append(str(exc))
            continue
        denominator = qualified.get(rule["denominator"], 0.0)
        actual = qualified.get(rule["event"], 0.0) / denominator if denominator else None
        criteria.append({"kind": "min_rate", "event": rule["event"], "denominator": rule["denominator"], "required": minimum, "actual": actual, "met": actual is not None and actual >= minimum})
        if actual is None:
            limitations.append(f"缺少 {rule['denominator']}，无法计算 {rule['event']} 转化率")

    if not criteria:
        limitations.append("没有可计算的 success_threshold；请在实验前写出 min_events 或 min_rates")
    return criteria, limitations


def check_stop_condition(stop: dict[str, Any], result: dict[str, Any], counts: dict[str, float]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    costs = result.get("costs", {})
    if "max_spend" in stop:
        maximum = nonnegative_number(stop["max_spend"], "stop_condition.max_spend")
        spend = float(costs.get("ad_spend", 0))
        if spend >= maximum:
            reasons.append(f"广告支出 {spend:g} 已达到上限 {maximum:g}")
    if "max_total_cost" in stop:
        maximum = nonnegative_number(stop["max_total_cost"], "stop_condition.max_total_cost")
        total = sum(float(value) for value in costs.values())
        if total >= maximum:
            reasons.append(f"总成本 {total:g} 已达到上限 {maximum:g}")
    stop_on_events = stop.get("stop_on_events", [])
    if stop_on_events is not None and not isinstance(stop_on_events, list):
        raise ValueError("stop_condition.stop_on_events: expected a list")
    for event in stop_on_events:
        if not isinstance(event, str):
            raise ValueError("stop_condition.stop_on_events: event names must be strings")
        if counts.get(event, 0) > 0:
            reasons.append(f"出现预设停止事件：{event}")
    return bool(reasons), reasons


def build_evidence(result: dict[str, Any], counts: dict[str, float], qualified: dict[str, float], notes: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    recorded_at = result.get("observed_window") or datetime.now(timezone.utc).date().isoformat()
    for event in sorted(counts):
        strength = STRENGTH.get(event, "lead")
        records.append({
            "id": f"X-{event}",
            "source_url": result.get("raw_result_locator", ""),
            "source_type": "validation",
            "source_origin": "experiment",
            "source_locator": result.get("raw_result_locator", "ExperimentRun.events"),
            "captured_at": recorded_at,
            "claim_kind": "experiment_observation",
            "quote_or_observation": f"{event}: count={counts[event]:g}, qualified_count={qualified.get(event, 0):g}",
            "supports": SUPPORTS.get(event, "demand"),
            "evidence_strength": strength,
            "confidence": 4 if event in STRENGTH else 2,
            "does_not_prove": "单次实验不能单独证明规模化需求、留存或单位经济性。",
            "notes": notes.get(event, ""),
        })
    return records


def review(plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    counts, qualified, notes = event_counts(result)
    criteria, limitations = check_thresholds(plan.get("success_threshold", {}), counts, qualified)
    stop_triggered, stop_reasons = check_stop_condition(plan.get("stop_condition", {}), result, counts)
    sample_reached = bool(result.get("sample_reached", False))
    met_count = sum(1 for item in criteria if item["met"])
    if stop_triggered:
        threshold_result = "not_met" if criteria and met_count < len(criteria) else "inconclusive"
        decision = "stop"
    elif criteria and met_count == len(criteria):
        threshold_result, decision = "met", "continue"
    elif not criteria:
        threshold_result, decision = "inconclusive", "run_another_test"
        limitations.append("没有可计算的成功阈值；无法把本轮结果判定为成功或失败")
    elif sample_reached:
        threshold_result, decision = ("partially_met", "adjust") if met_count else ("not_met", "adjust")
    else:
        threshold_result, decision = "inconclusive", "run_another_test"
        limitations.append("sample_reached=false；未达到预注册样本/预算前，不把未达阈值解释为失败")

    payment = qualified.get("payment", 0) + qualified.get("deposit", 0)
    repeat = qualified.get("repeat_use", 0)
    views = qualified.get("qualified_view", 0)
    interpretation = f"记录到 {sum(qualified.values()):g} 个合格事件"
    if views:
        interpretation += f"，其中 qualified_view={views:g}"
        if payment:
            interpretation += f"、payment/deposit={payment:g}（{payment / views:.2%}）"
        else:
            interpretation += "；尚未记录付款或押金"
    if repeat:
        interpretation += f"；repeat_use={repeat:g}"
    if stop_reasons:
        interpretation += "。触发停止条件：" + "；".join(stop_reasons)

    next_action = {
        "continue": "按原计划扩大交付或进入下一阶段，同时检查交付成本、退款和复用。",
        "adjust": "保留已发生的行为证据，优先调整人群、承诺、价格或渠道中证据最弱的一项，再做一次小实验。",
        "stop": "归档本轮假设和证据，记录停止原因；只有出现新的人群、场景或渠道证据时再重开。",
        "run_another_test": "先达到预注册样本/预算或补齐缺失事件，再复盘；不要事后降低阈值。",
    }[decision]
    evidence = build_evidence(result, counts, qualified, notes)
    return {
        "experiment_id": plan["experiment_id"],
        "observed_window": result.get("observed_window", "unknown"),
        "audience_and_channel": result.get("audience_and_channel", "unknown"),
        "events": [{"event": event, "count": counts[event], "qualified_count": qualified.get(event, 0), "notes": notes.get(event, "")} for event in sorted(counts)],
        "costs": result.get("costs", {}),
        "sample_reached": sample_reached,
        "criteria": criteria,
        "threshold_result": threshold_result,
        "stop_triggered": stop_triggered,
        "stop_reasons": stop_reasons,
        "interpretation": interpretation,
        "evidence_records": evidence,
        "decision": decision,
        "updated_opportunity_fields": ["evidence_ids", "decision", "unanswered_questions", "history"],
        "next_action": next_action,
        "limitations": limitations + list(result.get("limitations", [])),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON containing plan and result objects")
    parser.add_argument("--output", required=True, help="DecisionRecord JSON output")
    args = parser.parse_args()
    try:
        plan, result = load_bundle(Path(args.input))
        report = review(plan, result)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"experiment_id": report["experiment_id"], "decision": report["decision"], "threshold_result": report["threshold_result"], "output": args.output}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
