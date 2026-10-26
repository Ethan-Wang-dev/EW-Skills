---
name: codex-offload
description: Let Grok Bot delegate substantial coding, document, or data tasks to a connected Mac running codex-hub, inspect independent acceptance checks, request bounded revisions, and return a verified result. Requires Grok Bot machine tools and an existing codex-hub installation.
---
# Grok Bot → Codex

你负责明确任务、写验收标准、判断结果与汇报；Codex 执行，`codex-hub/run.sh` 独立运行验收。适用于已有 codex-hub 的 Grok Bot 环境，不是在 Codex 内再次启动 Codex 的通用指令。

## 选择任务与机器

- 适合委派：较大的代码修改、代码评审、数据处理、长文档分析或初稿。简单问答直接处理。
- 需要 Grok Bot 连接器或实时浏览器的部分，先由 Grok Bot 获取必要资料，再传经过筛选的输入。不要让 Codex 把同一任务再交回 Grok Bot。
- 发布、发送、付款等对外操作不包含在委派中；只生成草稿或本地改动。用户已有授权可以继续适用，但不得扩大范围。
- 用 `ListMachines` 找到装有 codex-hub、`connected: true` 的 desktop。所有机器命令都通过带该 `machineId` 的 `Shell` 执行。离线或缺少工具时说明依赖，不假定本地 shell 就是用户的 Mac。
- 只调用已部署的 `~/codex-hub/run.sh`。不修改运行器、凭证或权限配置，不绕开它直接执行 Codex。

## 规划与派发

1. 写清目标、输入、输出文件、格式、边界情况和允许修改范围。对大任务拆成可独立验收的部分。
2. 提供至少一条自己确定的 `--check`。退出码 0 为通过，但文件存在检查只能证明产物存在，不能证明内容正确。不要只运行由 Codex 自己编写的验证脚本；补上独立断言。
3. 用 `run.sh models` 查看部署实际支持的模型与强度，用 `run.sh limits <自己的 Bot ID>` 查看限额。优先运行器默认值或 `--auto normal`；用户指定的模型优先。不要假定订阅额度或模型档位固定，也不要因某个强度名称自动启用子代理。
4. 任务 ID 只含字母、数字、`.`、`_`、`-`，长度不超过 60；不要以 `-rN` 或 `-review` 结尾。`--bot` 与 `--reply-to` 中的 agent ID 必须一致，使用自己真实的 ID。
5. 按 [调用与回传](references/runner.md) 提交一次，保存任务 ID。运行中等待现有任务，不创建重复任务。

命令模板（尖括号内容需替换；任务正文使用带引号的 heredoc）：

```bash
~/codex-hub/run.sh --id '<任务ID>' --type code --auto normal --timeout 10 --bg \
  --bot '<自己的BotID>' --reply-to 'agent:<自己的BotID>;ctx:<简短上下文>' \
  --check '<独立验收命令>' <<'TASK'
目标：……
输入：……
交付物：scratch 模式写入 out/……
允许修改与限制：……
TASK
```

后台模式依赖已配置的结果回传。收到回调后执行 `run.sh status <ID>`；回调不可用时按约定间隔查询同一 ID，明确告知结果仍在等待。前台调用与长输入见参考文档。

## 验收、返工与收尾

- 先读运行器状态和 checks，再看 Codex 自报。`ok` 且检查通过后仍抽查关键 diff/产物、`unfinished`、`risks`；自报 completion 不是 done 或有未完成需求时不能宣布完成。
- `unverified` 不等于通过：补充检查或如实报告未验收。`check_failed` 时给出具体失败证据与期望，不只说“再检查一下”。
- 用 `run.sh revise <上一轮ID>` 继续原工作目录与会话；最多返工两次，部署上限更低时遵循更低上限。可用 `--check` 添加抽查发现的验收条件。
- 需要额外审查时可用 `run.sh review <ID>`，只采纳能在产物中核实的问题；它是额外模型调用，不能代替独立检查。
- 最后一轮执行 `run.sh verdict <ID> accepted|rejected '<原因>'`。回报做了什么、怎么验收、返工情况、剩余问题，并按需取回文件。
- 权限拒绝、额度不足、用户暂停或返工用尽时停止自动重派；状态与恢复规则见 [调用与回传](references/runner.md)。

任务和结果中不包含密钥、无关私人数据或微信原始聊天。自动安全检查拒绝时报告原始原因，不改写命令、冒用 Bot ID 或改配置绕过。合并、push、部署及其他对外动作须在用户明确授权范围内单独执行。
