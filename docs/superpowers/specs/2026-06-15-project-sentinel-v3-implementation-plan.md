# Project Sentinel v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Project Sentinel v3 as a local, file-contract-first intelligence pipeline with atomic state persistence, pre-flight token budgeting, a Blind Scout pipeline, and a minimal web gate that can safely trigger third-layer audits.

**Architecture:** Build the system in three TDD milestones. Each milestone must land failing tests first, then the smallest implementation needed to pass, then verification and commit. No external network or paid model calls are allowed in tests; all source APIs, tokenizer outputs, strong-model clients, and OS signals must be mocked or injected.

**Tech Stack:** TypeScript on Node.js 22+, Vitest, Zod, `js-tiktoken` or a documented tokenizer adapter, local JSON/JSONL state, Node HTTP server, and an optional Python `os.replace` helper only if needed for cross-runtime atomic-write verification.

---

## Source of Truth

- SDD: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-14-project-sentinel-v3-design.md`
- Work root: `/Users/tristanzh/agent/Git-Scout`
- Shared web boundary: do not publish into `/Users/tristanzh/agent/web` in this implementation.
- Existing unrelated dirty files under `Medical/`, `Passenger-Vehicle-Intel/`, and root handover files must not be staged, modified, or reverted.

## Implementation File Map

Create these files under `/Users/tristanzh/agent/Git-Scout` during execution:

```text
package.json
tsconfig.json
vitest.config.ts
scout_pipeline.json
src/
  cli.ts
  schemas/
    pipelineSchema.ts
    scoutContracts.ts
  storage/
    atomicJson.ts
    checkpointStore.ts
    pythonAtomicReplaceHelper.py
  state/
    stateMachine.ts
    shutdown.ts
  scout/
    sourceClient.ts
    blindScout.ts
    retryPolicy.ts
    scheduler.ts
  token/
    tokenizer.ts
    budgetLedger.ts
    circuitBreaker.ts
  audit/
    auditPack.ts
    auditTrigger.ts
  dashboard/
    server.ts
  web/
    index.html
    app.js
    styles.css
tests/
  storage/
    atomicJson.test.ts
    checkpointRecovery.test.ts
  state/
    signalRecovery.test.ts
  scout/
    blindScout429.test.ts
    payloadBudget.test.ts
  dashboard/
    highFrequencyDecision.test.ts
    auditTrigger.test.ts
fixtures/
  scout_candidates.json
  audit_payloads/
```

## Milestone 1: Data & State Base

**Objective:** Build the durable storage base: `scout_pipeline.json` schema, atomic JSON writes using temp-file plus OS-level replace semantics, and a resumable checkpoint state machine.

**Deliverables:**

- `scout_pipeline.json` model definition.
- Zod schema for pipeline state and event contracts.
- Atomic JSON writer with same-directory temp file, fsync, atomic replacement, and per-file lock.
- Python helper using `os.replace` for explicit cross-runtime atomic replace verification if the implementation needs a Python-side fixture.
- Checkpoint rebuild from event log.
- Signal-safe shutdown hook for `SIGINT` and `SIGTERM`.

### TDD Matrix

| Test file | Test name | Arrange | Act | Assert |
| --- | --- | --- | --- | --- |
| `tests/storage/atomicJson.test.ts` | `atomic writer never leaves corrupted json under interrupted write` | Create valid `scout_pipeline.json`; inject a writer that receives abort after temp file is created but before replace. | Trigger write and simulated `SIGTERM`. | Target JSON still parses; old state is intact; temp file is ignored by readers. |
| `tests/storage/atomicJson.test.ts` | `concurrent writers serialize through lock` | Start two writes against the same JSON with controlled lock delay. | Resolve both writes. | Final JSON parses and contains exactly one legal final state; no partial JSON is observed. |
| `tests/storage/checkpointRecovery.test.ts` | `checkpoint rebuilds from events when snapshot is corrupt` | Write valid `events.jsonl`; write invalid `checkpoint.json`. | Load checkpoint. | Loader rebuilds from events and rewrites valid checkpoint. |
| `tests/state/signalRecovery.test.ts` | `sigterm during io writes shutdown event and keeps json valid` | Start a long-running write with injectable barrier. | Send `SIGTERM` through shutdown handler. | `shutdown_requested` event exists; `scout_pipeline.json` parses; checkpoint is resumable. |

### Tasks

- [ ] **Step 1: Write failing storage and state tests**

Create:

```text
/Users/tristanzh/agent/Git-Scout/tests/storage/atomicJson.test.ts
/Users/tristanzh/agent/Git-Scout/tests/storage/checkpointRecovery.test.ts
/Users/tristanzh/agent/Git-Scout/tests/state/signalRecovery.test.ts
```

The tests must import only planned public interfaces:

```text
writeJsonAtomic
mutateJsonAtomic
loadCheckpoint
appendEvent
installShutdownHandlers
```

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/storage/atomicJson.test.ts tests/storage/checkpointRecovery.test.ts tests/state/signalRecovery.test.ts
```

