# 出海需求研究数据契约

子 Skill 之间只传递这些结构化对象。字段没有证据时写 `unknown`、空数组或 `null`，不要用看似完整的默认值填空。契约描述的是研究状态，不代表产品已经验证。

## ResearchBrief

```yaml
research_mode: idea|knowledge_base|keyword_or_audience|monitoring
requester: ""
target_user: ""
scenario: ""
problem: ""
desired_outcome: ""
target_markets: []
current_alternative: ""
constraints: []
confirmed: []
assumptions: []
unknowns: []
evidence_gaps: [frequency|value_or_payment|distribution|geography|competition|delivery]
seed_phrases: []
baseline_at: "YYYY-MM-DD or unknown"
```

## EvidenceGap

```yaml
id: G-001
kind: frequency|value_or_payment|distribution|geography|competition|delivery|trend
question: ""
decision_affected: ""
priority: high|medium|low
preferred_source_types: [community|search|marketplace|review|competitor|trend|internal_kb]
stop_when: ""
status: open|answered|conflicted|deferred
```

## AdapterRun

```yaml
id: A-001
gap_id: G-001
source_url: ""
source_name: ""
source_type: community|search|marketplace|review|competitor|trend|internal_kb
adapter: http|api|browser|authenticated_browser|user_export|manual|local_read
query_or_filters: ""
captured_at: "YYYY-MM-DDTHH:MM:SSZ"
access_state: public|authenticated|partial|blocked|rate_limited|not_applicable
batch_limit: ""
budget_limit: ""
coverage_limit: ""
fallback_used: ""
raw_observation_ids: []
```

`AdapterRun` 记录一次调用的边界；它不能代替 `EvidenceRecord`。遇到登录墙、验证码、付费墙或限流时，记录状态并使用允许的回退，不把失败当成没有需求。

## EvidenceRecord

```yaml
id: E-001
source_url: ""
source_type: internal_kb|community|search|marketplace|review|competitor|trend|validation
source_origin: first_party|external|experiment
source_locator: "文件路径、笔记标题或网页段落"
source_created_at: "YYYY-MM-DD or unknown"
captured_at: "YYYY-MM-DD"
market: ""
persona: ""
claim_kind: direct_experience|source_observation|interpretation|hypothesis|external_observation|experiment_observation
quote_or_observation: ""
supports: demand|pain|frequency|willingness_to_pay|distribution|competition|risk
evidence_strength: direct_payment|behavior|repeated_quote|metric|inference|lead
confidence: 1
does_not_prove: ""
conflicts_with: []
adapter: http|api|browser|authenticated_browser|user_export|manual|local_read
query_or_filters: ""
access_state: public|authenticated|blocked|rate_limited|partial|not_applicable
coverage_limit: ""
notes: ""
```

强度顺序通常为：`lead < metric < repeated_quote < behavior < direct_payment`。强度描述证据性质，不是产品质量评分；`confidence` 描述记录是否忠实于原始材料。

## OpportunityCard

```yaml
id: O-001
name: ""
persona: ""
scenario: ""
problem: ""
desired_outcome: ""
current_alternatives: []
knowledge_base_evidence_ids: []
external_evidence_ids: []
evidence_ids: []
target_markets: []
monetization_hypothesis: ""
distribution_channels: []
competitive_gap: ""
minimum_test: ""
score: {}
risks: []
unanswered_questions: []
decision: continue|adjust|stop|unvalidated
next_action: ""
history: []
```

机会卡片是可被实验更新的对象。`ready-for-validation` 只表示可以设计实验；只有实验产生行为证据后，才可进入 `validated_for_next_stage`。

## ValueAssessment

```yaml
opportunity_id: O-001
pain_assessment: {level: "", reason: "", evidence_ids: []}
value_proposition: ""
payment_assessment: {signal: none|weak|possible|direct|unknown, evidence_ids: [], missing: ""}
market_assessment: {markets: [], buyer: "", purchasing_power: "", payment_notes: "", evidence_ids: []}
competition_and_channel: {gap: "", channels: [], acquisition_hypothesis: "", evidence_ids: []}
delivery_assessment: {cost_range: "", constraints: [], fallback: "", evidence_ids: []}
roi_sanity_check: ""
largest_uncertainty: ""
decision: investigate|validate|adjust|stop
```

## ValidationPlan / ValidationAsset

```yaml
# ValidationPlan
experiment_id: X-001
opportunity_id: O-001
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
success_threshold: {}
stop_condition: {}
time_window: ""
ethical_notes: ""

# ValidationAsset
experiment_id: X-001
asset_type: landing_page|preorder_page|service_listing|outreach_script|prototype|demo|community_post|ad_set|pilot_one_pager|followup
files: []
primary_cta: ""
event_map: []
preview_or_use_instructions: ""
authorization_needed: []
known_limits: []
```

## ExperimentRun / DecisionRecord

```yaml
# ExperimentRun
experiment_id: X-001
observed_window: ""
audience_and_channel: ""
events:
  - event: qualified_view
    count: 0
    qualified_count: 0
    notes: ""
costs: {ad_spend: 0, delivery_cost: 0, time_cost: 0}
sample_reached: false
raw_result_locator: ""
limitations: []

# DecisionRecord
experiment_id: X-001
threshold_result: met|partially_met|not_met|inconclusive
evidence_record_ids: []
interpretation: ""
decision: continue|adjust|stop|run_another_test
updated_opportunity_fields: []
next_action: ""
recorded_at: "YYYY-MM-DD"
```

## 状态流转

```text
ResearchBrief + InternalEvidence
  → EvidenceGap[]
  → AdapterRun + EvidenceRecord[]
  → OpportunityCard
  → ValueAssessment + ValidationPlan
  → ValidationAsset
  → ExperimentRun
  → DecisionRecord + 新 EvidenceRecord[]
  → 更新 OpportunityCard / 下一轮 EvidenceGap[]
```

任何结论都要能沿着 `DecisionRecord → EvidenceRecord → AdapterRun/源定位` 回溯。实验结果不覆盖原始假设，而是在 `history` 中追加一条带日期的记录。
