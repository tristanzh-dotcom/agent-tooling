---
name: vibe-clean
description: "Use only when the user enters the exact command 执行vibe clean for Vibe Clean file garbage-collection dry-run."
---

# Vibe Clean 文件 GC 与状态重置

## 核心原则

- 唯一 dry-run 触发命令：`执行vibe clean`。
- 任何其他近似表达都不得触发 Vibe Clean 文件 GC dry-run。
- 只根据当前目录的物理文件状态判断清理目标，不读取 `pure_context.md` 或历史上下文作为依据。
- **必须先执行 dry run 并展示拟清理清单；未经 TZ 确认，禁止删除或移动任何文件。**
- 只有 TZ 回复精确确认词 `确认执行清除指令` 后，才允许执行物理清理。
- dry run 只对紧随其后的最新用户回复有效；若中间出现其他回复、等待、换题或新任务，必须重新 dry run。
- 清理范围是当前工作目录的递归扫描；不得跨项目扫描。
- 底层执行必须使用本技能配套脚本：`/Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py`。
- 若删除目标本身是符号链接，只删除链接本身，不递归删除链接指向的目标。

## 免疫边界

以下路径或文件禁止触碰：

- `.git/` 及其内部所有内容。
- `_archive_legacy/` 内部已有归档内容。
- `.ai_skills/` 内所有技能文件。
- `.env`、`.env.*`。
- `.venv/`、`venv/`。
- `node_modules/`，但 `node_modules/.cache/` 是可再生缓存，可进入删除清单。
- `SKILL.md`、`*_skill.md`。
- `audit_artifact_cleanup_catalog.md`。
- 当天生成的 `HANDOVER_*_YYYYMMDD.md`。
- 未命中清理规则的业务源码、文档和配置。

## 清理目标

删除：

- `*.bak`
- `temp_*`
- `test_draft_*`
- `debug_*.log`
- `temp_*.log`
- `*.tmp.log`
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `.vitest/`
- `node_modules/.cache/`
- `.DS_Store`
- `*.swp`
- `*.swo`
- `*~`
- `deepseek_audit_feedback_r*.md` 中非最大轮次的历史审计快照；若只有一个轮次则保留。

归档到 `_archive_legacy/`：

- 非当天的 `HANDOVER_*.md`

不归档：

- `pure_context.md`。这是 `context-clean` 的上下文隔离产物，生命周期由 `执行context clean` 管理。

## 执行步骤

### Step 1: Dry Run

在当前项目根目录运行：

```bash
python3 /Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py \
  --root "$PWD" \
  --today "$(date +%Y%m%d)" \
  --mode dry-run \
  --format markdown
```

将命令输出原样展示给 TZ。然后停止，等待 TZ 回复精确确认词：

```text
确认执行清除指令
```

任何其他回复都不是确认。不得运行 GC。

### Step 2: Execute

仅当 TZ 的最新回复精确等于 `确认执行清除指令` 时，在同一项目根目录运行：

```bash
python3 /Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py \
  --root "$PWD" \
  --today "$(date +%Y%m%d)" \
  --mode execute \
  --confirm "确认执行清除指令"
```

执行后简要报告删除和归档已完成。

如果清理清单显示某类可再生产物反复出现，可以建议 TZ 将该类型加入项目 `.gitignore`。不得自动修改 `.gitignore`。

## 禁止事项

- 禁止把"确认执行""可以""OK""执行吧"等近似表达当作确认。
- 禁止跳过 dry run。
- 禁止手写 `rm` 或 `mv` 替代配套脚本。
- 禁止清理 `_archive_legacy/` 内部文件。
- 禁止清理 `.env*`、虚拟环境或 `node_modules/` 主体目录。
- 禁止跟随符号链接递归删除链接目标。
- 禁止因为文件看起来无用而扩大清理规则。
