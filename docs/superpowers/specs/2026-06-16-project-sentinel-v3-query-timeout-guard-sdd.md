# Project Sentinel v3 Query Batch Timeout Guard SDD

Date: 2026-06-16
Status: Draft for red-line specification review
Owner: TZ
Baseline commit: `52c6729`
Parent SDD:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-real-source-adapter-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-source-tightening-sdd.md`
Implementation root: `/Users/tristanzh/agent/Git-Scout`
Live probe evidence:
- `npm run sentinel:daily -- --live-network=true --live-model=false --live-publish=false` after `52c6729` did not return within the manual operational window and was interrupted with `SIGINT`.
- Probable failure surface: GitHub Search or Contents request hanging during the larger SourcePlan v2 matrix.

## 1. Objective

Stage 9 adds a network throughput guard around RealSourceAdapter's GitHub query execution. Stage 8.1 connected `SourcePlan v2` and `ArtifactHintGuard` into production, but the live probe showed that a larger query matrix can hang long enough to make daily runtime unsafe.

This stage must ensure that one slow GitHub sub-query cannot block the entire runtime:

```text
SourcePlan v2
  -> QueryBatch[] ordered by matrix entry and page
  -> Per-batch AbortController with 8000ms deadline
  -> On success: normalize items and continue
  -> On timeout: write TIMEOUT_SKIPPED checkpoint and NDJSON event
  -> Continue to next batch
  -> Preserve all candidates collected before timeout
```

The goal is not to make public network collection faster. The goal is to make it bounded, observable, resumable, and unable to hang local cron or the future Agent07 manual pull button.

## 2. Non-Goals

- Do not change `ArtifactHintGuard` scoring, reason codes, or linear scan implementation.
- Do not add live model calls.
- Do not publish to `data/scout_pipeline.json`.
- Do not introduce a global queue, Redis, SQLite, daemon, or worker pool.
- Do not parallelize the entire GitHub matrix by default.
- Do not retry a hung Search query indefinitely.
- Do not treat a timed-out sub-query as a terminal runtime failure when other sub-queries remain.
- Do not use `git clone`, GitHub HTML Trending, or repository source tree fetches.

## 3. Problem Statement

`SourcePlan v2` deliberately replaced a broad single query with multiple high-intent queries. This improves candidate purity, but it increases the number of Search requests. The second live probe after Stage 8.1 showed that the CLI can remain silent for more than two minutes while using live network and mock model mode.

Current risk:

- a single GitHub Search request can hang longer than the daily runtime budget;
- the runtime has no per-query skip marker;
- NDJSON logs only show runtime start/completion, not which query is hanging;
- future UI manual pull would look frozen;
- future cron would risk overlapping daily runs if the previous run never exits.

The fix must be at the query batch boundary, not at the dashboard boundary.

## 4. Query Matrix v2 Linear Slicing

### 4.1 QueryBatch Contract

Every enabled `QueryMatrixEntry` from `SourcePlan v2` must be expanded into atomic query batches. A batch is one GitHub Search URL request for one query id and one page.

```ts
type QueryBatch = {
  version: 1;
  batch_id: string;          // `${query.id}:page:${page}`
  query_id: string;
  intent: SourcePlanV2Intent;
  q: string;
  sort: "updated" | "stars";
  order: "desc";
  page: number;
  per_page: number;
  timeout_ms: 8000;
  idempotency_key: string;   // same as batch_id unless future checkpoint version changes it
};
```

Expansion rules:

- preserve the order of `SourcePlanV2.github_query_matrix`;
- skip disabled query entries before creating batches;
- for each enabled entry, create page batches from `page_start = 1` through `page_limit`;
- clamp `page_limit` to `config.github.max_pages_per_query`;
- clamp `per_page` to `config.github.per_page`;
- do not merge topic queries into longer OR queries;
- do not create a batch with `timeout_ms > 8000`.

Example:

```text
topic_layout_engine page 1
topic_layout_engine page 2
topic_vector_graphics page 1
topic_vector_graphics page 2
readme_constraint_layout_engine page 1
...
```

### 4.2 Execution Mode

The default execution mode is linear serial execution:

```text
for batch of query_batches:
  runSearchBatch(batch)
  if timeout:
    mark skipped
    continue