Expected: fail because storage and state modules do not exist.

- [ ] **Step 2: Define the pipeline schema and state contract**

Create:

```text
/Users/tristanzh/agent/Git-Scout/scout_pipeline.json
/Users/tristanzh/agent/Git-Scout/src/schemas/pipelineSchema.ts
/Users/tristanzh/agent/Git-Scout/src/schemas/scoutContracts.ts
```

The schema must include:

```text
version
run_id
date
state
events_cursor
candidate_ids
budget_day
last_successful_stage
updated_at
```

Allowed states:

```text
idle
discovering
metadata_fetched
cheap_classified
assets_cached
awaiting_tz_gate
approved_for_audit
audit_pack_prepared
audit_budget_reserved
audit_running
audit_complete
rejected_terminal
failed_retryable
failed_terminal
shutdown_requested
```

- [ ] **Step 3: Implement atomic JSON storage**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/storage/atomicJson.ts
```

Implementation requirements:

- Write to same-directory temp file: `<target>.<pid>.<nonce>.tmp`.
- Fsync temp file before replacement.
- Replace target with OS-level atomic rename in Node.
- Fsync parent directory.
- Use per-target lock under `data/locks/`.
- Never read `.tmp` files as authoritative state.
- Delete stale lock only after owner PID check or stale TTL rule.

If a Python helper is needed for integration parity, create:

```text
/Users/tristanzh/agent/Git-Scout/src/storage/pythonAtomicReplaceHelper.py
```

It must use `os.replace(tmp_path, target_path)` and must not perform in-place writes.

- [ ] **Step 4: Implement checkpoint state machine**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/state/stateMachine.ts
/Users/tristanzh/agent/Git-Scout/src/storage/checkpointStore.ts
```

Implementation requirements:

- Append event before checkpoint mutation.
- Reject illegal transitions.
- Rebuild checkpoint from `events.jsonl` if `checkpoint.json` is absent or corrupt.
- Preserve idempotency by `run_id` and event id.
- Never advance from terminal states except through a new `run_id`.

- [ ] **Step 5: Implement signal-safe shutdown**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/state/shutdown.ts
```

Implementation requirements:

- Capture `SIGINT` and `SIGTERM`.
- Abort current fetch or write through `AbortController`.
- Wait for active atomic write safe point.
- Append `shutdown_requested` event.
- Leave every JSON file parseable.

- [ ] **Step 6: Verify Milestone 1**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/storage/atomicJson.test.ts tests/storage/checkpointRecovery.test.ts tests/state/signalRecovery.test.ts
npm run typecheck
```

Expected:

```text
all Milestone 1 tests pass
typecheck exits 0
```

- [ ] **Step 7: Commit Milestone 1**

```bash
cd /Users/tristanzh/agent
git add Git-Scout/scout_pipeline.json Git-Scout/src/schemas Git-Scout/src/storage Git-Scout/src/state Git-Scout/tests/storage Git-Scout/tests/state
git commit -m "feat(sentinel): add atomic state base"
```

## Milestone 2: Blind Scout and Pre-flight Token Interceptor

**Objective:** Build the first-layer scout pipeline with scheduled source flow, HTTP 429-aware exponential backoff, deterministic pre-flight token counting, and post-reservation token circuit breaker.

**Deliverables:**

- Scheduler entry point for daily scout runs.
- Source client abstraction with mocked GitHub/RSS-compatible responses.
- Blind Scout classifier boundary that accepts cleaned metadata, not full repos.
- `js-tiktoken` or tokenizer adapter for exact serialized payload estimates.
- Pre-flight budget interceptor.
- Post-reservation circuit breaker and ledger reconciliation.
- Exponential backoff with jitter for HTTP 429 and retryable failures.

### TDD Matrix

| Test file | Test name | Arrange | Act | Assert |
| --- | --- | --- | --- | --- |
| `tests/scout/blindScout429.test.ts` | `http 429 retries with exponential backoff and resumes cursor` | Mock source client to return 429 twice, then success; fake timers enabled. | Run scout once. | Backoff schedule is deterministic; cursor is persisted; final state reaches `metadata_fetched`. |
| `tests/scout/blindScout429.test.ts` | `retry exhaustion records failed_retryable without duplicate billing` | Mock source client to always return 429. | Run scout once. | State is `failed_retryable`; budget ledger has no model reservation. |
| `tests/scout/payloadBudget.test.ts` | `oversized payload is blocked before model request` | Mock tokenizer to return tokens above `max_input_tokens`. | Attempt third-layer payload reservation. | Strong model client is not called; event is `JOB_INPUT_TOKEN_LIMIT_EXCEEDED`. |
| `tests/scout/payloadBudget.test.ts` | `daily token limit blocks before network model call` | Mock tokenizer under input limit but above remaining daily budget with reserved output. | Attempt reservation. | No model request occurs; event is `audit_skipped_budget_exhausted`; job remains resumable. |

