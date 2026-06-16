# Project Sentinel v3 Query Timeout Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an 8000ms per-query timeout guard so one hung GitHub Search batch cannot block Sentinel's daily runtime.

**Architecture:** RealSourceAdapter will expand existing `github_search_queries` into serial query batches, execute each batch with an independent `AbortController`, and continue after timeout. Timeout evidence is written to `source_query_checkpoint.json` under the current runtime shadow directory and to existing NDJSON logs as `github_query_timeout_skipped`.

**Tech Stack:** TypeScript, Node.js `AbortController`, Vitest fake timers, existing Sentinel atomic file-store adapter, existing Runtime shadow directory.

---

## Files

- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - Add `signal?: AbortSignal` to `HttpRequestSpec`.
  - Add `QueryBatch`, `SourceQueryBatchStatus`, and checkpoint result types.
  - Add query batch expansion and per-batch timeout execution.
  - Persist `source_query_checkpoint.json`.
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`
  - Pass `request.signal` into `fetchImpl`.
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
  - Add Stage 9 Red tests using `vi.useFakeTimers()`.

## Task 1: Red Tests for Query Timeout Guard

- [ ] **Step 1: Add fake-timer test setup**

In `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`, add `vi.useRealTimers()` to `afterEach` so Stage 9 fake timers cannot leak into existing tests.

- [ ] **Step 2: Add hung batch abort test**

Add a test that configures two search queries. Query A returns a never-resolving Promise and captures `request.signal`. After `vi.advanceTimersByTimeAsync(8000)`, assert Query A's signal is aborted and the adapter does not crash.

Expected Red result before implementation:

```text
expected undefined to be true
```

- [ ] **Step 3: Add continuity and candidate inheritance test**

Add a test where Query A hangs, Query B returns two high-trust repositories, and README fetch returns high-trust content. Assert the final candidates contain only Query B repos and no runtime crash occurs.

Expected Red result before implementation:

```text
test does not observe Query B because Query A never progresses
```

- [ ] **Step 4: Add log/checkpoint test**

Add a test that expects `github_query_timeout_skipped` in logger events and `source_query_checkpoint.json` with `QUERY_TIMEOUT_SKIPPED`.

Expected Red result before implementation:

```text
expected logger/checkpoint call not found
```

- [ ] **Step 5: Run Stage 9 Red test**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: existing RealSourceAdapter tests pass, new Stage 9 tests fail for missing timeout behavior.

## Task 2: Minimal Interface Expansion

- [ ] **Step 1: Extend request type only**

In `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`, extend:

```ts
export type HttpRequestSpec = {
  url: string;
  headers: Record<string, string>;
  timeout_ms: number;
  source_id: string;
  idempotency_key: string;
  signal?: AbortSignal;
};
```

This is a type-only contract expansion. It must not implement business timeout behavior in Red phase.

- [ ] **Step 2: Run typecheck**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
```

Expected: pass.

## Task 3: Green Implementation

- [ ] **Step 1: Add query batch types**

Add:

```ts
type QueryBatch = {
  version: 1;
  batch_id: string;
  query_id: string;
  q: string;
  sort: GitHubRepositorySearchQuery["sort"];
  order: GitHubRepositorySearchQuery["order"];
  page: number;
  per_page: number;
  timeout_ms: 8000;
  idempotency_key: string;
};

type SourceQueryCheckpoint = {
  batch_id: string;
  query_id: string;
  status: "QUERY_SUCCESS" | "QUERY_TIMEOUT_SKIPPED" | "QUERY_RATE_LIMITED";
  attempts: number;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  timeout_ms: 8000;
  url_hash: string;
  skipped_reason?: "TIMEOUT_SKIPPED" | "RATE_LIMIT_SKIPPED";
};
```

- [ ] **Step 2: Expand query batches**

Create batches from each enabled query and page while preserving matrix order.

- [ ] **Step 3: Run each batch with `AbortController`**

For each batch:

```ts
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(new Error("GITHUB_QUERY_TIMEOUT")), 8000);
try {
  await deps.http.getJson({ ...request, signal: controller.signal });
} finally {
  clearTimeout(timer);
}
```

- [ ] **Step 4: Continue after timeout**

Catch `AbortError`, `ABORT_ERR`, `ERR_CANCELED`, or `GITHUB_QUERY_TIMEOUT`; write checkpoint and log, then continue to the next batch.

- [ ] **Step 5: Persist checkpoint**

Write `/sources/source_query_checkpoint.json` through `deps.fileStore.writeJsonAtomic`.

- [ ] **Step 6: Pass `signal` through CLI**

In `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`, pass `request.signal` into `fetchImpl`.

## Task 4: Verification and Commit

- [ ] **Step 1: Run target tests**

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: all RealSourceAdapter tests pass.

- [ ] **Step 2: Run full tests and typecheck**

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npm test
```

Expected: all tests pass.

- [ ] **Step 3: Commit scoped files only**

```bash
cd /Users/tristanzh/agent
git add \
  docs/superpowers/specs/2026-06-16-project-sentinel-v3-query-timeout-guard-implementation-plan.md \
  Git-Scout/src/sentinel/realSourceAdapter.ts \
  Git-Scout/src/sentinel/runtimeOrchestratorCli.ts \
  Git-Scout/tests/sentinel/realSourceAdapter.test.ts
git commit -m "fix(sentinel): 实现 Stage 9 子查询超时熔断与连续性步进"
```

## Self-Review

- Spec coverage: covers AbortController, fake timers, query continuity, logging, checkpoint, and shadow isolation.
- Incomplete-section scan: no deferred implementation sections.
- Type consistency: uses existing `RealSourceAdapterConfig`, `HttpRequestSpec`, and fileStore contracts.
