<div align="center">

# EW-Skills

[English](README.md)

### 把好想法变成 AI Agent 可以直接使用的 Skill

为开发者和 AI 实践者持续打磨实用、可复用、以证据为基础的 Skills。

<p>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/stargazers"><img src="https://img.shields.io/github/stars/Ethan-Wang-dev/EW-Skills?style=flat-square&color=gold" alt="GitHub stars"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/network/members"><img src="https://img.shields.io/github/forks/Ethan-Wang-dev/EW-Skills?style=flat-square" alt="GitHub forks"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Ethan-Wang-dev/EW-Skills?style=flat-square" alt="License"></a>
  <a href="https://github.com/Ethan-Wang-dev/EW-Skills"><img src="https://img.shields.io/badge/AI%20agents-Codex%20%7C%20Claude%20Code-6f42c1?style=flat-square" alt="AI agents"></a>
</p>

[开始使用](#快速开始) · [查看 EW-Repo Scout](ew-repo-scout/) · [参与贡献](CONTRIBUTING.md)

</div>

---

## 这是什么

EW-Skills 是一个持续更新的 AI Agent Skill 集合。每个 Skill 都把一类复杂任务整理成清晰的步骤、合适的工具和可以检查的结果，让 Agent 不只是给建议，而是帮助你把事情推进下去。

当前仓库的第一个示例是 **EW-Repo Scout**。它帮助你在开发产品、工具或新 Skill 前，找到 GitHub 上相似的项目，弄清楚它们服务谁、解决什么问题、怎么工作，以及哪些地方值得借鉴。它只是 EW-Skills 的一个示例，后续还会加入更多 Skill。

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

## 快速开始

以当前的 EW-Repo Scout 为例，对 Codex 或 Claude Code 说：

```text
帮我安装 https://github.com/Ethan-Wang-dev/EW-Skills 中的 ew-repo-scout Skill。
```

然后描述你的 idea 或任务：

```text
用 EW-Repo Scout 帮我找一个能把网页文章整理成 Markdown 的现成 Skill，并告诉我怎么安装和使用。
```

如果任务存在会改变方向的歧义，Agent 会先问一个关键问题；确认后自动完成需要的检索、证据收集和结果整理。

## Skill 如何工作

不同 Skill 的具体步骤会不同，但通常会经历：

```mermaid
flowchart LR
    A[描述 idea 或任务] --> B[明确目标和限制]
    B --> C[选择工具和信息源]
    C --> D[执行关键步骤]
    D --> E[检查证据和结果]
    E --> F[给出可执行的下一步]
```

## 仓库结构

```text
EW-Skills/
├── ew-repo-scout/
│   ├── SKILL.md                    # Skill 行为规则与输出要求
│   ├── agents/openai.yaml          # Codex 界面名称与默认提示词
│   ├── scripts/                   # 可复用脚本
│   ├── references/                # 工作流、证据和输出规则
│   └── tests/                     # 回归测试
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

## 参与贡献

EW-Skills 会持续增加和改进。欢迎提交 Issue 或 Pull Request：

- 改进现有 Skill 的工作流和证据标准；
- 修复脚本、工具调用和输出问题；
- 提交新的、可复用的 Skill。

你可以 Fork 后按自己的工作流修改。贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。

<div align="center">

**让每个好想法，都能更快找到下一步。**

</div>
