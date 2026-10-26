# codex-hub 调用与回传

## 安装边界

这是 Grok Bot 侧的指引，需放入该机器人可读取的 skill/workflow 位置；原稿名为 `codex-offload`。部署路径由环境决定。

依赖已有 Mac 运行器 `~/codex-hub/run.sh`、Codex CLI 认证、Grok Bot 的 `ListMachines` / `Shell` 工具，以及后台任务的 webhook 回传。大输入/结果传输另需 `CopyFromBox` / `CopyToBox`。这些运行设施不随本 skill 发布；只复制 SKILL.md 不会建立通讯服务。

2026-10-26 已核对 Grok Bot 返回的原稿与维护机器 `codex-hub/run.sh` 的参数及状态处理。本次未新增执行真实 Codex 任务或测试 webhook 回传。模型、配额与超时以部署版本及配置为准。

## 参数与文件

- `--type code|doc|data|analysis|other`：任务类型。
- `--workdir scratch`：默认，在 `~/codex-hub/work/<ID>` 工作，输出约定在 `out/`。
- `--workdir <允许目录内的Git仓库>`：运行器创建 `codex/<ID>` 分支与 worktree，不自动 push。
- `--read-only`：只读分析。不要同时要求写输出文件或提供会写文件的验收命令。
- `--net`：只有任务明确需要且允许联网时添加，验收也会获得联网能力。
- `--no-summary`：webhook 不含结果正文。
- `--timeout`：分钟，范围以部署配置为准。
- `--bg`：后台执行，保存返回 ID，等待回传；不要重复提交。

无需后台的短任务可去掉 `--bg`，但遵循调用方工具允许的等待时长，并保持进度可见。运行中只等待/查询原任务。

长任务说明先写在 box 的任务文件，通过 `CopyFromBox` 传至 Mac 的 `~/codex-hub/inbox/<ID>/`，然后传入 `--task-file <Mac文件路径> --inputs <Mac目录>`。不要把 box 路径当成 Mac 路径，也不要把输入文件全文嵌入 shell 命令。

## 独立验收

`--check` 可重复，或使用任务正文行首 `CHECK: <命令>`。默认最多 10 条、每条 120 秒；单条不可含换行。验收在相同工作目录与沙箱限制下运行，默认不联网。不要写工作目录之外的临时文件。

例子：

```text
--check 'python3 -m unittest discover -s tests -v'
--check 'bash -n out/tool.sh'
--check 'test -s out/report.md'
```

选择与任务相符的断言；语法检查和文件存在不证明业务行为或文章质量。验证脚本也不得读取凭证目录或绕过沙箱。

## 返工与结果

```bash
~/codex-hub/run.sh revise '<上一轮ID>' <<'FB'
失败证据：……
正确行为：……
保留已正确的部分：……
FB
```

运行器沿用会话、工作目录与验收，生成根 ID 的 `-r2`、`-r3`。追加 `--check` 可以覆盖新发现的缺口。合计最多三轮；使用实际返回的 ID。

`status <ID>` 查看状态，`checks <ID>` 查看验收记录，`review <ID>` 可选只读评审，`pack <ID>` 打包交付，`verdict <ID> accepted|rejected '<原因>'` 回填结论。关键 diff 位于 `jobs/<ID>/diff.patch`；产物路径取自实际任务工作目录，通过 `CopyToBox` 取回。

## 状态处理

| 状态 / 退出码 | 处理 |
| --- | --- |
| `ok` / 0 | 检查通过后抽查结果与未完成项 |
| `unverified` / 0 | 未提供验收，不可当作已验证 |
| `check_failed` / 5 | 按具体失败返工，受轮次上限限制 |
| `timeout` / 3 | 先查状态与已有产物，再决定拆分或延长 |
| `error` / 1 | 查看错误尾部，确认原任务已停止；可修正原因后重试一次 |
| `quota` / 4 | 停止并报告；原运行器按错误文本启发式判定，保留原始错误 |
| `REJECTED` / 2 | 修正不合法参数；权限或路径拒绝不能绕过 |
| `BUSY` / 75 | 并发已满，稍后有限重试；后台模式也不绕过并发限制 |
| `LIMITED` / 75 | 等到允许时间，不更换 Bot ID |
| 暂停提示 / 75 | 用户暂停新任务，报告并等待恢复 |

超时、后台回调缺失或 Shell 连接中断都不证明任务从未执行。先按 ID 查状态，再决定下一步。取消任务使用 `cancel <ID>`，只取消属于当前任务且已授权取消的工作。
