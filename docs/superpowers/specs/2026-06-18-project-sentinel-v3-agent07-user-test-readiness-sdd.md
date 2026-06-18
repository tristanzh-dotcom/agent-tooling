# Project Sentinel v3 Agent07 User-Test Readiness SDD

Date: 2026-06-18
Stage: Agent07 user-test readiness
Scope: feature-required Agent07 project delta. No shared web publishing paradigm changes.

## Goal

Agent07 must be testable by TZ as a product loop, not only as a state mutation demo. The loop is:

1. Scout returns up to five source-backed skill candidates.
2. TZ selects a candidate and sees source-backed decision evidence.
3. TZ rejects weak candidates; the queue backfills from the same runtime run when possible.
4. TZ approves a candidate; a local deep audit report is generated and becomes visible in the Artifacts Theater.
5. TZ can decide whether the skill should proceed to integration based on the audit card.

## Backfill Contract

Runtime shadow display must not hard-slice the first five repos before applying blacklist. It must:

1. Read the latest runtime candidate pool from `source_candidates.runtime.json` and `source_candidates.envelope.json`.
2. Merge runtime candidates first, then envelope candidates.
3. Remove persisted blacklist repos before display.
4. Render the first five remaining repos.
5. Report `READY_FOR_REVIEW` only when five visible candidates remain; otherwise report `PARTIAL_RECALL`.

This is same-run backfill. It must not silently start network collection. If the same runtime run has fewer than five non-blacklisted candidates, the UI must expose partial recall honestly.

## Approve Deep Audit Contract

Approve must remain first-frame responsive and must still persist `APPROVED/AUDITING` before any heavier work. After persistence, the default local auditor must:

1. Create a deterministic audit report from the selected lead's runtime capability evidence.
2. Write a Markdown report under `Git-Scout/storage/audit_reports/<safe_repo>/audit_report.md`.
3. Atomically update the production lead with:
   - `audit_status: "COMPLETED"` on success;
   - `audit_report` containing verdict, recommendation, confidence, evidence, integration steps, risks, deliverables, and markdown path.
4. Keep the existing `audit_wakeup.jsonl` event for traceability.

The first user-test implementation is local and deterministic. It must not call external LLMs or send repository data out of the machine.

## UI Contract

The Artifacts Theater must show the selected lead's audit card when `audit_report` exists:

- verdict and recommendation;
- confidence;
- evidence bullets;
- integration steps;
- expected deliverables;
- risks;
- report path rewritten to a `shadow://`-style or relative safe reference.

The page may poll `/api/agent07/status` after approve so the visible card moves from `AUDITING` to `COMPLETED` without a manual refresh.

## Acceptance Tests

Add service and DOM contract tests for:

- reject backfills from runtime envelope candidates after blacklist filtering;
- approve schedules local audit and eventually returns `COMPLETED` with an `audit_report`;
- status overlay preserves `audit_report` for runtime display candidates;
- Artifacts Theater renders the audit report and never leaks absolute local paths;
- approve/reject decision controls remain usable.

## Git Guard

Root repository has unrelated dirty files. Stage only this SDD and the matching implementation plan in root. Web changes are staged only in the Agent07 QA worktree files needed for server, JS, CSS, and tests.

