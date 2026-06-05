# R2 Ecosystem Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the verified DeepSeek R2 remediation items into a cleaner, testable, versioned baseline.

**Architecture:** This pass keeps each project as an independent repository. It fixes repository hygiene first, then fixes reproducible tests and hardcoded runtime identity, then records operational scripts before baseline commits.

**Tech Stack:** Git, Python/pytest, Node/Vitest, shell scripts, project-local `.gitignore` files.

---

### Task 1: Repository Hygiene Gate

**Files:**
- Modify: `/Users/tristanzh/agent/web/.gitignore`
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/.gitignore`
- Modify: `/Users/tristanzh/agent/Medical/.gitignore`
- Modify: `/Users/tristanzh/agent/Local-photo-model/.gitignore`
- Modify: `/Users/tristanzh/agent/Webstyle-editor/.gitignore`
- Modify: `/Users/tristanzh/agent/Stratigic-AGI-System/.gitignore`
- Modify: `/Users/tristanzh/agent/Codex-Ops/.gitignore`
- Modify: `/Users/tristanzh/agent/PetRelatedServices/.gitignore`

- [ ] Add ignore rules for virtualenvs, caches, generated databases, logs, build output, `_archive_legacy/`, and backup files.
- [ ] Run `git status --short --ignored` in each project and confirm ignored files include heavy runtime artifacts.
- [ ] Run `git status --short` in each project and inspect staged candidates before committing.

### Task 2: Local Photo Test Repair

**Files:**
- Modify: `/Users/tristanzh/agent/Local-photo-model/tests/test_frontend_agent04.py`
- Modify: `/Users/tristanzh/agent/Local-photo-model/tests/test_workspace_scripts.py`

- [ ] Reproduce the current failures with `python3 -m pytest tests -q`.
- [ ] Confirm whether failures are stale assertions against current CSS/script structure or real product regressions.
- [ ] Update tests only when current implementation satisfies the original behavior.
- [ ] Re-run `python3 -m pytest tests -q` and require all tests to pass.

### Task 3: Web Runtime Identity Configuration

**Files:**
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Modify: `/Users/tristanzh/agent/web/tests/agent04-service.test.mjs`

- [ ] Add a failing test that rejects hardcoded `tzSelfOpenId` and requires environment-based default identity configuration.
- [ ] Replace the hardcoded open_id with `process.env.LARK_DEFAULT_USER_ID || ""`.
- [ ] Re-run `node --test tests/agent02-service.test.mjs tests/agent04-service.test.mjs`.

### Task 4: Rollback and Backup Governance

**Files:**
- Create: `/Users/tristanzh/agent/docs/rollback-and-backup-governance.md`

- [ ] Inventory retained rollback scripts.
- [ ] State that `.bak*` files are local backup artifacts and should not enter baseline commits.
- [ ] State that `_archive_legacy/` is local historical material excluded from initial repository baselines.

### Task 5: Baseline Commits

**Files:** project-local tracked files only.

- [ ] For each empty repository, run `git add .`.
- [ ] Inspect `git status --short` and `git ls-files`.
- [ ] Abort if secrets, virtualenvs, caches, node_modules, generated DBs, or backup files appear.
- [ ] Commit with `chore: establish audited baseline`.

