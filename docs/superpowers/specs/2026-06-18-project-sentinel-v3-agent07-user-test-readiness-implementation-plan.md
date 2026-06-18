# Agent07 User-Test Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Agent07 user-test loop by adding same-run backfill, local deep audit report generation, and visible audit deliverables.

**Architecture:** Keep the authoritative production state in `Git-Scout/data/scout_pipeline.json`. Use runtime shadow as the read-only candidate source and production JSON as the decision overlay. Run the first audit worker locally and deterministically from already-captured capability evidence.

**Tech Stack:** Node ESM web server, vanilla JS Agent07 frontend, Node test runner for web contracts, local JSON/Markdown artifacts.

---

### Task 1: Runtime Backfill

**Files:**
- Modify: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/server.mjs`
- Test: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/tests/agent07-service.test.mjs`

- [ ] Add a failing service test that rejects the first runtime candidate and expects the displayed list to remain at five by pulling the next repo from `source_candidates.envelope.json`.
- [ ] Change runtime candidate loading to collect more than five repos before blacklist filtering.
- [ ] Apply blacklist filtering before final `.slice(0, 5)`.
- [ ] Run `node --test tests/agent07-service.test.mjs`.

### Task 2: Local Audit Worker

**Files:**
- Modify: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/server.mjs`
- Test: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/tests/agent07-service.test.mjs`

- [ ] Add a failing service test that approves a runtime candidate, waits for audit completion, and expects `audit_status: "COMPLETED"` plus a persisted `audit_report`.
- [ ] Preserve `AUDIT_FAILED` and `audit_report` in `normalizeAgent07Lead`.
- [ ] Implement a default local auditor that writes `audit_wakeup.jsonl`, creates `storage/audit_reports/<safe_repo>/audit_report.md`, and updates the lead with deterministic report content.
- [ ] Ensure approve response remains responsive and status polling observes completion.
- [ ] Run `node --test tests/agent07-service.test.mjs`.

### Task 3: Audit Report UI

**Files:**
- Modify: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/app/agent07.js`
- Modify: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/app/agent07.css`
- Test: `/Users/tristanzh/.config/superpowers/worktrees/web/agent07-stage10-qa/tests/agent07-ui-dom.test.mjs`

- [ ] Add a failing DOM test that supplies a selected lead with `audit_report` and expects the Artifacts Theater to show verdict, recommendation, evidence, integration steps, deliverables, risks, and no absolute local path.
- [ ] Render a compact audit card inside the existing evidence ledger area.
- [ ] Sanitize report paths with existing telemetry path sanitizer.
- [ ] Poll status after approve until selected lead is no longer `AUDITING` or a short bounded poll limit is hit.
- [ ] Run `node --test tests/agent07-ui-dom.test.mjs`.

### Task 4: End-to-End Gate

**Files:**
- Test: existing Agent07 web tests.

- [ ] Run `node --test tests/agent07-ui-dom.test.mjs tests/agent07-telemetry-panel.test.mjs tests/agent07-service.test.mjs`.
- [ ] Run `node --check server.mjs && node --check app/agent07.js`.
- [ ] Start the QA server on `127.0.0.1:3317` with real Git-Scout paths.
- [ ] Exercise reject and approve through HTTP or browser automation and verify status JSON exposes a user-testable audit card.
- [ ] Commit root docs and Web changes separately with selective staging.

