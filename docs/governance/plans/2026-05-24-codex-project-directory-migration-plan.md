# Codex 项目物理目录迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将所有长期 Codex 工作流项目统一迁入 `/Users/tristanzh/agent` 体系，并把通用治理能力从业务项目中剥离到 `Codex-Ops`。

**Architecture:** 迁移采用“一次只迁移一个项目”的串行方式。每个项目先建立目标目录，再迁移文件、更新引用、运行全量测试，通过后保留旧路径软链接 1 天；3 天后将旧保留文件移动到 `/Users/tristanzh/agent/temp` 并断开映射；6 天后无异常再物理删除 `temp`。

**Tech Stack:** macOS filesystem, shell, SQLite Codex state checks, Node.js tests for Web, Python tests for业务项目, Markdown governance docs.

---

## Source Design

本计划执行以下设计文档：

`/Users/tristanzh/agent/docs/governance/2026-05-24-codex-project-directory-governance-design.md`

## Global Safety Rules

- 不使用 `git reset --hard` 或破坏性回滚。
- 不一次性迁移多个项目。
- 每个迁移任务开始前先备份或确认可回滚路径。
- 旧路径保留策略按 TZ 已确认规则执行：
  - 迁移后立即全量测试；
  - 全部通过则旧路径软链接保留 1 天；
  - 任一测试失败则停止并提示 TZ；
  - 3 天后将保留文件移动到 `/Users/tristanzh/agent/temp` 并断开映射；
  - 6 天后无问题则物理删除 `/Users/tristanzh/agent/temp`。
- `~/.codex/skills` 不迁移。
- `/agent01` 到 `/agent04` Web 路由不改名。

## Target Structure

```text
/Users/tristanzh/agent/
├── web/
├── Codex-Ops/
├── Document-creator/
├── Passenger-Vehicle-Intel/
│   ├── domestic-sales/
│   ├── jlr-sales/
│   ├── hardware-supplier/
│   └── data-platform/
├── DiamondTurtles/
├── Local-photo-model/
├── Medical/
├── docs/
│   ├── governance/
│   └── model-configs/
├── temp/
└── _archive/
```

## Task 1: Create Codex-Ops Governance Workspace

**Files / Directories:**
- Create: `/Users/tristanzh/agent/Codex-Ops`
- Create: `/Users/tristanzh/agent/Codex-Ops/docs`
- Create: `/Users/tristanzh/agent/Codex-Ops/PROJECT_MEMORY.md`
- Create: `/Users/tristanzh/agent/Codex-Ops/PROJECT_RULES.md`
- Create: `/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md`
- Modify later: `/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md`

- [ ] **Step 1: Create directories**

Run:

```bash
mkdir -p /Users/tristanzh/agent/Codex-Ops/docs
```

Expected: directory exists.

- [ ] **Step 2: Create Codex-Ops project memory**

Create `/Users/tristanzh/agent/Codex-Ops/PROJECT_MEMORY.md` with:

```markdown
# Project Memory - Codex-Ops

Last updated: 2026-05-24

## Identity

- Canonical project name: `Codex-Ops`
- Project shorthand: `Codex-Ops`
- Workspace: `/Users/tristanzh/agent/Codex-Ops`
- Technical route: none

## Scope

Codex-Ops owns cross-project governance, naming policy, model policy records, Codex state repair notes, self-audit usage records, and cross-project handoff documents.

Codex-Ops does not own business project data, Web routes, Feishu cards, or `~/.codex/skills`.
```

- [ ] **Step 3: Create Codex-Ops rules**

Create `/Users/tristanzh/agent/Codex-Ops/PROJECT_RULES.md` with:

```markdown
# Project Rules - Codex-Ops

Last updated: 2026-05-24

## Boundaries

- Keep `~/.codex/skills` as the actual skill installation location.
- Store only governance documents, audit records, model policy records, and project index records here.
- Do not place business workflow code in Codex-Ops.
- Do not make Codex-Ops a Web route unless TZ explicitly requests it.
```

- [ ] **Step 4: Copy global project index**

Run:

```bash
cp /Users/tristanzh/agent/Assistant/PROJECT_INDEX.md /Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md
```

Expected: copied index exists.

- [ ] **Step 5: Verify**

Run:

```bash
test -f /Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md
test -f /Users/tristanzh/agent/Codex-Ops/PROJECT_MEMORY.md
test -f /Users/tristanzh/agent/Codex-Ops/PROJECT_RULES.md
```

Expected: all commands exit 0.

## Task 2: Migrate 文档生成小能手

**Files / Directories:**
- Move source: `/Users/tristanzh/Documents/PowerPoint-creator`
- Target: `/Users/tristanzh/agent/Document-creator`
- Update docs/index references after move.
- Preserve old path as symlink if tests pass.

- [ ] **Step 1: Preflight source and target**

