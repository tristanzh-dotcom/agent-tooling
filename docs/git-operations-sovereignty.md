# Git Operations Sovereignty

## §1 规则

所有 Git 写操作（commit / push / pull / stash / rebase）的唯一控制面是 Agent08 Git Control（`http://127.0.0.1:3000/agent08`）。业务 agent 的 Codex 工作流严禁在本地直接执行 `git commit`、`git push`、`git pull`、`git stash`、`git rebase`。

## §2 安全单点

Agent08 的 SafetyGate 是生态内唯一的 Git 安全门禁。所有 mutation 必须经过 preflight snapshot、confirmation token、当前状态复核。绕过 Agent08 直连 repo 执行 git 写命令视为治理违规。

## §3 自监控无豁免

agent08-gitboard 自身受同等规则约束。self-mutation 需显示 running-code 警告。

## §4 Codex 工作流的合规行为

| 场景 | 旧行为（禁止） | 新行为（要求） |
|---|---|---|
| 功能开发完成，需提交 | `git commit -m "..."` | 打开 `/agent08` → 点击该 repo 的 `commit` 按钮 |
| 需推送到 GitHub | `git push` | 打开 `/agent08` → 点击该 repo 的 `push` 按钮 |
| 需拉取最新 | `git pull` | 打开 `/agent08` → 点击该 repo 的 `pull` 按钮 |
| 需 stash+rebase | 手动操作 | 打开 `/agent08` → 点击 `stash+rebase` 按钮 |

## §5 TZ 手动豁免

TZ 在终端中直接执行的 git 命令不受此协议约束。此协议约束的是 Codex 工作流中的自动化 git 行为。

## §6 检测方法

每次审计或 handover 时，应检查被监控 repo 的 git log 中是否存在未经 Agent08 的 commit。任一 repo 中出现非 TZ 手动执行的 git 写操作，视为合规缺口。
