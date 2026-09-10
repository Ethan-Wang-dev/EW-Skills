# 信息源和检索操作

脚本只访问公开 GitHub 数据。外部项目官网、文档与 Demo 可以补充定位；使用当前 session 可用的网页工具读取，不依赖某个付费搜索服务。

| 信息源 | 用途 | 已实现入口 | 注意事项 |
|---|---|---|---|
| Repository Search | 名称、描述、README 范围召回 | `--query` | 默认搜索不等于全文 README 搜索；按需加 `in:name,description,readme` |
| Topics | 不同命名下的领域项目 | `--topic web-clipper` | 不要求低星项目必须有 topic |
| Code Search | 特定实现或集成线索 | `--code-query` | 需要认证；索引不覆盖所有文件/分支，命中不证明产品完整 |
| Issues / PR | 真实问题、替代方案与功能讨论 | `--issue-query` | 默认包含 PR；可加 `is:issue`，请求中的功能不代表已实现 |
| README | 产品定位、使用流程、相关仓库链接 | 深读默认获取 | 输出开头和查询相关片段，保留行号、URL、blob SHA 和获取时间 |
| License / Release | 文件许可与最新正式发布信息 | 深读默认获取 | 404 是该端点未找到；403/429 是未知，不能写成“没有” |
| 最近提交、Issues / PR | 有日期的维护样本 | `--activity` | 样本不能直接证明维护者回复速度，也不是完整活跃度统计 |
| Awesome Lists / 关联仓库 | 发现命名差异较大的项目 | 阅读 README 的 `related_repositories`，再用 `--seed-repo` 验证 | 链接可能只是依赖或徽章；不自动当竞品 |
| Discussions / 官网 / 文档 / 代码上下文 | 进一步核验关键判断 | Agent 按需读取 | 脚本没有实现全站 Discussions、依赖图或网页抓取 |

## 查询设计与两阶段检索

从已澄清的目标用户和核心任务开始，通常先用 3–5 个短查询。GitHub 查询通常组合条件较严格，把整句中文需求译成一长串英文容易零命中。分别覆盖问题、任务动词、项目形态和同义词；不要总加 `open source`，也不要擅自添加 stars、语言、自托管或日期过滤。

按 [SKILL.md 的保存规则](../SKILL.md#research-storage)，先在当前工作目录确定本轮资料目录。将 `topic` 换成简短主题名；继续已有研究时复用原目录。后续命令沿用同一个 `scout_dir`，脚本位置仍相对于 Skill 安装目录解析。

```bash
scout_dir="$PWD/repo-scout-results/$(date +%F)-topic"
mkdir -p "$scout_dir"
python3 <skill_dir>/scripts/github_discover.py \
  --idea '个人网页剪藏，整理和回顾' \
  --query 'web clipper in:name,description,readme' \
  --query 'bookmark manager' \
  --topic web-clipper \
  --limit 20 --deep-limit 8 --output "$scout_dir/discovery-round1.json"
```

第一轮不足时，用 1–2 个针对性查询补充，不把所有查询同时广播到所有端点：

```bash
python3 <skill_dir>/scripts/github_discover.py \
  --code-query 'MutationObserver repo:owner/repo' \
  --issue-query '"web clipping" is:issue' \
  --secondary-limit 8 --deep-limit 3 --output "$scout_dir/discovery-round2.json"
```

这只是语法示例，不是固定产品需求。不同端点的 qualifiers 不完全通用。保留两轮的原始 JSON，按仓库 ID/名称合并候选再评估，不用第二轮覆盖第一轮。

验证已知候选时可直接指定仓库，避免重新搜索：

```bash
python3 <skill_dir>/scripts/github_discover.py \
  --seed-repo owner/repo --deep-limit 1 --activity --refresh \
  --output "$scout_dir/project-evidence.json"
```

`--seed-repo` 是定向核验，评测时不能拿预先输入正确答案的结果来宣称召回能力。

## 速度、预算和缓存

- 仅使用 Python 3.10+ 标准库。读取已有 `GITHUB_TOKEN` 或 `GH_TOKEN`，不把凭据写入输出。
- 默认 3 个并发线程、60 次网络请求预算；`--workers`、`--max-requests` 可调整。无认证时 Code Search 会明确跳过，不反复重试。
- `--limit` 为每个 repository 查询上限，`--secondary-limit` 为 code/issues 上限。支持分页，最多取 GitHub Search 可访问的前 1000 条；输出 `total_count`、`limited`、`incomplete_results`。
- `--deep-limit` 控制深读数量，`--metadata-limit` 限制从代码或 Issue 发现的仓库补全数量。深读选择依据相关性及查询覆盖，不依赖 stars。其余候选保留在 JSON 中。
- `--deep-limit 0` 只检索；`--no-readme` 只跳过 README，仍可核验 License/Release。`--activity` 会增加请求，适合少量候选。
- 默认缓存位置 `.github-oss-cache`；搜索缓存 15 分钟，其他元数据 1 小时。保存原获取时间并标记缓存命中；`--refresh` 绕过缓存，`--no-cache` 禁用缓存。
- 缓存原始响应、输出紧凑候选字段与证据摘要。不要把所有 README 原文直接塞进用户报告。

## 失败、去重和结论边界

读取 `search_metadata.status` 和每条 `query_runs`，不要只看 `count`。无结果的成功查询与认证失败、限流、预算耗尽是不同状态。全体检索失败时输出诊断 JSON 并以状态码 1 结束；部分失败会保留可用结果。

限流不作长时间等待；记录 HTTP 状态、remaining/reset、失败的查询。按可用配额缩小查询、复用缓存或使用当前可用的 GitHub 网页/搜索工具。若没有可用替代途径，报告覆盖受限；不要用模型记忆填充并伪装成检索结果。

自动合并同 ID、大小写和已知改名别名。fork、mirror 与多仓库产品只提供关系线索，需要人工/Agent 判别是否独立；公共可见不等于开源，License 不明和非商业/源码可见项目应分别标注。

检索分数是词面和结果排名融合，不是语义准确率。Issue/PR、代码命中只产生线索；需要打开相应文件、上下文或官方文档才能形成产品判断。达到主要工作流覆盖且连续补充查询无新相关项目时可以结束，同时披露搜索上限和盲区，不能宣称搜全 GitHub。
