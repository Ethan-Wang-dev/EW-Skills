# 检索质量评估（维护者内部）

本文件和 `scripts/evaluate_results.py` 属于 skill 开发与回归验证工具，不是普通用户的产品功能。正常发现流程不要求用户准备人工标签、运行脚本或查看这些指标；只有维护者明确进行基准测试时才使用。

把质量拆成独立维度，不用一个总分掩盖问题。自检清单不等于经过标注验证的准确率：

1. **意图一致性**：目标用户、问题和核心工作流是否与用户原意一致；关键歧义是否先确认。
2. **候选召回**：不同表达、不同项目形态和不同 GitHub 信息源能否找到已知相关项目。
3. **排序与分类**：高相关项目是否排在前面，且直接产品、相邻产品、技术组件和低相关结果是否分开。
4. **证据正确性**：功能、用户、License、维护状态和成熟度是否有 README、文档、代码或 API 元数据支持。
5. **成本和时效**：耗时、请求量、缓存时间、错误率；相同质量下才比较速度。

## 建立小型评测集

为每个真实 idea 记录，并把评测标签与 Agent 的检索输入分开，防止提前给出答案：

- 原始输入和必要的澄清回答；
- 目标用户、问题、工作流和核心能力；
- 3～10 个人工确认的相关仓库；
- 直接相似、相邻、组件和误匹配标签；
- 必须找到的关键项目；
- 不应作为直接匹配的项目。

至少覆盖不同使用模式和项目形态，例如个人剪藏、开发者工具、浏览器扩展、自托管服务和团队协作。

## 建议指标

```text
Known Recall@10 = 前 10 个结果中命中的已知相关项目 / 已标注的相关项目总数
Precision@10 = 前 10 个结果中被人工判定相关的项目 / 10（不足 10 项时空位计为未返回）
Top-3 direct hit = 前 3 个是否包含直接相似项目
Unsupported claim rate = 已检查且无支持证据的断言 / 已检查的断言
```

Known Recall 是有限标注池内的召回率，不是整个 GitHub 的召回率。未标注新项目不能当成无关：脚本会给 Precision 下界/上界及标注覆盖率，未充分标注时不输出点估计。无相关项目标签时，Recall 为 null。Top-3 是单个案例的布尔值，批量案例才能计算命中率。

初始目标可以讨论 Known Recall@10 ≥ 0.8、Precision@10 ≥ 0.7、Top-3 直接匹配命中率 ≥ 0.8，但这些只是待校准目标，不能作为当前实现已达到的成绩。

## 可运行评测

保存人工标注 JSON；以下仓库名仅展示格式，不是真实基准答案：

```json
{
  "case_id": "personal-capture-01",
  "intent_correct": true,
  "clarification_appropriate": true,
  "labels": {"owner/direct": 3, "owner/adjacent": 2, "owner/component": 1, "owner/unrelated": 0},
  "aliases": {"owner/old-name": "owner/direct"},
  "claim_judgments": ["supported", "unsupported", "unknown"]
}
```

3 = 直接相似、2 = 相邻但相关、1 = 组件或参考、0 = 无关。默认 Recall/Precision 以 2、3 为相关；NDCG 保留 0–3 的相关度差异。意图与澄清字段是人工判断，未知应为 null，不由脚本自动推断。

```bash
python3 <skill_dir>/scripts/evaluate_results.py \
  --results /tmp/discovery.json --labels /tmp/labels.json --k 10 \
  --output /tmp/evaluation.json
```

可评估检索脚本的候选排序，也可评估 Agent 最终排序：最终排序文件使用 `{"repositories":[{"full_name":"owner/repo"}]}`，顺序即排名。两阶段分别评估，避免把语言模型重排效果误认为底层召回效果。

## 比较优化前后

同一个已澄清 idea、相近检索时间、相同预算和认证条件，分别保存：A 仓库检索、B 增加 topic/代码/Issue 检索、C 深读及 Agent 重排。比较 Known Recall、Precision、NDCG、未标注比例、耗时、请求量和错误率。

把各版本候选合并后盲标，新增相关项目纳入标注池并用同一批标签重算所有版本。直接指定 `--seed-repo` 的已知答案应标为辅助检索，不能和无提示召回结果混算。至少保留一组未参与调参的案例，避免围绕个人剪藏或某个热门项目过拟合。

维护、License 与功能断言需要逐条核对证据；不要把报告有链接就当作证据正确。没有人工标注或未做独立行为测试时，明确写“未评估”。

每次评测都保存查询、数据源、检索时间、Token 状态、限流错误和候选数量。若意图理解错误，应先修复澄清流程；若召回不足，增加查询或信息源；若排序错误，修复重排和分类；若事实错误，补充证据核验。

## 脚本回归检查

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <skill_dir>/tests -v
```

这些测试检查错误处理、排序不受 stars 干扰、来源保留、去重与指标计算。它们不证明 Agent 能正确理解任何 idea，也不替代真实项目的人工作答评测。
