<div align="center">

<img src="assets/ew-skills-avatar.png" alt="EW-Skills Q版头像" width="360">

# EW-SKILLS

[English](README.md)

### 把专家从不写下来的做事方法，交给 Agent

<em>EW-Skills 把真实工作中的提问、判断、工具、证据检查和失败处理整理出来，让开发者和 AI 实践者复用的不只是答案，还有答案背后的做事方法。</em>

<p>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/stargazers"><img src="https://img.shields.io/github/stars/Ethan-Wang-dev/EW-Skills?style=flat-square&color=gold" alt="GitHub stars"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/network/members"><img src="https://img.shields.io/github/forks/Ethan-Wang-dev/EW-Skills?style=flat-square" alt="GitHub forks"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Ethan-Wang-dev/EW-Skills?style=flat-square" alt="License"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills"><img src="https://img.shields.io/badge/AI%20agents-Codex%20%7C%20Claude%20Code-6f42c1?style=flat-square" alt="AI agents"></a>
</p>

<p><strong>使用的工具和技术：</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Markdown-000000.svg?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown">
  <img src="https://img.shields.io/badge/GitHub-181717.svg?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  <img src="https://img.shields.io/badge/Codex%20%7C%20Claude%20Code-6f42c1.svg?style=for-the-badge" alt="Codex 和 Claude Code">
</p>