### Tasks

- [ ] **Step 1: Write failing scout and token tests**

Create:

```text
/Users/tristanzh/agent/Git-Scout/tests/scout/blindScout429.test.ts
/Users/tristanzh/agent/Git-Scout/tests/scout/payloadBudget.test.ts
```

Tests must use injected clients:

```text
SourceClient
Tokenizer
BudgetLedger
StrongModelClient
Clock
```

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/scout/blindScout429.test.ts tests/scout/payloadBudget.test.ts
```

Expected: fail because scout, retry, tokenizer, and budget modules do not exist.

- [ ] **Step 2: Implement retry policy and source client boundary**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/scout/sourceClient.ts
/Users/tristanzh/agent/Git-Scout/src/scout/retryPolicy.ts
```

Implementation requirements:

- Treat HTTP 429, HTTP 5xx, timeout, and connection reset as retryable.
- Use exponential backoff with jitter.
- Accept injected clock/timer for deterministic tests.
- Persist per-source cursor after each completed fetch stage.
- Do not fetch README or source code in this milestone.

- [ ] **Step 3: Implement scheduled Blind Scout flow**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/scout/scheduler.ts
/Users/tristanzh/agent/Git-Scout/src/scout/blindScout.ts
```

Implementation requirements:

- Run from local CLI or scheduler entry point.
- Consume fixture or mocked source metadata.
- Apply blacklist before LLM/token work.
- Keep only five candidates.
- Store candidate queue through atomic JSON.
- Never call external APIs in tests.

- [ ] **Step 4: Implement pre-flight tokenizer**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/token/tokenizer.ts
```

Implementation requirements:

- Count tokens on the exact serialized payload.
- Provide adapter for `js-tiktoken`.
- Allow deterministic mock tokenizer in tests.
- Record tokenizer name, model profile, input estimate, output reserve, total reserve, timestamp, and payload hash.

- [ ] **Step 5: Implement budget ledger and circuit breaker**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/token/budgetLedger.ts
/Users/tristanzh/agent/Git-Scout/src/token/circuitBreaker.ts
```

Implementation requirements:

- Pre-flight block if `input_tokens_estimated > max_input_tokens`.
- Pre-flight block if `input_tokens_estimated + output_tokens_reserved > remaining_daily_budget`.
- Reserve budget atomically before model call.
- Reconcile actual usage after model response.
- Release or mark resumable on abort before model call.

- [ ] **Step 6: Verify Milestone 2**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/scout/blindScout429.test.ts tests/scout/payloadBudget.test.ts
npm run typecheck
```

Expected:

```text
all Milestone 2 tests pass
typecheck exits 0
```

- [ ] **Step 7: Commit Milestone 2**

```bash
cd /Users/tristanzh/agent
git add Git-Scout/src/scout Git-Scout/src/token Git-Scout/tests/scout Git-Scout/fixtures
git commit -m "feat(sentinel): add blind scout and token gates"
```

## Milestone 3: Minimal Web Dashboard and Third-layer Audit Trigger

**Objective:** Build a stateless local web dashboard that renders the five-candidate queue in a three-column layout, applies Approve/Reject decisions through atomic state updates, and triggers third-layer audit jobs only through the pre-flight token gate.

**Deliverables:**

- Local Node dashboard server.
- Static three-column frontend.
- JSON-backed candidate reader.
- Atomic Approve/Reject decision endpoints.
- Blacklist mutation endpoint for reject flow.
- Audit trigger endpoint for approve flow.
- High-frequency click test proving no lock conflict with background Scout writes.

### TDD Matrix

| Test file | Test name | Arrange | Act | Assert |
| --- | --- | --- | --- | --- |
| `tests/dashboard/highFrequencyDecision.test.ts` | `high frequency approve reject clicks do not corrupt state` | Seed five candidates; run dashboard decision mutations concurrently with mocked Scout checkpoint writes. | Fire many approve/reject requests through local server. | Decision JSON parses; each candidate has one final legal decision; checkpoint remains valid. |
| `tests/dashboard/highFrequencyDecision.test.ts` | `reject atomically updates blacklist and terminal state` | Seed one candidate. | Call reject endpoint repeatedly. | Repo or owner appears once in blacklist; candidate state is `rejected_terminal`; no duplicate terminal events. |
| `tests/dashboard/auditTrigger.test.ts` | `approve creates audit job only after token preflight passes` | Mock tokenizer under budget and strong audit client. | Call approve endpoint. | Audit job is queued; budget reservation exists; strong audit trigger is called through injected client. |
| `tests/dashboard/auditTrigger.test.ts` | `approve does not trigger audit when token preflight fails` | Mock tokenizer over budget. | Call approve endpoint. | Audit job records terminal or skipped budget event; strong audit client is not called. |

