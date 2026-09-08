# EW-Repo Scout

[English](README.md)

**把想法说出来，找到 GitHub 上值得参考的项目。**

准备开发产品、工具或 Skill 时，EW-Repo Scout 帮你先看清：谁做过类似的东西、做到了哪一步、你能借鉴什么。你也可以直接用它找一个现在就能用的现成 Skill。它从问题、使用方式和功能出发搜索，对重点项目继续读源码，检查关键步骤是否有实现。

## 它解决什么问题

搜索结果里经常出现“名字很像，用起来却不是一回事”的项目。EW-Repo Scout 会对照你的想法，回答这些问题：

- 谁在什么场景使用这个项目；
- 它解决什么问题，交付什么结果；
- 用户如何完成核心工作流；
- 与当前 idea 重合和不同在哪里；
- 项目是否仍在维护、成熟度如何、许可证是什么。

关键功能没确认，会明确标注；项目的受欢迎程度、维护状态和相似程度也会分开说明。

## 两种用法

- **找参考**：准备开发时，比较相似项目的用户、工作流、产品差异和实现方式。
- **找现成 Skill**：描述你要完成的任务，查看候选 Skill 的能力、安装/调用方式、前置条件、维护状态和许可证。

找到 Skill 后不会自动安装或运行，除非你明确提出下一步要求。

## 使用方式

对 Codex 或 Claude Code 说：

```text
帮我安装 https://github.com/Ethan-Wang-dev/EW-Skills 中的 ew-repo-scout Skill。
```

装好后直接描述你的 idea，例如：

```text
用 EW-Repo Scout 帮我找：有没有能把网页剪藏到本地、方便个人整理和搜索的开源项目？
```

也可以这样找现成 Skill：

```text
帮我找一个能把网页文章整理成 Markdown 的 Skill，并告诉我怎么安装和使用。
```

存在会改变检索方向的歧义时，Skill 会先问一个澄清问题。完成检索后，Agent 负责运行脚本和生成报告，用户不需要手动执行命令。

## 调试脚本

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

欢迎 Fork 后按自己的习惯修改，也欢迎通过 [PR 贡献改进](https://github.com/Ethan-Wang-dev/EW-Skills/blob/main/CONTRIBUTING.md)。查找不同领域的项目只需描述新的需求，无需修改脚本。

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