Run:

```bash
test -d /Users/tristanzh/Documents/PowerPoint-creator
test ! -e /Users/tristanzh/agent/Document-creator
```

Expected: source exists; target does not exist.

- [ ] **Step 2: Inventory absolute references**

Run:

```bash
rg -n '/Users/tristanzh/Documents/PowerPoint-creator|PowerPoint-creator' /Users/tristanzh/agent /Users/tristanzh/Documents/PowerPoint-creator
```

Expected: collect references before migration.

- [ ] **Step 3: Move directory**

Run:

```bash
mv /Users/tristanzh/Documents/PowerPoint-creator /Users/tristanzh/agent/Document-creator
```

Expected: target exists; source no longer exists.

- [ ] **Step 4: Update references**

Update references from:

```text
/Users/tristanzh/Documents/PowerPoint-creator
```

to:

```text
/Users/tristanzh/agent/Document-creator
```

Expected files include:
- `/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md`
- `/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md`
- `/Users/tristanzh/agent/web/PROJECT_MEMORY.md`
- `/Users/tristanzh/agent/web/docs/2026-05-24-project-naming-change-notice.md`
- `/Users/tristanzh/agent/Document-creator/docs/2026-05-24-project-naming-change-notice.md`

- [ ] **Step 5: Update Codex state if needed**

Query:

```bash
sqlite3 -header -column /Users/tristanzh/.codex/state_5.sqlite "SELECT id,cwd,title FROM threads WHERE cwd='/Users/tristanzh/Documents/PowerPoint-creator';"
```

If rows exist, back up `state_5.sqlite` and update only those `cwd` values to `/Users/tristanzh/agent/Document-creator`.

- [ ] **Step 6: Run verification**

Run:

```bash
npm test
```

from `/Users/tristanzh/agent/web`.

Also run any project-local tests discovered in `/Users/tristanzh/agent/Document-creator`.

- [ ] **Step 7: Create old-path symlink if all tests pass**

Run:

```bash
ln -s /Users/tristanzh/agent/Document-creator /Users/tristanzh/Documents/PowerPoint-creator
```

Expected: old path resolves to target.

- [ ] **Step 8: Schedule cleanup milestones**

Create follow-up records for:
- 1 day: inspect symlink after stabilization.
- 3 days: move retained old-path material to `/Users/tristanzh/agent/temp` and unlink old mapping.
- 6 days: delete `/Users/tristanzh/agent/temp` if no issue.

## Task 3: Migrate 钻纹龟资料库

**Files / Directories:**
- Move source: `/Users/tristanzh/Documents/DiamondTurtles`
- Target: `/Users/tristanzh/agent/DiamondTurtles`
- Preserve old path as symlink if tests pass.

- [ ] **Step 1: Preflight**

Run:

```bash
test -d /Users/tristanzh/Documents/DiamondTurtles
test ! -e /Users/tristanzh/agent/DiamondTurtles
```

Expected: source exists; target does not exist.

- [ ] **Step 2: Inventory absolute references**

Run:

```bash
rg -n '/Users/tristanzh/Documents/DiamondTurtles|DiamondTurtles' /Users/tristanzh/agent /Users/tristanzh/Documents/DiamondTurtles
```

Expected: collect references before migration.

- [ ] **Step 3: Move directory**

Run:

```bash
mv /Users/tristanzh/Documents/DiamondTurtles /Users/tristanzh/agent/DiamondTurtles
```

- [ ] **Step 4: Update references**

Replace absolute path references with:

```text
/Users/tristanzh/agent/DiamondTurtles
```

Expected files include:
- `/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md`
- `/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md`
- `/Users/tristanzh/agent/web/PROJECT_MEMORY.md`
- `/Users/tristanzh/agent/web/PROJECT_RULES.md`
- `/Users/tristanzh/agent/web/NEXT_STEPS.md`
- `/Users/tristanzh/agent/web/CHANGELOG.md`
- `/Users/tristanzh/agent/DiamondTurtles/PROJECT_RULES.md`
- `/Users/tristanzh/agent/DiamondTurtles/docs/**`

- [ ] **Step 5: Update Codex state if needed**

Query:

```bash
sqlite3 -header -column /Users/tristanzh/.codex/state_5.sqlite "SELECT id,cwd,title FROM threads WHERE cwd='/Users/tristanzh/Documents/DiamondTurtles';"
```

If rows exist, back up and update only those `cwd` values.

- [ ] **Step 6: Run verification**

Run from `/Users/tristanzh/agent/web`:

```bash
node --test tests/agent03-service.test.mjs
npm test
```

- [ ] **Step 7: Create old-path symlink if all tests pass**

Run:

```bash
ln -s /Users/tristanzh/agent/DiamondTurtles /Users/tristanzh/Documents/DiamondTurtles
```

- [ ] **Step 8: Schedule cleanup milestones**