### Tasks

- [ ] **Step 1: Write failing dashboard and audit trigger tests**

Create:

```text
/Users/tristanzh/agent/Git-Scout/tests/dashboard/highFrequencyDecision.test.ts
/Users/tristanzh/agent/Git-Scout/tests/dashboard/auditTrigger.test.ts
```

Tests must run against local server instances and temporary data directories. They must not open a browser or hit external URLs.

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/dashboard/highFrequencyDecision.test.ts tests/dashboard/auditTrigger.test.ts
```

Expected: fail because dashboard and audit trigger modules do not exist.

- [ ] **Step 2: Implement local dashboard server**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/dashboard/server.ts
```

Required endpoints:

```text
GET  /api/candidates
POST /api/decision/approve
POST /api/decision/reject
POST /api/audit/trigger
GET  /
```

Implementation requirements:

- Validate every request body with schema.
- Use atomic JSON mutation for decisions, blacklist, audit jobs, and checkpoint.
- Keep server stateless; authoritative state is local JSON.
- Inject audit trigger dependency for tests.

- [ ] **Step 3: Implement minimal three-column frontend**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/web/index.html
/Users/tristanzh/agent/Git-Scout/src/web/app.js
/Users/tristanzh/agent/Git-Scout/src/web/styles.css
```

Layout requirements:

- Left column: five candidate leads.
- Center column: artifact theater.
- Right column: value promise, token estimate, Approve, Reject.
- No dependency on `/Users/tristanzh/agent/web`.
- No visible instructional copy beyond necessary labels.

- [ ] **Step 4: Implement audit job trigger**

Create:

```text
/Users/tristanzh/agent/Git-Scout/src/audit/auditPack.ts
/Users/tristanzh/agent/Git-Scout/src/audit/auditTrigger.ts
```

Implementation requirements:

- Build bounded audit pack only from digest, file tree, selected snippets, artifact index, and TZ note.
- Serialize payload.
- Run pre-flight token estimator.
- Reserve budget.
- Queue strong audit job.
- Never send raw README, entire repo source, or unbounded pages.

- [ ] **Step 5: Verify Milestone 3**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/dashboard/highFrequencyDecision.test.ts tests/dashboard/auditTrigger.test.ts
npm run typecheck
```

Expected:

```text
all Milestone 3 tests pass
typecheck exits 0
```

- [ ] **Step 6: Manual local smoke check**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run scout:seed
npm run dashboard
```

Expected:

```text
Local dashboard listening on http://127.0.0.1:<port>
```

Open the local URL and verify:

- three-column layout renders;
- five candidates appear;
- Approve writes an audit job;
- Reject updates blacklist;
- repeated clicks do not break JSON state.

- [ ] **Step 7: Commit Milestone 3**

```bash
cd /Users/tristanzh/agent
git add Git-Scout/src/dashboard Git-Scout/src/web Git-Scout/src/audit Git-Scout/tests/dashboard
git commit -m "feat(sentinel): add local dashboard audit gate"
```

## Final Acceptance Gate

Run after all three milestones:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test
npm run typecheck
```

Expected:

```text
all tests pass
typecheck exits 0
```

Then verify state durability:

```bash
cd /Users/tristanzh/agent/Git-Scout
find data -name "*.json" -print0 | xargs -0 -n1 node -e 'const fs=require("fs"); JSON.parse(fs.readFileSync(process.argv[1],"utf8"));'
```

Expected:

```text
no JSON parse errors
```

## Execution Rules

- Do not implement any milestone without first adding its failing tests.
- Do not call live GitHub, RSS, OpenAI, DeepSeek, or any paid API in tests.
- Do not stage unrelated dirty files outside `Git-Scout/`.
- Do not touch `/Users/tristanzh/agent/web` in this implementation.
- Do not store API keys in source, fixtures, logs, or reports.
- Do not proceed to Milestone 2 until Milestone 1 verification passes.
- Do not proceed to Milestone 3 until Milestone 2 verification passes.

## Self-review Coverage

- Milestone 1 covers the SDD requirements for Atomic JSON Write, `os.replace` parity, checkpoint rebuild, and `SIGINT` / `SIGTERM` durability.
- Milestone 2 covers Blind Scout, HTTP 429 exponential backoff, pre-flight token budgeting with tokenizer estimates, and post-reservation circuit breaking.
- Milestone 3 covers local three-column dashboard interaction, high-frequency approve/reject writes, blacklist updates, and third-layer audit triggering through the token gate.
