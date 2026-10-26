---
name: ew-demand-validation-review
description: "读取验证实验的行为结果，区分信号、意向、付款和复用，并更新机会决策。"
---

# EW Demand Validation Review

## Purpose

Use this skill after a validation run. Turn observed events into new evidence, compare them with pre-registered thresholds, and choose continue, adjust, stop, or run another test.

For a reproducible threshold check, pass a JSON bundle containing `plan` and `result` to [scripts/review_experiment.py](scripts/review_experiment.py):

```bash
python3 <skill-dir>/scripts/review_experiment.py \
  --input experiment-run.json \
  --output decision-record.json
```

The calculator supports pre-registered `success_threshold.min_events` and `success_threshold.min_rates`, plus `stop_condition.max_spend`, `max_total_cost`, and `stop_on_events`. Unsupported or missing fields remain explicit limitations. See [../ew-overseas-product-discovery/references/data-contracts.md](../ew-overseas-product-discovery/references/data-contracts.md) for the `ExperimentRun` and `DecisionRecord` contract.

最小输入示例：

```json
{
  "plan": {
    "experiment_id": "X-001",
    "success_threshold": {"min_events": {"payment": 1}},
    "stop_condition": {"max_total_cost": 100}
  },
  "result": {
    "experiment_id": "X-001",
    "observed_window": "2026-09-13",
    "audience_and_channel": "US / target community",
    "events": [{"event": "qualified_view", "count": 50, "qualified_count": 40}, {"event": "payment", "count": 1, "qualified_count": 1}],
    "costs": {"ad_spend": 0, "delivery_cost": 10, "time_cost": 3},
    "sample_reached": true
  }
}
```

## Workflow

1. Check that the audience, channel, price, time window, sample/budget, and experiment definition are known.
2. Deduplicate events and separate qualified users from accidental traffic, bots, friends, and unsupported geographies.
3. Classify each result: `metric`, `behavior`, `direct_payment`, `inference`, or `lead`. Preserve refunds, cancellations, and negative feedback.
4. Compare results to the planned success threshold and stop condition. Do not change the threshold after seeing the result without recording why.
5. Explain channel effects separately from problem/value effects: low clicks may be message or reach; high clicks with no task/payment may be offer, trust, price, or problem mismatch.
6. Update the opportunity evidence IDs, unanswered questions, confidence, and next experiment. Keep the original hypothesis and result history.

## Output

```yaml
experiment_id: ""
observed_window: ""
audience_and_channel: ""
events: [{event: "", count: 0, qualified_count: 0, notes: ""}]
costs: {ad_spend: "", delivery_cost: "", time_cost: ""}
evidence_records: []
threshold_result: met|partially_met|not_met|inconclusive
interpretation: ""
decision: continue|adjust|stop|run_another_test
updated_opportunity_fields: []
next_action: ""
limitations: []
```

## Decision rules

- Payment, completed paid work, repeat use, and referral are stronger than clicks, votes, views, or positive comments.
- A failed channel test does not automatically disprove the problem; check reach, message, offer, price, and audience quality.
- A paid order does not automatically prove scalable economics; check delivery cost, quality, refunds, and repeat behavior.
- If evidence conflicts, retain both results with dates and design a discriminating next test.
