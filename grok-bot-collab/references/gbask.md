# gbask 异步备用通道

适用于已有 webhook 接收机器人和本地 `gbask` 的环境；本仓库不包含 webhook 服务或凭证。

## 前置条件

`gbask` 在 PATH 中；原实现为 macOS Bash 脚本，使用 macOS `stat` / `sed` 语法。工作目录 `~/gb-hub/requests` 和 `~/gb-hub/results` 已创建；`~/gb-hub/webhook.env` 权限为 `600`，由用户配置 `GB_WEBHOOK_URL` 和 `GB_WEBHOOK_KEY`。不要读取或输出密钥。

接收端必须能够访问指定结果路径；云端机器人需要明确的本机访问或回传机制，不能假定共享文件系统。

## 提交与读取

```bash
gbask '自包含的只读任务，要求结果附来源链接'
gbask --status '<返回的任务 ID>'
gbask --wait '<返回的任务 ID>' 50
```

任务文本用安全的参数传递方式，不把生成文本拼成可执行 shell。

原发送端请求格式：

```json
{"schema":"gbask.v1","id":"<任务 ID>","task":"<任务>","result_path":"<本机结果文件绝对路径>","source":"mac-codex"}
```

接收端应按 ID 去重并只向约定结果目录写入结果，不能直接信任传入的任意路径。原发送端网络重试可能重复投递同一 ID。

结果文件 `~/gb-hub/results/<ID>.md` 第一行为：

| 状态 | 处理 |
| --- | --- |
| `status: pending` | 等待原任务，不重发 |
| `status: done` | 读取结果并核对来源 |
| `status: failed` | 报告失败原因 |
| `status: needs-user-confirm` | 报告所缺授权，停止自动继续 |

原 `--wait` 只判断首行是否仍为 pending，退出码为零不代表 done；必须检查首行。超时不取消任务。提交报错也可能发生在接收端已收到请求之后，重试前检查同一 ID 的结果。

此格式依据已有发送脚本与 Grok Bot 侧 `codex-gb-collab` 指引整理。接收机器人通过指定 machineId 的 Shell 写回 Mac；webhook 正文保持简短，原指引提示约 4000 字符以上可能截断，大内容改用文件。本次未端到端测试 webhook 接收与回传。
