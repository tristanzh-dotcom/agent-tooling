### ☀️ 次日启动胶囊 (Boot Prompt)
请在明天开启新对话时，直接复制以下指令发给系统：

```text
请静默读取并完全理解当前目录下的 `HANDOVER_ecosystem_audit_20260602.md`。
1. 请将本对话的逻辑分支锁定为：【生态审计治理基线】，并在你回复的第一句话使用 Markdown 的 H1 标题 (`# 生态审计治理基线 工作流重启`) 输出，以便系统自动重命名此对话。
2. 在执行任何操作前，请简要复述当前的【核心卡点】与【下一步行动】。等待我的确认后，再开始执行。
```

## 第一性原理与项目上下文

本轮工作的核心目的不是做单一功能开发，而是把 `/Users/tristanzh/agent` 下多个 Codex-managed 项目从松散、脏工作区、无统一质量入口的状态，推进到可审计、可复现、可回滚判断的 release-ready 基线。DeepSeek R1 到 R6 的审计轨迹为：R1 4.6 -> R3 7.25 -> R5 8.25 -> R6 8.50。

本轮坚持的边界：

- 事实核查优先，不盲从外部审计结论。
- SDD/TDD 优先，修复前先明确接口和失败测试。
- 不擅自处理未批准的 untracked/历史/跨项目文件。
- 项目业务边界与 `/Users/tristanzh/agent/web` 发布边界分离。
- 质量门应证明项目可复现，而不是靠手工清理掩盖问题。

## 今日完成事项

- PetRelatedServices：
  - 建立 Pet 质量入口并提交：`4fecaf0 chore: establish pet quality gate`。
  - 新增 `package.json`、`pyproject.toml`、`requirements.txt`、`.github/workflows/quality.yml`。
  - `requirements.txt` 版本来自 Pet 当前 `venv` 的实际 `pip freeze`，不是估算。
  - 清理废弃 PPT 分支和 rollback helper，并提交记录：`224e0c1 chore: record abandoned pet cleanup`。
  - 删除了废弃文件 `make_ppt.py`、`rollback_agent03.sh` 及明确相关桌面产物。

- Codex-Ops：
  - 提交 Pet 质量门验证：`6e2fb47 chore: verify pet quality gate`。
  - ecosystem quality gate 改为使用 Pet 统一入口 `npm test`。
  - 记录 root Pet boundary patch：`2567d13 docs: record root pet boundary patch`。

- Passenger-Vehicle-Intel：
  - 修复 PVI CI 中 deterministic npm 安装：`e9ce40c fix: use deterministic npm ci in pvi workflow`。
  - 修复 JLR adapter 测试污染 tracked snapshot：`8d78228 fix: keep jlr tests from mutating tracked snapshots`。
  - 根据 R6 新信号继续修复 JLR collect CLI 写入 tracked `latest_snapshot.json` 的根因：`4979184 fix: keep jlr collect snapshots in runtime output`。
  - `jlr-sales/src/collect.js` 与 `workflows/jlr-sales/src/collect.js` 默认输出改为 `.runtime/latest_snapshot.json`。
  - 如需有意刷新 tracked 手动快照，改用 `JLR_SNAPSHOT_PATH=data/latest_snapshot.json npm run collect`。

- Local-photo-model 与 web：
  - Local-photo-model 已修复 Agent04 搜索结果在无缩略图时退化成文字描述的问题：`b6c5123 fix: render agent04 photos when thumbnails are missing`。
  - web 已修复 Agent03 工作流卡片状态隔离问题：`e96542e fix: isolate agent03 workflow result state`。
  - web 还有 `57bbbc5 fix: write jlr runtime snapshots outside tracked data` 和 `378a6cd test: track agent04 preview url static version`。

- 验证记录：
  - Pet `npm test`：Node 35/35，Python 58/58 通过。
  - Codex-Ops tests：11 passed。
  - PVI CI 等价检查：root Python 43 passed，domestic workflow 33 passed，root JLR 33 passed，workflow JLR 34 passed，hardware dashboard 5 passed。
  - Codex-Ops `ecosystem_quality_gate.py --mode audit`：OK。
  - Codex-Ops `ecosystem_quality_gate.py --mode verify`：OK。

## 已作出的关键决策

- 接受 DeepSeek R6 的 `8.50/10` 评分判断。Pet clean baseline、root `AGENTS.md` bare edit、Medical PDF 作为 Phase 6 任务这三点与本地事实一致。
- 对 R6 的 PVI `latest_snapshot.json` 新信号没有当作偶发处理，而是做根因排查。结论：R4/R5 主要覆盖 adapter 注入路径，R6 额外触发 collect CLI，暴露了之前未覆盖的硬编码写入点。
- PVI collect CLI 的正确接口是：默认写 `.runtime/`，只有显式 `JLR_SNAPSHOT_PATH` 才写入 tracked/manual snapshot。这样保留手动刷新能力，同时避免审计/测试污染仓库。
- Pet 的 `make_ppt.py` 不属于 Pet 业务边界，且 TZ 明确为废弃项目残留，因此物理删除而非提交。
- `rollback_agent03.sh` 是旧备份方案分支，当前治理方向不再需要可执行 rollback helper；确认不影响现有项目后物理删除，并在 Pet 文档中记录。
- root `/Users/tristanzh/agent/AGENTS.md` 不是 git 仓库内文件，但 R6 已接受它作为已批准治理事实。

## 未解决的风险/报错

- 当前收工前重新扫描发现若干 dirty 项。它们出现在我最后一次“8 个项目干净”确认之后，可能来自 DeepSeek/R6 审计、其他工作流或同步清理动作。明天不要直接恢复，先确认归属：
  - `web`：`.gitignore`、`server.mjs`、`scripts/`、`tests/cd-watcher.test.mjs` 有未提交变更。
  - `Local-photo-model`：旧 handover 文件删除。
  - `Codex-Ops`：旧 handover 文件删除。
  - `Passenger-Vehicle-Intel`：旧 handover 文件删除。
  - `Stratigic-AGI-System`：旧 handover 文件删除。
  - `PetRelatedServices`：`HANDOVER_agent03_cleanup_20260531.md` 删除。
  - `Medical`：多份 PDF 被修改，符合之前 ecosystem verify 会重写 PDF 产物的已知模式，但本次归属仍需明天先确认。
- Medical PDF 幂等性仍是 Phase 6 独立任务，不阻塞 R6 基线，但未来审计会继续看到这个运行产物风险。
- root 目录不是 git 仓库，本文件和 root `AGENTS.md` 都不会被 git 版本控制保护。
- R6 后已达到 release-ready，但还没有进入 Phase 5/6 的去重、canonical 迁移和 Medical PDF 幂等修复。

## 下一步行动

1. 先读取 `/Users/tristanzh/agent/GLOBAL_MODEL_ROUTING_RECORD.md` 和 `/Users/tristanzh/agent/AGENTS.md`。
2. 运行工作区状态扫描：

```bash
for d in web Local-photo-model Codex-Ops Passenger-Vehicle-Intel Medical Webstyle-editor Stratigic-AGI-System PetRelatedServices; do
  printf '[%s]\n' "$d"
  git -C "$d" status --short
done
```

3. 对当前 dirty 项逐一确认归属，不要直接恢复：
   - 若是 R6/其他工作流有意变更，按项目流程 SDD -> TDD -> 实现 -> 验证后提交。
   - 若是 ecosystem verify 产物，确认只恢复运行产物，不恢复用户变更。
4. 如果要继续提升分数，建议 Phase 6 顺序：
   - 先处理 Medical PDF 幂等性，让 quality gate 不再改 tracked PDF。
   - 再处理 PVI 和 web 的剩余运行产物/发布边界一致性。
   - 最后做跨项目去重和 canonical 迁移。
5. 复验命令优先级：

```bash
cd /Users/tristanzh/agent/Codex-Ops
python3 tools/ecosystem_quality_gate.py --mode audit
python3 tools/ecosystem_quality_gate.py --mode verify
```
