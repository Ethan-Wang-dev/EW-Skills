# EW-Repo Scout

这个 Skill 主要服务有技术想法的开发者、AI 实践者和产品构建者。它把一个 idea、Skill 或产品描述转成 GitHub 检索任务，找到相似开源项目，并解释这些项目在产品和技术上的关系。

## 它解决什么问题

GitHub 的关键词命中不等于产品相似。这个 Skill 先确认需求，再从多个角度召回候选，去重并读取 README、许可证、发布和维护信息；对关键候选继续检查源码中的真实工作流。最终报告同时回答：

- 谁在什么场景使用这个项目；
- 它解决什么问题，交付什么结果；
- 用户如何完成核心工作流；
- 与当前 idea 重合和不同在哪里；
- 项目是否仍在维护、成熟度如何、许可证是什么。

Skill 使用者和被分析产品的最终用户是两层角色。前者从上下文识别，后者从 idea 和项目证据判断，不能混为一谈。

## 使用方式

直接描述你的 idea，例如：

```text
找出能帮助开发者快速发现 GitHub 相似开源项目的项目，重点比较产品工作流和源码核验方式。
```

存在会改变检索方向的歧义时，Skill 会先问一个澄清问题。完成检索后，Agent 负责运行脚本和生成报告，用户不需要手动执行命令。

如果要单独调试脚本，可以在本目录运行：

```bash
python3 scripts/github_discover.py \
  --idea "自然语言描述你的 idea" \
  --query "描述用户任务的查询" \
  --query "描述工作流的查询" \
  --output /tmp/discovery.json
```

设置 `GITHUB_TOKEN` 或 `GH_TOKEN` 可启用认证请求和 Code Search；不设置也能使用 Repository、Topic 和 README 检索，但更容易触发 GitHub 限流。完整参数和来源说明见 [`references/retrieval.md`](references/retrieval.md)。

## 目录

```text
SKILL.md                         Agent 的行为规则和输出要求
agents/openai.yaml               Codex 界面名称、简介和默认提示词
scripts/github_discover.py      GitHub 检索、去重、缓存和证据采集
scripts/render_report.py         校验并渲染完整项目卡片
scripts/evaluate_results.py     维护者内部评测，不属于正常用户流程
references/retrieval.md         信息源、查询角度、预算和限流说明
references/product-comparison.md 产品匹配、星级和源码核验规则
references/report-template.md   报告 JSON 契约和简洁输出格式
references/evaluation.md        维护者 QA 方法
tests/                           脚本回归测试
```

## 自定义位置

- 修改行为和产品判断规则：编辑 `SKILL.md`。
- 修改 GitHub 请求、查询类型或缓存：编辑 `scripts/github_discover.py`。
- 修改报告字段、星级或版式：同步编辑 `references/report-template.md` 和 `scripts/render_report.py`。
- 修改匹配定义和证据标准：编辑 `references/product-comparison.md`。
- 修改 Codex 显示信息：编辑 `agents/openai.yaml`。

复制到 Codex 的技能目录（通常为 `~/.codex/skills/`）即可使用；修改后重新加载 Skill。无需修改脚本才能更换产品领域，通常只需调整查询策略和报告规则。

不要把 GitHub stars 当成相似度或质量分数，也不要把搜索结果当成“搜全 GitHub”的证明。未认证 GitHub API 会跳过 Code Search，并可能受到限流；报告会保留这些限制。

## 本地验证

```bash
python3 -m unittest discover -s tests -v
```

如果安装了 Codex `skill-creator`，再运行其校验器：

```bash
python3 <skill-creator-dir>/scripts/quick_validate.py .
```

渲染器会拒绝过长的项目卡片，要求先压缩内容而不是静默丢失证据。正常用户不需要运行 `evaluate_results.py`；它只用于维护者有人工标注时的回归评测。
