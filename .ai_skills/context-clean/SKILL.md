---
name: context-clean
description: "Use only when the user enters the exact command 执行context clean for logical context isolation without filesystem cleanup."
---

# Context Clean 逻辑上下文隔离

## 核心原则

- 唯一触发命令：`执行context clean`。
- 这是逻辑上下文过滤，不是物理文件 GC。
- 不删除、不移动、不归档任何物理文件。
- 不使用物理 GC 的执行确认词，也不调用 `vibe-clean` 的 GC 脚本。
- 协议源：`/Users/tristanzh/agent/web/docs/vibe-clean-protocol.md`。

## 执行边界

读取协议源后执行其中的上下文隔离流程：

- 确认不会进行物理删除。
- 识别 core truth files 与 environmental noise。
- 在对话中激活 context filter。
- 如果项目已有上下文快照脚本，可按协议生成或更新 `pure_context.md`；否则只列出 truth set。
- 后续推理默认使用 `pure_context.md` 或列出的 truth files。

## 非目标

- 不清理 `.bak`、`__pycache__`、`temp_*` 等文件。
- 不归档 `pure_context.md`。
- 不移动旧 handover 文件。
- 不扫描并修改跨项目文件。
- 不把 `执行context clean` 映射到 `执行vibe clean`。

## 输出语句

完成后按协议报告：

```text
Vibe clean complete.
Core truth source:
- ...

Ignored by default:
- ...

Safety posture:
- no deletion
- patch-only edits
- state drift suspended
- tests before implementation
```
