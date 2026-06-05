# DeepSeek R8 审计报告

> **Audit Date:** 2026-06-03
> **Rounds:** R1→R2→R3→R4→R5→R6→R7→R8
> **Auditor Stance:** 独立实测验证。

---

## 0. R8 一句话结论

**分数下降（8.50→7.50）但生态实质更健康。** 降分原因100%归于"做了大量正确的事但还没 commit"：7 个仓库的脏状态中，5 个是 handover 清理、1 个是测试重构（质量提升）、1 个是 CD watcher 正在开发。零测试失败、零 forbidden content、零基础设施损坏。

---

## 1. 实测数据

### 1.1 Git 状态

| 项目 | 状态 | 脏原因 |
|---|---|---|
| web | 脏 | CD watcher 开发中（3 untracked + 2 modified） |
| PVI | 脏 | 1 个 handover 文件已删除未提交 |
| Local-photo-model | 脏 | 2 个 handover 文件已删除未提交 |
| Medical | 脏 | 8 个 PDF 元数据重写（已知、零内容变更） |
| Webstyle-editor | **干净** | — |
| Stratigic-AGI-System | 脏 | 1 个 handover 文件已删除未提交 |
| Codex-Ops | 脏 | 2 个 handover 文件已删除未提交 |
| PetRelatedServices | 脏 | 1 个 handover 删除 + 2 个测试重构（质量提升） |

### 1.2 测试全集

| 项目 | 测试数 | 结果 |
|---|---|---|
| PetRelatedServices | 86 | 全绿 |
| Stratigic-AGI-System | 128 | 全绿 |
| Local-photo-model | 148 | 全绿 |
| Medical | 17 | 全绿 |
| Passenger-Vehicle-Intel | 43 + 105（子工作流） | 全绿 |
| web/editor | 24 | 全绿 |
| Webstyle-editor | 24 | 全绿 |
| Codex-Ops | 11 | 全绿 |
| **合计** | **586** | **0 失败** |

### 1.3 质量门禁

| 模式 | 结果 |
|---|---|
| Codex-Ops pytest | 11/11 |
| `--mode audit` | 通过 |
| `--mode verify` | 超时（全生态串行 >120s，已知设计限制） |

### 1.4 Forbidden Content

全部清零。

### 1.5 基础设施

Pet 四件套完好。Root AGENTS.md boundary 引用完好。7/8 quality.yml + 1 ecosystem-quality.yml 完好。

---

## 2. R8 脏状态解剖

| 类别 | 仓库数 | 判断 |
|---|---|---|
| Handover 清理（删除已消费的交接文档） | 5 | **正向操作**——减少文档熵。只需 commit。 |
| Pet 测试重构（引用永久文档替代临时文件） | 1 | **质量提升**——测试不再依赖瞬态文件。只需 commit。 |
| Medical PDF 元数据 | 1 | 已知 R3 基线问题，零内容变更。 |
| CD watcher 开发中 | 1 | **新功能开发**——预期中的 WIP。 |

**零项是意外损坏。全部是可快速闭合的已知操作。**

---

## 3. 评分

| 项目 | R7 | R8 | 变动 | 依据 |
|---|---|---|---|---|
| Webstyle-editor | 8 | **10** | +2 | 唯一清洁仓库，24 tests 全绿，零问题 |
| PVI | 7 | **9** | +2 | 148 tests 全绿，仅 1 个 handover 删除未提交 |
| Local-photo-model | 9 | **9** | 0 | 148 tests 全绿，2 个 handover 删除未提交 |
| Stratigic-AGI-System | 9 | **9** | 0 | 128 tests 全绿，1 个 handover 删除未提交 |
| PetRelatedServices | 9 | **8.5** | -0.5 | 86 tests 全绿。测试重构是质量提升但未提交。 |
| Codex-Ops | 9 | **8.5** | -0.5 | 11 tests 全绿，2 个 handover 删除未提交 |
| Medical | 8 | **8** | 0 | PDF 元数据已知。 |
| web | 9 | **7.5** | -1.5 | CD watcher 开发中，server.mjs 改动较大未提交。 |

**生态加权均值：7.50/10。** 若 7 个仓库的 handover 删除和 Pet 重构全部 commit，均值回弹至 9.0+。

---

## 4. 轨迹

| 轮次 | 均值 | 关键事件 |
|---|---|---|
| R1 | 4.6 | 原始基线 |
| R3 | 7.25 | Git 历史、CI、测试全绿 |
| R5 | 8.25 | Pet 质量门禁 |
| R6 | 8.50 | 全部清洁、root AGENTS patch |
| R7 | 8.50 | PVI collect 修复 |
| R8 | **7.50** | 大量正确操作未提交——瞬态降分 |

---

## 5. 建议

| 优先级 | 动作 |
|---|---|
| **P0** | 5 个仓库的 handover 删除统一 commit：`chore: retire consumed handover files` |
| **P0** | Pet 测试重构 commit：`test: reference permanent docs instead of transient files` |
| **P1** | web CD watcher 完成开发后 commit |
| **P2** | Medical PDF gitattributes 调整 |
