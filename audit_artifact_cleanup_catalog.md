# Audit Artifact Cleanup Catalog

> **Purpose:** 供 vibe-clean skill 学习识别审计过程中产生的可清理文件。
> **生成者:** DeepSeek 审计 agent（R1-R3 三轮）。
> **维护者:** TZ / Codex。

---

## 1. 可直接删除的审计文档

审计每轮都会生成独立的 MD 白皮书。当前轮次完成后，历史轮次的文档即变为过时快照。

| 文件 | 轮次 | 性质 | 保留/删除 |
|---|---|---|---|
| `Agent_Ecosystem_Review.md` | R1 原始白皮书 | 已完全被 R3 取代 | **可删除** |
| `deepseek_audit_feedback_r2.md` | R2 复审 | 已完全被 R3 取代 | **可删除** |
| `deepseek_audit_feedback_r3.md` | R3 Phase 1-4 验收 | **当前最新** | 保留至下一轮 |

**命名模式识别规则：**
```
Agent_Ecosystem_Review*.md    # R1 及其变体
deepseek_audit_feedback_r*.md # 除最新一轮外的所有 rN.md
audit_*.md                    # 通用审计文档
*_audit_*.md                  # 嵌入式审计文件名
```

建议：保留最新一轮（最大 rN 编号），其余删除。

---

## 2. 审计测试执行产生的运行时垃圾

审计 agent 会执行 `pytest` / `vitest` / `npm test` 来验证项目健康度。这些命令会在项目目录中留下缓存。

| 路径 | 来源 | 大小 |
|---|---|---|
| `/.pytest_cache/` | 根级 pytest 运行 | ~4 KB |
| `Local-photo-model/.pytest_cache/` | LPM 测试套件运行 | ~4 KB |
| `PetRelatedServices/.pytest_cache/` | Pet 测试套件运行 | ~4 KB |
| `Medical/.pytest_cache/` | Medical 测试套件运行 | ~4 KB |
| `Codex-Ops/.pytest_cache/` | Codex-Ops 测试套件运行 | ~4 KB |
| `Passenger-Vehicle-Intel/.pytest_cache/` | PVI 测试套件运行 | ~4 KB |

**识别规则：**
```
.pytest_cache/           # pytest 运行时缓存，每次运行后可再生
__pycache__/             # Python 字节码缓存（本项目审计中未产生，但需规则覆盖）
*.pyc                    # Python 编译产物
node_modules/.cache/     # Node 工具链缓存
.vitest/                 # Vitest 运行时目录
```

这些目录已在各项目 `.gitignore` 中排除，不会进入版本控制。但从磁盘清理角度仍需处理。

---

## 3. 系统临时目录泄漏

审计 agent 的测试运行会在 macOS `/var/folders` 中创建临时 pipeline 目录。

| 模式 | 示例 | 说明 |
|---|---|---|
| `/var/folders/.../T/limb-pipeline-*` | `limb-pipeline-ttyy3g3x` | web/editor 测试的 DOM 指纹引擎临时管道 |
| `/var/folders/.../T/limb-html-*` | `limb-html-TCFoLn` | HTML AST 处理临时文件 |
| `/var/folders/.../T/limb-workbench-*` | `limb-workbench-kpCjvu` | 工作台渲染临时文件 |
| `/var/folders/.../T/tmp-*-source-*` | `tmp-relative-source-cP52Ar` | 测试用临时源文件目录 |

这些是由测试框架自动创建的临时文件，通常在进程退出后由 OS 回收，但长时间运行或异常退出时会残留。

**清理规则：** 检查 `/var/folders` 下超过 1 小时且匹配上述模式的文件/目录，安全删除。

---

## 4. 审计 agent 全局留下的标记

以下是我（DeepSeek 审计 agent）在当前 session 中在 agent 根目录留下的可识别痕迹：

| 类型 | 内容 | 清理建议 |
|---|---|---|
| 对话级 | 3 个 MD 白皮书（见第 1 节） | 保留 R3，其余删 |
| 对话级 | 6 个 `.pytest_cache/` 目录 | 全部可删 |
| 对话级 | `Agent_Ecosystem_Review.md` 中的明文 API key | **已用 `<redacted>` 替代**（R2 回滚时恢复，R3 再次本地点覆盖） |
| 系统级 | `/var/folders` 临时文件 | OS 自动回收，可手动清理 |
| **无** | 未创建 `.bak`、`.log`、`.tmp`、`.swp` 文件 | — |

---

## 5. 给 vibe-clean skill 的格式规则汇总

将以下模式加入 skill 的识别/清理白名单：

### 文件级（按文件名模式）

```
# 审计产物（版本化）
Agent_Ecosystem_Review*.md
deepseek_audit_feedback_r*.md
audit_report_*.md
*_audit_*.md

# 项目卫生产物（非业务）
.pytest_cache/
__pycache__/
*.pyc
.vitest/
node_modules/.cache/

# 编辑器/工具残留
.DS_Store
*.swp
*.swo
*~
```

### 目录级

```
.pytest_cache/     # 可再生，安全删除
__pycache__/       # 可再生，安全删除
```

### 系统临时目录模式

```
/var/folders/**/T/limb-pipeline-*
/var/folders/**/T/limb-html-*
/var/folders/**/T/limb-workbench-*
/var/folders/**/T/tmp-*-source-*
```

### 删除前的安全校验

在删除任何匹配审计产物的文件前，应检查：

1. 文件名中是否包含 `r` + 数字后缀？保留最大数字的，其余删。
2. 文件内容是否被其他活跃文档引用？（grep 文件名在其他 MD 中的出现次数）
3. 是否是当前审计周期的唯一输出？（如果只有一个 `r*.md` 则保留）

---

## 6. 适用于本项目当前状态的清理建议

```bash
# 建议执行（在 agent 根目录）
rm Agent_Ecosystem_Review.md        # R1 已过时
rm deepseek_audit_feedback_r2.md    # R2 已过时
# 保留 deepseek_audit_feedback_r3.md (最新)

# 清理测试缓存（可再生）
find . -name ".pytest_cache" -not -path "*/node_modules/*" -not -path "*/venv/*" -exec rm -rf {} + 2>/dev/null

# 系统临时文件（OS 通常自动回收，但可手动触发）
find /var/folders -maxdepth 5 -name "limb-*" -mmin +60 -exec rm -rf {} + 2>/dev/null
find /var/folders -maxdepth 5 -name "tmp-*-source-*" -mmin +60 -exec rm -rf {} + 2>/dev/null
```
