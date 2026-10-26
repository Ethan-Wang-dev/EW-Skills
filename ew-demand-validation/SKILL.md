---
name: ew-demand-validation
description: "根据机会的最大不确定性选择最低成本的需求验证方式，生成可执行实验、指标、阈值和停止条件。"
---

# EW Demand Validation

## Purpose

Use this skill after an `OpportunityCard` and value assessment exist. The central decision is not “做不做 Landing Page”，而是“当前最缺哪种证据，哪种测试能最快得到它”。

## Validation ladder

Use the weakest test that can answer the current question, then move toward stronger behavior:

```text
signal → response/intent → real task → commitment/payment → repeat use → referral/channel economics
```

Search volume, votes, traffic, rankings, complaints, or community size are signals. They do not count as payment or retention.

## Workflow

1. State one falsifiable hypothesis and the largest uncertainty.
2. Choose one primary mode:
   - `discovery_interview`: problem and recent real incident are unclear;
   - `concierge_service`: outcome/delivery is unclear; perform the job manually;
   - `marketplace_offer`: test a priced service where buyers already request work;
   - `landing_preorder`: test message, price, waitlist, deposit, or pre-sale with targeted traffic;
   - `prototype_task`: test workflow and output quality with a clickable demo or Wizard-of-Oz;
   - `community_test`: test demand and feedback in a relevant public community with non-spam participation;
   - `paid_traffic`: test qualified acquisition and CTA with a small capped budget;
   - `b2b_pilot`: test a paid pilot, procurement path, or letter of intent;
   - `retention_followup`: test repeated task, renewal, or referral after a first success.
3. Select one channel appropriate to the target user. A page without qualified traffic is not a validation.
4. Define the offer, price, audience, sample size or budget, events, success threshold, stop condition, and time window before running.
5. Pass the plan to `ew-validation-assets` for the smallest required asset. Do not build a full product unless the experiment requires it.
6. Record behavior in `ExperimentRun`, then send it to `ew-demand-validation-review`.

## Output

```yaml
hypothesis: ""
largest_uncertainty: ""
mode: discovery_interview|concierge_service|marketplace_offer|landing_preorder|prototype_task|community_test|paid_traffic|b2b_pilot|retention_followup
target_user: ""
channel: ""
offer: ""
price: ""
asset_request: landing_page|preorder_page|service_listing|outreach_script|prototype|demo|community_post|ad_set|pilot_one_pager|followup
events: [qualified_view|reply|lead|task_submitted|demo_completed|quote_accepted|deposit|payment|repeat_use|referral]
sample_or_budget: ""
success_threshold: ""
stop_condition: ""
time_window: ""
ethical_notes: ""
expected_evidence_strength: lead|metric|behavior|direct_payment
```

## Mode selection rules

- If the user cannot name a recent real task, start with interview/community evidence rather than a page.
- If the user can perform the result manually, prefer concierge or marketplace service before software.
- If the value and price can be stated clearly, use a transparent pre-sale or paid pilot; disclose that the product is pre-launch.
- If users need to see the workflow, use a prototype or sample output.
- If demand is plausible but reachability is unknown, test one channel at a capped budget; do not confuse impressions with qualified demand.
- If a first user exists, test a second task or referral before optimizing acquisition.

## Guardrails

- Do not call a waitlist, click, or like “validated” without stating its strength.
- Do not charge for an unavailable product without clear pre-sale terms and refund/fulfillment expectations.
- Do not send mass unsolicited messages or violate community rules.
- Prefer one audience, one promise, one CTA, and one primary price per experiment.