Same 1 day / 3 day / 6 day policy as Task 2.

## Task 4: Migrate 乘用车信息汇总 and JLR child project

**Files / Directories:**
- Move source: `/Users/tristanzh/agent/Passenger-Vehicle-Intel`
- Target: `/Users/tristanzh/agent/Passenger-Vehicle-Intel`
- Move source child: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales`
- Target child: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales`

- [ ] **Step 1: Preflight**

Run:

```bash
test -d /Users/tristanzh/agent/Passenger-Vehicle-Intel
test -d /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
test ! -e /Users/tristanzh/agent/Passenger-Vehicle-Intel
```

- [ ] **Step 2: Inventory absolute references**

Run:

```bash
rg -n '/Users/tristanzh/agent/Passenger-Vehicle-Intel|/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales|Daily-Auto-Report|JLR_data_statistic' /Users/tristanzh/agent
```

- [ ] **Step 3: Move parent project**

Run:

```bash
mv /Users/tristanzh/agent/Passenger-Vehicle-Intel /Users/tristanzh/agent/Passenger-Vehicle-Intel
```

- [ ] **Step 4: Move JLR child project**

Run:

```bash
mv /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
```

- [ ] **Step 5: Normalize internal docs folders**

Move or mirror:

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel/docs/data-platform
/Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier-dashboard
```

into the documented internal structure if needed:

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel/data-platform
/Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier
```

Only perform this if tests can be updated in the same task.

- [ ] **Step 6: Update references**

Replace paths:

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel -> /Users/tristanzh/agent/Passenger-Vehicle-Intel
/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales -> /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
```

Expected files include:
- Web server references
- Web tests
- project memory/rules docs
- governance docs
- Feishu preview paths
- local notification docs

- [ ] **Step 7: Update Codex state if needed**

Query and update rows with old `cwd` values only after backing up `state_5.sqlite`.

- [ ] **Step 8: Run verification**

Run from `/Users/tristanzh/agent/Passenger-Vehicle-Intel`:

```bash
python3 -m unittest tests/test_external_interface.py -v
python3 -m unittest tests/test_auto_intelligence_agent.py -v
```

Run from `/Users/tristanzh/agent/web`:

```bash
npm test
```

If available, run Agent02 preview API checks without sending Feishu messages.

- [ ] **Step 9: Create old-path symlinks if all tests pass**

Run:

```bash
mkdir -p /Users/tristanzh/agent/Assistant
ln -s /Users/tristanzh/agent/Passenger-Vehicle-Intel /Users/tristanzh/agent/Passenger-Vehicle-Intel
ln -s /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales /Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
```

- [ ] **Step 10: Schedule cleanup milestones**

Same 1 day / 3 day / 6 day policy.

## Task 5: Finalize Project Index Ownership

**Files:**
- Primary: `/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md`
- Transitional mirror: `/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md`

- [ ] **Step 1: Update primary index**

Ensure `/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md` reflects all final target paths.

- [ ] **Step 2: Convert Assistant index to transitional pointer**

After all migrations pass, replace `/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md` content with a pointer to:

```text
/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md
```

Do this only after Agent02 migration succeeds.

- [ ] **Step 3: Verify references**

Run:

```bash
rg -n '/Users/tristanzh/Documents/PowerPoint-creator|/Users/tristanzh/Documents/DiamondTurtles|/Users/tristanzh/agent/Passenger-Vehicle-Intel|/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales' /Users/tristanzh/agent /Users/tristanzh/Documents
```

Expected: only historical migration notes, symlink cleanup docs, or explicitly marked legacy context remain.

## Task 6: Cleanup Automation / Follow-up Records

**Files / Tools:**
- Codex automation tool for future checks.
- Local docs under `/Users/tristanzh/agent/Codex-Ops/docs`.

- [ ] **Step 1: After each migration, record cleanup timeline**

Create a migration log document:

```text
/Users/tristanzh/agent/Codex-Ops/docs/YYYY-MM-DD-<project>-migration-log.md
```

It must include:
- old path
- new path
- tests run
- pass/fail result
- symlink creation time
- 1 day check time
- 3 day temp move time
- 6 day delete time

- [ ] **Step 2: Use Codex reminders where appropriate**

Create follow-up reminders for 1 day / 3 day / 6 day checks after each successful migration.

- [ ] **Step 3: If a test fails**

Stop the migration chain and report:
- failed command
- relevant output
- current filesystem state
- rollback options
- requested TZ decision

## Self-Review Checklist

- [x] No placeholder tasks.
- [x] Every migration has preflight, inventory, move, reference update, Codex state check, verification, symlink, cleanup milestones.
- [x] Agent02 migration is isolated as the highest-risk task.
- [x] `~/.codex/skills` is explicitly not moved.
- [x] Web routes remain unchanged.
