# 完整但简洁的项目卡片

Skill 主要服务有技术想法的开发者、AI 实践者和其他产品构建者，但这不是固定用户值或检索过滤条件。报告中的“Skill 使用者”和 idea 对应产品的“目标用户”必须分开；实际使用者不明时写“未确认”。仅在关键歧义已解决，或用户明确要求分支探索后生成报告。澄清回合只问关键问题。所有正式推荐项目使用相同字段；不能为了简短而省略目标用户、工作流或项目状态。信息不足填“未确认 + 原因”。宁可推荐较少项目，也不要用不完整表格凑数。

## 生成方式

Agent 根据已读取的证据填写 JSON，再使用报告生成器校验和渲染：

```bash
python3 <skill_dir>/scripts/render_report.py \
  --input /tmp/product-comparison.json --output /tmp/product-comparison.md
```

这是正常报告生成流程，由 Agent 完成，用户不需要操作脚本。它只验证字段和星级格式，不验证事实真伪。生成失败时补齐字段或明确未知，不凭空编造。最终答复必须直接包含渲染后的完整项目卡片；Markdown/JSON 链接只补充详细证据和检索记录，不能用摘要或链接替代卡片。

默认展示“需求理解 → 逐项目卡片 → 判断 → 简短检索范围”。每个字段只写一条事实或结论；重合与差异各 1–3 点分开，工作流用箭头。每张卡片最多 5 个工作流步骤、6 项能力和 5 条核验记录，整份报告最多 5 个推荐项目；超出时先压缩或移入原始产物，不能静默截断。详细查询、响应、源码笔记放在产物中，前台只保留来源、范围和重要限制。原始 API 计数不是产品价值展示的主体。

评分前阅读 [product-comparison.md](product-comparison.md)。匹配用 ⭐️ 五级；❔表示不足以评分，不是低匹配。不要把所有信息塞进“主要重合与差异”一列。若附额外概览表，只作为索引，不能代替项目卡片。

## JSON 契约

以下是结构示例，内容均为待填字段，不是实际项目结论。所有非可选字段必填，可用“未明确”“未确认（原因）”表达缺失信息。

```json
{
  "idea": {
    "original": "用户原始需求或最新修正",
    "requester": "实际使用 Skill 的人；从上下文判断，无法判断则写未确认",
    "target_user": "目标用户",
    "scenario": "触发/使用场景",
    "problem": "要解决的问题",
    "outcome": "用户希望获得的结果",
    "current_alternative": "当前做法；未明确则标明",
    "workflow": ["输入或触发", "核心处理", "输出或后续操作"],
    "core_capabilities": ["必要能力 A", "必要能力 B"],
    "form_and_constraints": "产品形态、平台、部署及用户明确限制；不擅自补全",
    "confirmed": "用户已明确的内容",
    "assumptions": "暂定理解及依据；没有则写无",
    "unknowns": "非关键未知；没有则写无"
  },
  "projects": [
    {
      "repo": "owner/repo",
      "relationship": "直接产品匹配 / 相邻产品 / 技术组件 / 架构或交互参考",
      "form": "库 / CLI / 扩展 / Web 产品 / 其它",
      "target_user": "实际目标用户及依据",
      "scenario": "实际使用场景",
      "problem": "项目解决的问题",
      "outcome": "项目带给用户的结果",
      "workflow": ["实际入口", "处理过程", "结果；缺失阶段要明示"],
      "capabilities": ["核心能力与必要证据链接"],
      "product_match": {"stars": 4, "reason": "从用户、问题、场景、工作流和结果说明评分"},
      "functional_match": {"stars": 3, "reason": "哪些必要能力覆盖、哪些未覆盖或未确认"},
      "technical_match": {"stars": null, "reason": "未指定技术基线，无法判断；如已明确则按实际证据打星"},
      "overlap": ["具体重合点一", "具体重合点二"],
      "differences": ["关键产品边界或缺失步骤"],
      "workflow_checks": [
        {"step": "入口到处理", "status": "code_observed", "evidence": "具体调用关系与 [文件](https://github.com/owner/repo/blob/COMMIT/path#L10)"},
        {"step": "持久化或后续动作", "status": "docs_only", "evidence": "[官方文档](https://github.com/owner/repo) 声明；源码尚未核验"}
      ],
      "maintenance": "带日期的 last push/实际提交、归档与发布证据，失败与未找到分开",
      "maturity": "原型/可用/较完整/未知及依据，不把 CLI 或 Docker 当成熟度",
      "license": "许可证、文件链接、开源/源码可见/未确认",
      "takeaway": "为什么值得用户关注：同类方案、可复用环节或产品参考",
      "discovery": "可选：有日志支持的发现路径；不要凭低 star 宣称隐藏宝藏"
    }
  ],
  "conclusion": {
    "closest": "谁最接近，以及产品层面的主要理由",
    "common_ground": "已存在的方案覆盖了哪些用户任务",
    "unconfirmed": "未确认之处；不是不存在的证明",
    "next": "最值得进一步理解的产品边界或实现环节"
  },
  "retrieval": {
    "summary": "检索日期、实际成功的信息源、成功/部分完成、样本范围、核验方式与重要盲区；源码未运行时明示",
    "artifact": "[完整检索记录](/absolute/path/to/results.json)"
  }
}
```

workflow_checks.status 仅允许 code_observed（源码观察）、docs_only（文档声明）、unknown（未确认）。对关键步骤尚未核验时，用 unknown 并说明原因，不能删掉核验字段。所有事实的证据贴近断言，而不是仅给项目首页。

projects 可以是空数组：没有可靠候选或检索失败时不要编造。附加未深读候选只放在原始结果里；若作为正式推荐展示，也要补齐同一组字段。