[开始使用](#快速开始) · [查看 EW-Repo Scout](ew-repo-scout/) · [参与贡献](CONTRIBUTING.zh-CN.md)

</div>

---

## 这是什么

EW-Skills 是一个会持续长大的 AI Agent Skill 集合。每个 Skill 都把一类复杂任务整理成清晰的步骤、合适的工具和可以检查的结果，让 Agent 不只是给建议，而是陪你把事情推进下去。

当前仓库包含 **21 个 Skill**：EW-Repo Scout、Codex ↔ Grok Bot 双向协作，以及由 18 个模块组成的 EW 海外产品发现系列。

## 选择 Skill

| 你想做什么 | 入口 |
| --- | --- |
| 找相似开源项目或现成 Skill，核对实现 | [ew-repo-scout](ew-repo-scout/SKILL.md) |
| 分析出海机会、设计验证或复盘结果 | [ew-overseas-product-discovery](ew-overseas-product-discovery/SKILL.md) |
| 让 Codex 调用 Grok Bot 查询资料 | [grok-bot-collab](grok-bot-collab/SKILL.md) |
| 让 Grok Bot 把代码、文档和数据任务交给 Codex | [codex-offload](codex-offload/SKILL.md) |

出海研究通常从总控入口开始，由它按证据缺口选择内部模块。


## EW Demand Evidence

用于出海产品需求研究的证据标准化。它先读取用户自己的知识库，将内容区分为一手经验、外部观察、解释和假设，再按频率、付费、分发、地域或风险缺口选择小批量外部来源。它不把搜索量、点赞或 AI 总结直接当成需求已验证。

## EW 海外产品发现

总控 Skill 只向用户呈现三个入口：

- **分析机会**：先读自己的资料，明确人群和任务，只补当前缺口需要的证据，形成机会卡片。
- **设计验证**：根据最大未知选择访谈、人工交付、服务市场、预售页、原型、社群测试、小额渠道、B2B 试点或复用/推荐测试。
- **复盘结果**：区分合格事件、付款、复用、推荐、成本和限制，决定继续、调整、停止或再做一次实验。

来源路由支持通过来源注册表进行有边界的自动批量采集，优先公开 HTTP/API，必要时使用明确开启的公开浏览器会话，也支持用户授权会话和导出文件。不依赖 Firecrawl，不绕过登录、验证码、付费墙或限流，不在网站条款禁止的范围外使用浏览器自动化；HTTP 适配器会遵守 `robots.txt`。验证材料默认只在本地生成；发布、收款、投放广告和批量外联都需要明确授权。

内部模块包括：

`ew-demand-intake` · `ew-demand-kb` · `ew-demand-source-router` · `ew-demand-evidence` · `ew-demand-keyword` · `ew-demand-community` · `ew-demand-marketplace` · `ew-demand-reviews` · `ew-demand-competitor` · `ew-demand-trend` · `ew-demand-geo` · `ew-demand-opportunity` · `ew-demand-value` · `ew-demand-score` · `ew-demand-validation` · `ew-validation-assets` · `ew-demand-validation-review` · `ew-overseas-product-discovery`

模块交接格式见 [`data-contracts.md`](ew-overseas-product-discovery/references/data-contracts.md)。需要运行多来源采集时使用 `ew-demand-source-router/scripts/run_sources.py`；需要生成本地页面或服务材料时使用 `ew-validation-assets/scripts/build_experiment.py`；需要按预注册阈值复盘时使用 `ew-demand-validation-review/scripts/review_experiment.py`。

多来源自动采集示例：

```bash
python3 ew-demand-source-router/scripts/run_sources.py \
  --input research-run.json \
  --output-dir ./research-runs/feedback \
  --max-requests 5
```

只有在需要读取公开动态页面时才添加 `--allow-browser`。每次运行会生成 `research-run.json`、`evidence.jsonl`、`analysis.json`、`summary.md` 和逐来源的适配器记录。

对 Similarweb、Semrush、Ahrefs、Discord 等重要但需要权限的来源，可在用户已登录的前提下显式提供 profile/state：

```bash
python3 ew-demand-source-router/scripts/run_sources.py \
  --input research-run.json --output-dir ./research-runs/authorized \
  --allow-authenticated-browser --browser-profile "/path/to/profile"
```

也可以先从网站导出 CSV/JSON/JSONL/HTML，再本地标准化（不会上传或复制原文件）：

```bash
python3 ew-demand-source-router/scripts/ingest_export.py \
  --input ./exports/semrush.csv --output-dir ./research-runs/semrush-export \
  --source semrush --source-type search --market US
```

验证码、付费墙、私有权限或限流不会被绕过；运行结果会保留限制并提示切换导出路径。

## Codex ↔ Grok Bot

双向通讯由两个互补的 Skill 组成：

| 方向 | Skill | 工作流 |
| --- | --- | --- |
| Codex → Grok Bot | [grok-bot-collab](grok-bot-collab/SKILL.md) | 通过 MCP 查询 X、只读邮件和浏览器资料；已有 `gbask` 作为异步备用通道 |
| Grok Bot → Codex | [codex-offload](codex-offload/SKILL.md) | 把代码、文档与数据任务交给在线 Mac，独立验收、有限返工并回传结果 |

将 `grok-bot-collab` 安装到 Codex skills 目录；将 `codex-offload` 加入 Grok Bot 可读取的 workflow/skill 指引。**这次发布的是工作流 Skill，MCP 桥接、gbask webhook 和 codex-hub 运行器需要另行部署。** 详见 [MCP 前置条件](grok-bot-collab/references/setup.md)、[gbask 协议](grok-bot-collab/references/gbask.md) 和 [codex-hub 前置条件](codex-offload/references/runner.md)。

2026-10-26 更新：按当前 MCP schema 与本机运行器源码梳理既有 skill，移除个人账号标识，补齐状态处理和失败恢复。已验证 MCP 工具发现与一次只读 Grok Bot 通讯；本次未测试 webhook 回传或新增真实 Codex 委派任务。

## EW-Repo Scout

在 GitHub 上发现与 idea、Skill 或产品相似的开源项目，并比较目标用户、问题、工作流、产品差异和实现证据。它也可以帮你寻找满足当前任务的现成 Skill，并说明安装、调用方式和前置条件。

### 为什么值得用

<table>
<tr>
<td width="50%">

### 🚀 开始前少走弯路

动手开发前，先知道有没有人做过、别人做到哪一步，避免重复造轮子。

</td>
<td width="50%">

### 🎯 找到真正相关的方案

不再被相似的名字和关键词误导，找到真正解决同一个问题的项目和 Skill。

</td>
</tr>
<tr>
<td width="50%">

### 🧭 看清差距再做决定

知道哪些可以直接使用，哪些适合借鉴，哪些地方还需要自己补上。

</td>
<td width="50%">

### ⚡ 更快走到下一步

把分散的项目、信息和判断整理好，让你更快开始使用、验证或开发。

</td>
</tr>
</table>

### 报告会回答什么

| 你想知道什么 | 你会得到什么 |
| --- | --- |
| 谁做过类似的东西？ | **候选仓库**、**发现路径** 和 **产品定位** |
| 它真的相似吗？ | 对 **目标用户**、**问题**、**工作流** 和 **结果** 的比较 |
| 关键功能真的存在吗？ | **源码观察**、**文档证据**，或明确标注的 **未知项** |
| 应该先看哪个项目？ | 分开的 **产品匹配度**、**功能匹配度** 和 **技术匹配度** |
| 能不能直接复用？ | **维护状态**、**成熟度**、**许可证** 和 **适用边界** |

## 快速开始

以当前的 EW-Repo Scout 为例，对 Codex 或 Claude Code 说：

```text
帮我安装 https://github.com/Ethan-Wang-dev/EW-Skills 中的 ew-repo-scout Skill。
```

然后描述你的 idea 或任务：

```text
用 EW-Repo Scout 帮我找一个能把网页文章整理成 Markdown 的现成 Skill，并告诉我怎么安装和使用。
```

如果任务存在会改变方向的歧义，Agent 会先问一个关键问题；方向确定后，就会自动完成检索、证据收集和结果整理。

出海系列的 18 个模块会相互引用，安装时应保留为同一 skills 目录下的兄弟文件夹。可以对 Agent 说：

```text
从 https://github.com/Ethan-Wang-dev/EW-Skills 安装完整的出海产品发现系列：
所有 ew-demand-* 目录，以及 ew-overseas-product-discovery 和 ew-validation-assets。
保留它们的 scripts、references、agents 文件；已有同名 Skill 时先比较差异。
```

Python 辅助脚本使用 Python 3.10+ 和标准库。浏览器采集还需要可用的 `agent-browser` CLI，并显式开启对应浏览器选项；HTTP 与本地导入不需要该 CLI。安装 Skill 不会自动提供第三方网站账号或访问权限。

研究出海产品时，可以直接调用总控 Skill：

```text
使用 $ew-overseas-product-discovery 分析这个想法，先读取 ./my-research，并告诉我成本最低的下一步验证。
使用 $ew-overseas-product-discovery 为这个机会设计预售或人工交付实验。
使用 $ew-overseas-product-discovery 复盘这份 ExperimentRun，判断继续、调整、停止还是再做一次。
```

## EW-Repo Scout 工作流

以下流程适用于开源项目检索：

```mermaid
flowchart LR
    A[描述 idea 或任务] --> B[明确用户和场景]
    B --> C[从多个角度检索 GitHub]
    C --> D[阅读 README 和项目证据]
    D --> E[检查关键工作流和源码]
    E --> F[比较匹配度、差异和状态]
    F --> G[整理项目卡片和下一步]
```

## 仓库结构

```text
EW-Skills/
├── grok-bot-collab/                # Codex → Grok Bot
├── codex-offload/                  # Grok Bot → Codex
├── ew-repo-scout/
│   ├── SKILL.md                    # Skill 行为规则与输出要求
│   ├── agents/openai.yaml          # Codex 界面名称与默认提示词
│   ├── scripts/
│   │   ├── github_discover.py      # GitHub 检索、去重和证据收集
│   │   ├── render_report.py        # 校验并渲染项目卡片
│   │   └── evaluate_results.py     # 维护者使用的评测工具
│   ├── references/                 # 检索、比较和报告规则
│   └── tests/                      # 回归测试
├── ew-demand-evidence/
│   ├── SKILL.md                    # 需求证据标准化与知识库优先规则
│   ├── agents/openai.yaml          # Codex 界面名称与默认提示词
│   └── references/source-adapters.md # 单站/多站来源适配器与失败回退
├── ew-overseas-product-discovery/
│   ├── SKILL.md                    # 端到端路由与用户侧输出
│   └── references/data-contracts.md # 研究/证据/实验共享契约
├── ew-validation-assets/
│   ├── SKILL.md                    # 最小、诚实的验证材料
│   └── scripts/build_experiment.py # 本地页面/服务材料生成器
├── ew-demand-validation-review/
│   ├── SKILL.md                    # 实验结果解释
│   └── scripts/review_experiment.py # 阈值和停止条件计算器
├── ew-demand-source-router/
│   ├── references/source-playbooks.md # 网站缺口与回退方法
│   ├── scripts/fetch_public.py       # 受限公开 HTTP 适配器
│   ├── scripts/ingest_export.py      # 本地 CSV/JSON/HTML 导出标准化
│   ├── scripts/source_registry.py    # 目标来源 URL/解析注册表
│   └── scripts/run_sources.py        # 多来源运行器与自动汇总
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 本地验证

以 EW-Repo Scout 为例：

```bash
python3 -m unittest discover -s ew-repo-scout/tests -v
```

需要更高 GitHub API 配额或 Code Search 时，设置 `GITHUB_TOKEN` 或 `GH_TOKEN`。未认证请求仍可使用 Repository、Topic 和 README 检索，但更容易遇到 GitHub 限流。

验证辅助脚本测试：

```bash
python3 -m unittest discover -s ew-demand-source-router/tests -v
python3 -m unittest discover -s ew-overseas-product-discovery/tests -v
python3 -m unittest discover -s ew-validation-assets/tests -v
python3 -m unittest discover -s ew-demand-validation-review/tests -v
```

## 一起来贡献

EW-Skills 还在不断成长，欢迎来一起把它变得更好！发现问题就提 Issue，想到改进就发 Pull Request，想分享自己的 Skill 也可以直接来：

- 改进现有 Skill 的工作流和证据标准；
- 修复脚本、工具调用和输出问题；
- 提交新的、可复用的 Skill。

不管是改一行文案、修一个小问题，还是带来一个全新的 Skill，都欢迎。你也可以先 Fork，按自己的工作流改起来。详细流程见 [中文贡献说明](CONTRIBUTING.zh-CN.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。

<div align="center">

**带着你的想法来，一起把下一步做出来。**

</div>
