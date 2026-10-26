# 运行环境与安装

把本目录复制到 Codex 的 skills 目录（默认 `~/.codex/skills/grok-bot-collab`），保留已有安装的备份。安装 skill 只增加指引，不自动安装 MCP 服务、Grok Bot 或登录凭证。

## MCP 前置条件

- 可访问的 Grok Bot 账号与真实存在的接收机器人。
- 带 `@cursor/bdk/extensions/cursor-grokbot-agents` 扩展的 BDK 本地服务，配置明确的机器人 allowlist。
- Codex 已连接该服务并能发现 `ask`、`check`、`call_tool`（或直接暴露的扩展工具）。

2026-10-26 维护环境核对：BDK 0.2.28 安装包包含此扩展，`call_tool → grokbot__list` 成功返回配置。不要假定其他版本提供相同接口；先检查安装包与工具 schema，再做版本迁移。

配置示意（机器人名必须替换成账号中已有的名字）：

```ts
import cursorGrokBotAgents from "@cursor/bdk/extensions/cursor-grokbot-agents";
export default cursorGrokBotAgents({ agents: ["Your Research Bot"] });
```

服务认证属于部署环境；不要把密钥提交到 skill 仓库。共享服务使用调用方认证，避免多人共享读取位置与机器人记忆。本机服务仅监听回环地址。

原维护环境使用 `~/gb-hub/bdk/start-serve.sh` 启动服务；该脚本是环境已有设施，不随本仓库分发，也不是所有用户都具有的路径。其他用户需按所安装 BDK 的文档配置服务。

## 核验依据

接口说明来自维护环境安装的 BDK 包：

- `docs/guides/grokbot-agents.md`
- `dist/extensions/cursor-grokbot-agents/tools/{ask,check,list}.js`
- 当前 MCP 的 `ask` / `check` / `call_tool` 工具定义

`list` 仅验证服务可达和配置可读，不能证明邮件、浏览器等权限已授予。
