### ☀️ 次日启动胶囊 (Boot Prompt)
请在明天开启新对话时，直接复制以下指令发给系统：

```text
请静默读取并完全理解当前目录下的 `HANDOVER_vibe_clean_20260602.md`。
1. 请将本对话的逻辑分支锁定为：【Vibe Clean 技能】,并在你回复的第一句话使用 Markdown 的 H1 标题 (`# Vibe Clean 技能 工作流重启`) 输出，以便系统自动重命名此对话。
2. 在执行任何操作前，请简要复述当前的【核心卡点】与【下一步行动】。等待我的确认后，再开始执行。
```

## 第一性原理与项目上下文

本轮工作主题是 Vibe Clean skill 开发与上线验证。核心目标是在 `/Users/tristanzh/agent` 审计结束后，用严格的 dry-run first + 精确确认词机制，对工作区内可再生垃圾、过期状态快照和审计历史产物做物理级清理，同时保护 `.git/`、`.env*`、虚拟环境、`node_modules/` 主体、技能文件和当天 handover。

必须保持的边界：

- 在 TZ 未给出 dry-run 后的精确确认词 `确认执行清除指令` 前，禁止任何删除或移动。
- dry-run 只对紧随其后的最新用户回复有效；中间若插入其他话题，必须重新 dry-run。
- Vibe Clean 不替代业务审计，不修改业务项目代码。

## 今日完成事项

核心文件：

- `/Users/tristanzh/agent/.ai_skills/vibe-clean/SKILL.md`
- `/Users/tristanzh/agent/.ai_skills/vibe_clean_skill.md`
- `/Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py`
- `/Users/tristanzh/agent/.ai_skills/vibe-clean/tests/test_vibe_clean_gc.py`

已完成：

- 将 Vibe Clean 从理论草案推进到 v3 生产可用级别。
- 按 SDD/TDD 流程先定义契约测试，再实现脚本，再同步 skill 文档。
- 底层脚本支持 `dry-run` / `execute` 两阶段 CLI，执行端强校验 `--confirm "确认执行清除指令"`。
- 清理规则扩展到 `.bak`、`temp_*`、`test_draft_*`、`debug_*.log`、`*.tmp.log`、`.pytest_cache/`、`__pycache__/`、`*.pyc`、`.vitest/`、`node_modules/.cache/`、`.DS_Store`、`*.swp`、`*.swo`、`*~`、过期 handover、`pure_context.md`、非最大轮次 `deepseek_audit_feedback_r*.md`。
- 免疫边界加入 `.git/`、`_archive_legacy/`、`.ai_skills/`、`.env*`、`.venv/`、`venv/`、`node_modules/` 主体、`SKILL.md`、`*_skill.md`、`audit_artifact_cleanup_catalog.md`、当天 handover。
- 修复 symlink 安全边界：删除目标本身是符号链接时只 `unlink()`，不递归删除链接目标。
- 删除 `temp_*.log` 的重复死代码分支。
- 真实 `/Users/tristanzh/agent` 已执行过一次 supervised dry-run，经 TZ 精确确认后执行清理；随后复核曾显示清单归零。

验证：

```bash
python3 /Users/tristanzh/agent/.ai_skills/vibe-clean/tests/test_vibe_clean_gc.py
```

最后一次测试结果：

```text
Ran 7 tests in 0.388s
OK
```

## 已作出的关键决策

- 接受 DeepSeek 审计中关于清理覆盖不足、免疫边界不足、symlink 风险的建议；拒绝把 `/var/folders` 系统临时目录纳入默认 Vibe Clean，因为它违反“只扫描当前项目目录”的边界。
- `node_modules/` 主体免疫，但 `node_modules/.cache/` 作为可再生缓存允许删除。
- `deepseek_audit_feedback_r*.md` 采用版本保留逻辑：多个轮次只保留最大 rN；只有一个轮次则保留。
- `audit_artifact_cleanup_catalog.md` 显式免疫，避免被审计通配规则误删。
- `.gitignore` 只作为清理后建议，不自动修改，避免跨项目策略污染。
- 当前保留本机硬编码脚本路径 `/Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py`，因为这是本机个人 skill；迁移到通用 skill 包时再改相对路径解析。

## 未解决的风险/报错

- 收工前再次只读 dry-run 时，清单不再为空，显示以下待清理目标：

```json
{
  "delete": [
    "Codex-Ops/.pytest_cache",
    "Local-photo-model/.pytest_cache",
    "Medical/.pytest_cache",
    "Passenger-Vehicle-Intel/.pytest_cache"
  ],
  "archive": [
    "web/HANDOVER_20260530.md",
    "web/pure_context.md"
  ]
}
```

- 上述清单尚未执行清理；因为当前用户触发的是“收工”，按 handover 流程只生成交接文件，不再追加执行清理。
- `/Users/tristanzh/agent/.ai_skills/vibe-clean/SKILL.md` 与 `/Users/tristanzh/agent/.ai_skills/vibe_clean_skill.md` 同时存在。前者是更接近标准 skill 包结构的文件；后者是早期本地技能说明文件。明天需要确认是否保留双文件，或将 `vibe_clean_skill.md` 归并/废弃。
- 硬编码路径仍是 P2 遗留项；若未来迁移到其他主机或 CI，应改为 skill 相对路径或 `$SKILL_HOME` 解析。

## 下一步行动

1. 首先读取本文件和 `/Users/tristanzh/agent/.ai_skills/vibe-clean/SKILL.md`，确认当前 canonical skill 文件是哪一个。
2. 重新运行只读 dry-run：

```bash
python3 /Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py \
  --root /Users/tristanzh/agent \
  --today "$(date +%Y%m%d)" \
  --mode dry-run \
  --format markdown
```

3. 将 dry-run 清单展示给 TZ，等待精确确认词 `确认执行清除指令`。不要自动执行。
4. 若 TZ 确认，再执行：

```bash
python3 /Users/tristanzh/agent/.ai_skills/vibe-clean/scripts/vibe_clean_gc.py \
  --root /Users/tristanzh/agent \
  --today "$(date +%Y%m%d)" \
  --mode execute \
  --confirm "确认执行清除指令"
```

5. 清理完成后复核 dry-run 是否归零；再决定是否处理双 skill 文件和硬编码路径问题。