```

This is intentionally conservative. GitHub Search has strict rate limits; concurrency is less valuable than deterministic forward progress. A future SDD may add `max_search_concurrency = 2`, but Stage 9 must ship serial execution first.

## 5. AbortController Timeout Guard

### 5.1 Single Batch Lifecycle

Each `QueryBatch` owns a fresh `AbortController`.

```ts
type QueryBatchRuntime = {
  batch: QueryBatch;
  controller: AbortController;
  started_at: string;
  deadline_at: string;
  timer: NodeJS.Timeout;
};
```

Lifecycle:

1. Create `AbortController`.
2. Start an 8000ms timer.
3. Pass `controller.signal` into the HTTP client's Search request.
4. If the timer fires, call `controller.abort(new Error("GITHUB_QUERY_TIMEOUT"))`.
5. Catch the abort error at the adapter boundary.
6. Clear the timer in `finally`.
7. Do not reuse the controller for any other request.

### 5.2 Required HTTP Client Contract

The injected HTTP client must support an optional `signal` field:

```ts
type HttpRequestSpec = {
  url: string;
  headers: Record<string, string>;
  timeout_ms: number;
  source_id: string;
  idempotency_key: string;
  signal?: AbortSignal;
};
```

The CLI `fetchImpl` adapter must pass this signal to `fetch(url, { headers, signal })`.

The test adapter must be able to detect `signal.aborted` and reject with an `AbortError`-compatible error:

```ts
type QueryTimeoutError = Error & {
  name: "AbortError" | "TimeoutError";
  code?: "ABORT_ERR" | "ERR_CANCELED" | "GITHUB_QUERY_TIMEOUT";
};
```

### 5.3 Abort Classification

The source adapter must classify these as timeout-skipped, not terminal:

- `error.name === "AbortError"`;
- `error.code === "ABORT_ERR"`;
- `error.code === "ERR_CANCELED"`;
- `error.message` contains `GITHUB_QUERY_TIMEOUT`;
- `signal.aborted === true` when the catch block runs.

Other network errors remain recoverable or terminal according to existing Stage 7 rules.

## 6. Fault-Tolerant Skipping Workflow

### 6.1 Search Batch State Machine

Stage 9 adds query-level statuses:

```ts
type SourceQueryBatchStatus =
  | "QUERY_PENDING"
  | "QUERY_RUNNING"
  | "QUERY_SUCCESS"
  | "QUERY_RATE_LIMITED"
  | "QUERY_TIMEOUT_SKIPPED"
  | "QUERY_FAILED_RECOVERABLE"
  | "QUERY_FAILED_TERMINAL";
```

The adapter must update in-memory and shadow checkpoint state with:

```ts
type SourceQueryCheckpoint = {
  batch_id: string;
  query_id: string;
  status: SourceQueryBatchStatus;
  attempts: number;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  timeout_ms: 8000;
  url_hash: string;
  skipped_reason?: "TIMEOUT_SKIPPED" | "RATE_LIMIT_SKIPPED";
};
```

The URL hash prevents leaking very long query URLs into compact checkpoint summaries while still allowing dedupe and replay. The full URL belongs in the NDJSON runtime log because logs are the debugging surface.

### 6.2 Checkpoint Location

Source-level checkpoint data must live under the current run shadow directory:

```text
storage/runtime_shadow/<run_id>/sources/source_query_checkpoint.json
```

Rules:

- write with temp-file plus atomic rename;
- never write to `data/scout_pipeline.json`;
- keep successful batches even if later batches timeout;
- preserve prior successful candidates;
- write timeout-skipped status before moving to the next batch.

### 6.3 Continue-on-Timeout Semantics

When one batch times out:

```text
catch timeout
  mark batch QUERY_TIMEOUT_SKIPPED
  log github_query_timeout_skipped
  continue next batch
