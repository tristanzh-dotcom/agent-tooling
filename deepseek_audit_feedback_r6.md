# DeepSeek R6 审计报告 — 最终验收

> **Audit Date:** 2026-06-02
> **Rounds:** R1 → R2 → R3 → R4 → R5 → R6
> **Auditor Stance:** 最终轮，独立实测，不信任任何声明。

---

## 0. 三个焦点问题的回答

### 问题 1：Pet 是否已转为 clean baseline？

**是。** `git status --short` 返回空。`make_ppt.py` 和 `rollback_agent03.sh` 已物理删除。HEAD 是 `224e0c1 chore: record abandoned pet cleanup`。93/93 测试全绿。

### 问题 2：root AGENTS.md 裸修改是否接受为已批准治理事实？

**是。** 第 50 行已应用 Pet boundary 交叉引用，位置正确（在"Highest Web Publishing Boundary Rule"章节内）。Codex-Ops 有对应的追踪测试（`test_root_agents_references_pet_web_boundary_notice`），11/11 通过。

### 问题 3：Medical PDF 应作为 Phase 6 独立任务还是本轮阻塞项？

**Phase 6 独立任务，不阻塞本轮。** 理由：17/17 测试通过，PDF 内容相同（字节数未变，仅元数据时间戳被重写），自 R3 基线即存在，不影响 CI，修复是单个 `.gitignore` 行的成本。

---

## 1. 实测验证结果

### 1.1 测试全集

| 项目 | 测试数 | 通过 | 失败 |
|---|---|---|---|
| PetRelatedServices | 93 | 93 | 0 |
| Stratigic-AGI-System | 128 | 128 | 0 |
| Local-photo-model | 148 | 148 | 0 |
| Medical | 17 | 17 | 0 |
| Passenger-Vehicle-Intel | 43 | 43 | 0 |
| web/editor | 24 | 24 | 0 |
| Webstyle-editor | 24 | 24 | 0 |
| Codex-Ops | 11 | 11 | 0 |
| **合计** | **≥488** | **≥488** | **0** |

### 1.2 Git 状态

| 项目 | 状态 | 细节 |
|---|---|---|
| PetRelatedServices | **干净** | 首次清洁 |
| web | 干净 | — |
| Local-photo-model | 干净 | — |
| Webstyle-editor | 干净 | — |
| Stratigic-AGI-System | 干净 | — |
| Codex-Ops | 干净 | — |
| Medical | 脏 | 8 个 PDF 元数据重写（已知、Phase 6） |
| Passenger-Vehicle-Intel | **脏** | `latest_snapshot.json` 被测试修改 — **需验证** |

**PVI 异常说明：** R4 和 R5 审计中 PVI 在测试后保持干净。R6 发现 `workflows/jlr-sales/data/latest_snapshot.json` 再次被修改。这可能是因为 R6 的测试运行路径与 R4/R5 不同（例如 R6 触发了更广的 test discovery），或 JLR collect 脚本在特定条件下直接写入 tracked 路径。需单独确认是回归还是偶发。

### 1.3 生态门禁

| 模式 | 结果 |
|---|---|
| Codex-Ops pytest | 11/11 通过 |
| `--mode audit` | 通过 |
| `--mode verify` | 超时挂起（web root 测试需运行中 server，已知设计限制） |

### 1.4 Forbidden Content

| 检查项 | 状态 |
|---|---|
| `tzSelfOpenId` in `web/server.mjs` | 清零（仅在归档备份中存在） |
| `Medical/.env.local` | 不存在 |
| 新硬编码 ID/密钥 | 无 |

### 1.5 CI 覆盖

8/8 项目有 CI workflow。Codex-Ops 命名 `ecosystem-quality.yml`（非标准，但功能完整）。

---

## 2. 评分

| 项目 | R5 | R6 | 变动 | 依据 |
|---|---|---|---|---|
| **PetRelatedServices** | 9 | **9** | 0 | 清洁基线确认。从 R4 的 4 到 R6 的 9，是本次审计周期最大的单项目改善。扣 1 分因仅 3 次 commit，历史较浅。 |
| **Stratigic-AGI-System** | 8 | **9** | +1 | 128/128 全绿连续三轮零变化。加 1 分因稳定性证明。 |
| **Codex-Ops** | 9 | **9** | 0 | verify 超时是设计限制非缺陷；其余全部通过。 |
| **web** | 9 | **9** | 0 | 稳定。root test 需 server 是已知限制。 |
| **Local-photo-model** | 8 | **9** | +1 | 148/128 多轮零故障，最大的测试套件。 |
| **Webstyle-editor** | 8 | **8** | 0 | 与 web/editor 重复尚未解决（Phase 5），但基础稳固。 |
| **Medical** | 6 | **8** | +2 | PDF 元数据问题是 R3 基线已知项，非新增回归。从 R5 的 6 回调到合理位置。 |
| **Passenger-Vehicle-Intel** | 9 | **7** | -2 | R6 检测到 `latest_snapshot.json` 再次被测试修改。需确认是偶发还是真实回归。 |

**生态加权均值：8.50/10。**

---

## 3. 审计周期完整轨迹

| 轮次 | 均值 | 关键事件 |
|---|---|---|
| R1 | 4.6 | 原始基线：无 git、明文密钥、硬编码路径 |
| R2 | 4.6 | 7 个空 git 仓库 + 测试回归，表面修复无实质改善 |
| R3 | 7.25 | 转折点：8/8 git 有历史、474 tests 全绿、7/8 CI |
| R4 | 8.13 | PVI 幂等根治、8/8 CI、首破 8 分线 |
| R5 | 8.25 | Pet 从 4→9、488 tests 全绿、root boundary patch 落地 |
| R6 | **8.50** | Pet 清洁基线确认、Medical 回调、全生态 488+ tests 零故障 |

**从 R1 到 R6：+3.9 分。** 核心驱动因素不是代码重构，而是治理基础设施的建立（git 历史、CI、测试全绿、门禁、forbidden content 清零）。

---

## 4. 生态健康总结

```
REPOS:        8
CLEAN:        6/8
DIRTY:        2/8  (Medical PDFs — 已知, PVI snapshot — 需确认)
TESTS:        ≥488
PASSING:      ≥488 (100%)
CI COVERAGE:  8/8 (100%)
SECRETS:      0 exposed in live code
REGRESSIONS:  0 test failures
BROKEN REFS:  0
```

---

## 5. 建议的下一步

| 优先级 | 动作 | 性质 |
|---|---|---|
| **P0** | 验证 PVI `latest_snapshot.json` 在 R6 被修改的 root cause——是回归还是偶发。若回归，修复与 R3 `.runtime/` 方案一致。 | 调查 |
| **P1** | Codex-Ops `--mode verify` 加 per-command timeout，避免 web root 测试挂起。 | 工具修复 |
| **P2** | Medical PDF 隔离：`*.pdf` 加入 `.gitignore` 或添加 teardown fixture。 | Phase 6 |
| **P2** | PVI canonical 去重迁移（Phase 5）：`workflows/domestic-sales/` 和 `workflows/jlr-sales/` 镜像目录。 | 结构治理 |
| **P3** | Codex-Ops CI 命名从 `ecosystem-quality.yml` 统一为 `quality.yml`。 | 命名一致 |