```

The adapter must not:

- clear `itemsByRepo`;
- clear already fetched README digests;
- clear `shadow_evidence`;
- return `FAILED_TERMINAL`;
- publish anything.

The final RealSourceAdapter status remains `COMPLETED` if at least one batch finished or all batches were skipped without a rate-limit circuit breaker. The result must include a warning count:

```ts
type RealSourceAdapterResult = {
  // existing fields
  query_batches: {
    total: number;
    completed: number;
    timeout_skipped: number;
    failed_recoverable: number;
  };
};
```

If every batch times out, return `FAILED_RECOVERABLE` only if the implementation can do so without breaking existing runtime semantics. Otherwise return `COMPLETED` with zero candidates and `timeout_skipped = total`; the TDD phase must lock one behavior. Recommended behavior: `COMPLETED` with zero candidates, because the runtime is still healthy and shadow-only.

## 7. NDJSON Structured Logging

The existing log path remains:

```text
storage/logs/sentinel_daily_<date>.log
```

When a query batch times out, write one NDJSON line:

```json
{
  "timestamp": "2026-06-16T09:01:08.123Z",
  "level": "WARN",
  "component": "realSourceAdapter.github",
  "event": "github_query_timeout_skipped",
  "meta": {
    "run_id": "runtime_20260616T090100Z",
    "batch_id": "topic_layout_engine:page:1",
    "query_id": "topic_layout_engine",
    "url": "https://api.github.com/search/repositories?...",
    "duration_ms": 8004,
    "timeout_ms": 8000,
    "page": 1,
    "per_page": 50,
    "github_token_status": "set"
  }
}
```

Requirements:

- `event` must be exactly `github_query_timeout_skipped`;
- `duration_ms >= timeout_ms`;
- include `run_id`;
- include `batch_id`;
- include the affected query URL;
- mask or omit any Authorization token;
- log through the existing NDJSON logger, not `console.log`;
- logging failure must not crash the runtime, but it must surface as a warning in the adapter result.

## 8. Shadow Containment and Production Safety

Timeout handling must obey all Stage 6 runtime rules:

- production `data/scout_pipeline.json` is read-only unless `--live-publish=true` and `dry_run=false`;
- timeout checkpoints remain under `storage/runtime_shadow/<run_id>/sources/`;
- incomplete runtime shadow directories remain inspectable;
- no timeout path may call `publisher.atomicRename`;
- no timeout path may call a real model;
- already filtered `LOW_QUALITY_FILTERED` evidence remains in `shadow_evidence`;
- already captured candidates remain candidates unless they themselves fail later quality gates.

## 9. Interaction with Existing Rate-Limit Handling

Timeout skip is distinct from GitHub 403/429 handling.

| Event | Existing/Stage | Behavior |
| --- | --- | --- |
| HTTP 403 primary limit | Stage 7 | parse reset, backoff, retry/circuit breaker |
| HTTP 429 | Stage 7 | parse retry-after/reset, backoff, retry/circuit breaker |
| Search request abort after 8000ms | Stage 9 | log timeout skipped, mark checkpoint, continue |
| Contents/README request abort after 8000ms | Future extension unless included in TDD | mark repo README fetch recoverable, do not create candidate without README |

Stage 9 must implement Search query timeout first. README timeout may be included if implementation cost is low, but Search timeout is the mandatory scope because the live hang occurred before useful completion output.

## 10. TDD Matrix

### 10.1 Hung Search Request Abort

Fixture:

- SourcePlan has two enabled query batches.
- First batch's mocked `getJson` never resolves until its `AbortSignal` aborts.
- Second batch returns one valid high-trust repository.

Assertions:

- first batch receives an `AbortSignal`;
- signal becomes aborted at 8000ms;
- adapter logs `github_query_timeout_skipped`;
- adapter does not throw;
- adapter still executes the second batch.

### 10.2 Candidate Preservation Across Timeout

Fixture:

- First batch succeeds with `github/high-trust-layout`;
- second batch hangs and is aborted;
- third batch succeeds with `github/typesetting-engine`.

Assertions:

- final candidates include both successful repos;
- timed-out batch appears in `source_query_checkpoint.json` as `QUERY_TIMEOUT_SKIPPED`;
- successful candidates are not discarded when a later batch times out.

### 10.3 Shadow Containment

Fixture:

- Runtime orchestrator uses live source adapter with one hung batch.
- `live_publish=false`.
- production `data/scout_pipeline.json` contains previous stable data.

Assertions:

- production JSON remains byte-for-byte unchanged;
- shadow path contains valid parseable JSON;
- no call to `publisher.atomicRename`;
- `source_query_checkpoint.json` exists under the current run shadow directory.

### 10.4 Log Redaction and Event Shape

Fixture:

- env includes `GITHUB_TOKEN=ghp_secret_value_for_test`.
- query timeout occurs.

Assertions:

- NDJSON line includes `github_token_status: "set"`;
- NDJSON line does not contain `ghp_secret_value_for_test`;
- event includes `url`, `duration_ms`, `timeout_ms`, `batch_id`, and `run_id`;
- `duration_ms` is at least `8000`.

### 10.5 No Event Loop Deadlock

Fixture:

- test uses fake timers or injected sleep/clock;
- one batch hangs until abort;
- one later batch succeeds immediately.

Assertions:

- test completes without real 8-second wait;
- implementation exposes injectable timeout scheduler or fake-timer-compatible `setTimeout`;
- all timers are cleared after each batch.

## 11. Implementation Boundaries for Next Phase

Expected files for TDD/implementation:

- `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - add `QueryBatch` expansion;
  - add per-batch `AbortController`;
  - add timeout classification;
  - write source query checkpoint.
- `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`
  - pass `AbortSignal` through `fetchImpl`;
  - preserve existing live/model/publish gates.
- `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
  - add timeout/continue tests.
- `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts`
  - add shadow containment regression if not already covered by adapter tests.

Forbidden implementation shortcuts:

- do not use one shared AbortController for all batches;
- do not use `Promise.race` without aborting the actual HTTP request;
- do not swallow timeout without checkpoint/log evidence;
- do not convert timeout into a process-level crash;
- do not use `git add .` when committing.

## 12. Acceptance Criteria

Stage 9 is complete only when:

- every Search query batch has an independent 8000ms timeout;
- the timeout calls `AbortController.abort()`;
- timeout produces `github_query_timeout_skipped` NDJSON;
- timeout writes `QUERY_TIMEOUT_SKIPPED` to shadow checkpoint;
- later query batches continue after one timeout;
- already collected candidates are preserved;
- production pipeline remains unchanged in dry-run;
- all existing tests pass;
- new timeout tests pass;
- `npm run typecheck` passes.

## 13. Spec Self-Review

- Incomplete-section scan: no deferred sections.
- Scope check: focused only on GitHub Search query timeout and skip behavior; README timeout is explicitly future/optional.
- Contract consistency: uses existing Runtime shadow, NDJSON, SourcePlan v2, RealSourceAdapter, and HintGuard boundaries.
- Risk boundary: live publish remains blocked unless Stage 6 gates explicitly allow it.
