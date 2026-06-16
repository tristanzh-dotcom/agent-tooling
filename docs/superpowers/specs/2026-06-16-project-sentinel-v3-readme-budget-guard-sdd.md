# Project Sentinel v3 README Rate-Limit Budget Guard SDD

Date: 2026-06-16
Status: Draft for red-line specification review
Owner: TZ
Sentinel baseline commit: `bdf7233`
Live probe evidence:
- Command: `npm run sentinel:daily -- --live-network=true --live-model=false --live-publish=false`
- Run ID: `runtime_20260616T101428Z`
- Result: process exceeded the 2 minute operational probe window and was manually interrupted with `SIGINT`, exit code `130`.
- Last structured event: `github_rate_limit_backoff` for `dataficationsdk/verso`, `status=403`, `rate_limit_kind=PRIMARY_RATE_LIMIT`, `retry_count=1`, `github_token_status=unset`.
- Shadow residue: `60` README digest files existed, but `scout_pipeline.shadow.json`, `source_candidates.runtime.json`, and `source_query_checkpoint.json` were not created for the interrupted run.
Parent SDDs:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-real-source-adapter-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-query-timeout-guard-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-lead-scorer-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
Implementation root: `/Users/tristanzh/agent/Git-Scout`

## 1. Objective

Stage 9.2 adds a README-phase budget guard around RealSourceAdapter. Stage 9 bounded socket-level GitHub Search hangs with per-query `AbortController`; Stage 9.1 improved lead purity after successful source collection. Probe `runtime_20260616T101428Z` exposed a different failure class:

```text
HTTP request returned quickly
  -> GitHub responded 403 Primary Rate Limit
  -> adapter parsed x-ratelimit-reset / retry-after
  -> adapter entered long local sleep
  -> HTTP timeout did not apply because socket was already closed
  -> runtime stayed alive past the 2 minute probe window
  -> SIGINT stopped process before structured shadow JSON was flushed
```

The fix is a budgeted state machine for README collection. The system must never obediently sleep for an unbounded GitHub reset window during local daily runtime. It must cap compliant sleep, flush structured shadow evidence incrementally, and move forward with partial results when the README phase wall-clock budget is exhausted.

## 2. Non-Goals

- Do not change `LeadPromotionScorer` weights, stable sorting, or overflow semantics.
- Do not loosen `ArtifactHintGuard`.
- Do not publish dry-run results to `data/scout_pipeline.json`.
- Do not add live model calls.
- Do not add a database, Redis queue, cron daemon, or background service.
- Do not blindly ignore all GitHub rate limits. Respect short backoff windows under a strict cap; reject long sleeps.
- Do not retry README fetches forever.
- Do not convert a partially successful source collection into a terminal failure when enough candidates already exist for downstream scoring.
- Do not rely on human SIGINT as a normal control path.

## 3. Problem Statement

The current `realSourceAdapter` has two different timing controls:

1. Per-HTTP request timeout via CLI `fetchWithTimeout`.
2. GitHub rate-limit backoff via `deps.sleep(rateLimitDelayMs(...))`.

The first path is bounded. The second path can be arbitrarily long. Under unauthenticated GitHub usage, Primary Rate Limit reset windows can be minutes or longer. Because that wait happens after a completed HTTP response, `AbortController` no longer protects runtime wall-clock.

Observed consequence:

- 41 low-quality guard events were logged before the stall;
- `readme_fetch_truncated` and digest writes proved the adapter made progress;
- the last event was `github_rate_limit_backoff`;
- no final shadow JSON existed, so the 41 completed decisions were not recoverable from the normal dashboard-facing contract;
- production data remained safe only because `--live-publish=false`.

Stage 9.2 must make the README phase bounded and evidence-preserving.

## 4. Core Runtime Constants

Stage 9.2 introduces explicit budget constants. These must be configurable in `RealSourceAdapterConfig.github`, with these defaults in the CLI:

```ts
type ReadmeBudgetConfig = {
  max_compliant_sleep_ms: 5000;
  readme_phase_wall_clock_budget_ms: 45_000;
  incremental_flush_every_repos: 1;
  max_readme_rate_limit_retries: 1;
};
```

Default contract:

| Constant | Default | Meaning |
|---|---:|---|
| `max_compliant_sleep_ms` | `5000` | Maximum allowed sleep for a GitHub README 403/429 before skipping or throttling. |
| `readme_phase_wall_clock_budget_ms` | `45000` | Maximum wall-clock time from first README fetch attempt to source scoring handoff. |
| `incremental_flush_every_repos` | `1` | Flush structured shadow state after every repo state transition. |
| `max_readme_rate_limit_retries` | `1` | At most one short compliant retry per README repo. |

The budget must be measured with a monotonic runtime clock where possible. In Node.js implementation, prefer injected `now()` for deterministic tests, but the implementation must account for fake timers and not rely on real 45 second sleeps in unit tests.

## 5. Capped Sleep Strategy

### 5.1 README Rate-Limit Classification

When README fetch returns `403` or `429`, classify it before sleeping:

```ts
type ReadmeRateLimitKind =
  | "PRIMARY_RATE_LIMIT"
  | "SECONDARY_RATE_LIMIT"
  | "UNKNOWN_RATE_LIMIT";
```

Classification rules:

- `x-ratelimit-remaining === "0"` means `PRIMARY_RATE_LIMIT`;
- 403 without primary exhaustion is `SECONDARY_RATE_LIMIT`;
- 429 is `SECONDARY_RATE_LIMIT` unless headers clearly indicate primary exhaustion;
- missing or malformed rate headers become `UNKNOWN_RATE_LIMIT`.

### 5.2 Capped Sleep Decision

```ts
type ReadmeBackoffDecision =
  | {
      action: "SLEEP_AND_RETRY";
      sleep_ms: number;
      reason: "SHORT_COMPLIANT_BACKOFF";
    }
  | {
      action: "SKIP_REPO";
      status: "README_RATE_LIMIT_SKIPPED";
      reason: "COMPLIANT_SLEEP_EXCEEDED" | "README_RETRY_BUDGET_EXHAUSTED";
      requested_sleep_ms: number;
    }
  | {
      action: "STOP_README_PHASE";
      status: "README_RATE_LIMIT_EXCEEDED";
      reason: "PRIMARY_RATE_LIMIT_LONG_SLEEP" | "GLOBAL_README_BUDGET_EXHAUSTED";
      requested_sleep_ms: number;
    };
```

Decision rules:

1. Compute `requested_sleep_ms = rateLimitDelayMs(headers, now)`.
2. If `requested_sleep_ms <= max_compliant_sleep_ms` and retry count is below `max_readme_rate_limit_retries`, sleep and retry.
3. If `requested_sleep_ms > max_compliant_sleep_ms` and the kind is `PRIMARY_RATE_LIMIT`, stop the README phase immediately with `README_RATE_LIMIT_EXCEEDED`.
4. If `requested_sleep_ms > max_compliant_sleep_ms` and the kind is secondary or unknown, skip the current repo with `README_RATE_LIMIT_SKIPPED`.
5. Never call `deps.sleep()` with a value greater than `max_compliant_sleep_ms`.

This is the key constitutional rule for Stage 9.2.

## 6. Global README Wall-Clock Budget

### 6.1 Budget Start

Set `readme_phase_started_at_ms` immediately before the adapter begins iterating `itemsByRepo` for README fetches.

```ts
const readmePhaseStartedAt = deps.now().getTime();
```

### 6.2 Budget Checkpoints

Before every repo fetch attempt:

```ts
if (deps.now().getTime() - readmePhaseStartedAt >= config.github.readme_phase_wall_clock_budget_ms) {
  mark remaining phase as GLOBAL_BUDGET_EXHAUSTED;
  break;
}
```

After every short compliant sleep:

```ts
if (deps.now().getTime() - readmePhaseStartedAt >= config.github.readme_phase_wall_clock_budget_ms) {
  stop README phase before retrying the same repo;
}
```

### 6.3 Runtime Outcome

If budget is exhausted after collecting at least one passable candidate, the adapter returns `COMPLETED_WITH_SOURCE_WARNINGS` or keeps existing `COMPLETED` with warnings metadata. The implementation plan must choose the smaller type change, but the shadow JSON must expose the warning.

If no usable candidates exist, the adapter returns `SOURCE_THROTTLED` with reason `GLOBAL_README_BUDGET_EXHAUSTED`.

## 7. Segmented Incremental Shadow Flush

### 7.1 Current Failure

Probe `runtime_20260616T101428Z` wrote README digest files but not structured source outputs. That means completed guard decisions were only recoverable from NDJSON logs, not from the normal `scout_pipeline.shadow.json` contract.

### 7.2 Required Shadow Flush Contract

The adapter must flush a compact source-stage snapshot after every state transition:

- README fetched and truncated;
- candidate passed `ArtifactHintGuard` and was added to promotion input;
- candidate was moved into `shadow_evidence` by `ArtifactHintGuard`;
- candidate was skipped due to README rate limit;
- README phase budget was exhausted;
- source status changed to throttled or completed with warnings.

Flush target:

```text
storage/runtime_shadow/<run_id>/sources/source_stage_snapshot.json
```

Snapshot schema:

```ts
type SourceStageSnapshot = {
  version: 1;
  run_id: string;
  updated_at: string;
  status:
    | "SOURCE_RUNNING"
    | "SOURCE_PARTIAL"
    | "SOURCE_THROTTLED"
    | "SOURCE_READY_FOR_SCORING";
  counters: {
    search_requests: number;
    readme_requests: number;
    promotion_inputs: number;
    shadow_evidence: number;
    low_relevance_overflow: number;
    skipped_readmes: number;
  };
  candidates_preview: RuntimeCandidate[];
  promotion_inputs_preview: LeadPromotionInput[];
  shadow_evidence: RuntimeShadowEvidence;
  readme_skip_evidence: Record<string, ReadmeSkipEvidence>;
  latest_event: SourceStageEvent;
};
```

This file is not the final dashboard contract. It is the crash-resume and forensic contract for an interrupted source stage.

### 7.3 Final Shadow Pipeline Flush

When source collection exits normally or partially:

1. Run `LeadPromotionScorer` on current promotion inputs.
2. Write `source_candidates.runtime.json`.
3. Write `source_candidates.envelope.json`.
4. Write `scout_pipeline.shadow.json` through `RuntimeOrchestrator` as before.
5. Preserve `shadow_evidence`, `low_relevance_overflow`, and `readme_skip_evidence`.

If source exits early due to `README_RATE_LIMIT_EXCEEDED`, it must still run scoring on already collected promotion inputs unless zero inputs exist.

## 8. README Skip Evidence

Stage 9.2 adds source evidence for rate-limit-induced README skips.

```ts
type ReadmeSkipEvidence = {
  repo: string;
  status:
    | "README_RATE_LIMIT_SKIPPED"
    | "README_RATE_LIMIT_EXCEEDED"
    | "GLOBAL_BUDGET_EXHAUSTED";
  source: "readme_budget_guard";
  captured_at: string;
  evidence: {
    http_status?: 403 | 429;
    rate_limit_kind?: ReadmeRateLimitKind;
    requested_sleep_ms?: number;
    max_compliant_sleep_ms: number;
    readme_phase_elapsed_ms: number;
    retry_count: number;
    github_token_status: "set" | "unset";
    decision: ReadmeBackoffDecision["action"];
  };
};
```

Storage location options:

- Preferred: `scout_pipeline.shadow.json.readme_skip_evidence`.
- Also allowed: `source_stage_snapshot.json.readme_skip_evidence` during mid-run.

These skipped repos must not call Blind Scout, Capturer, or Hardcore Auditor.

## 9. NDJSON Logging Enhancements

Every capped-sleep decision must emit a structured NDJSON event.

### 9.1 Short Sleep

```json
{
  "level": "WARN",
  "component": "realSourceAdapter.github",
  "event": "readme_rate_limit_short_backoff",
  "meta": {
    "run_id": "runtime_...",
    "repo": "owner/name",
    "status": 403,
    "rate_limit_kind": "SECONDARY_RATE_LIMIT",
    "requested_sleep_ms": 2500,
    "max_compliant_sleep_ms": 5000,
    "retry_count": 1,
    "github_token_status": "unset"
  }
}
```

### 9.2 Long Sleep Rejected

```json
{
  "level": "WARN",
  "component": "realSourceAdapter.github",
  "event": "readme_rate_limit_sleep_rejected",
  "meta": {
    "run_id": "runtime_...",
    "repo": "owner/name",
    "status": 403,
    "rate_limit_kind": "PRIMARY_RATE_LIMIT",
    "requested_sleep_ms": 900000,
    "max_compliant_sleep_ms": 5000,
    "decision": "STOP_README_PHASE",
    "github_token_status": "unset"
  }
}
```

### 9.3 Global Budget Exhausted

```json
{
  "level": "WARN",
  "component": "realSourceAdapter.github",
  "event": "readme_phase_budget_exhausted",
  "meta": {
    "run_id": "runtime_...",
    "elapsed_ms": 45000,
    "budget_ms": 45000,
    "promotion_inputs": 5,
    "shadow_evidence": 39
  }
}
```

Tokens or credentials must remain masked or represented only as `github_token_status: "set" | "unset"`.

## 10. Runtime State Machine

### 10.1 Source Status Extensions

The implementation plan should extend source-level statuses only if type changes remain contained:

```ts
type RealSourceAdapterStatus =
  | "COMPLETED"
  | "COMPLETED_WITH_SOURCE_WARNINGS"
  | "SOURCE_THROTTLED"
  | "FAILED_RECOVERABLE";
```

If maintaining the existing public union is safer, use `COMPLETED` plus warnings metadata:

```ts
type RealSourceAdapterResult = {
  warnings?: Array<{
    code:
      | "README_RATE_LIMIT_SKIPPED"
      | "README_RATE_LIMIT_EXCEEDED"
      | "GLOBAL_README_BUDGET_EXHAUSTED";
    repo?: string;
    evidence: ReadmeSkipEvidence["evidence"];
  }>;
};
```

### 10.2 Partial Success Rule

If at least one scored candidate exists:

```text
return partial source result
  -> RuntimeOrchestrator builds shadow pipeline
  -> production path remains untouched unless live-publish true and runtime status allows publish
```

Dry-run never publishes. Live-publish must not publish if source status is `SOURCE_THROTTLED` unless a future SDD explicitly allows partial publish.

## 11. Interaction With Existing Stages

| Stage | Existing guarantee | Stage 9.2 change |
|---|---|---|
| Stage 7 RealSourceAdapter | Rate-limit retry and circuit breaker | Adds cap on sleep and README phase budget. |
| Stage 8 ArtifactHintGuard | Low-quality projects move to `shadow_evidence` | Evidence must flush incrementally after each guard decision. |
| Stage 9 Query Timeout Guard | Search request timeout and skip | Does not cover post-response long sleep; Stage 9.2 fills that gap. |
| Stage 9.1 Lead Scorer | Top-5 and `low_relevance_overflow` | Must run on partial promotion inputs if README phase exits early. |
| Stage 6 RuntimeOrchestrator | Shadow-only dry-run and two-phase publish | Must preserve production zero-pollution under interrupted source collection. |

## 12. TDD Matrix for Next Stage

### Test 1: 403 Primary Rate Limit Long Sleep Rejected

Setup:

- Use fake timers.
- Mock Search to return one repo.
- Mock README fetch to return `403` with headers:
  - `x-ratelimit-remaining: "0"`;
  - `x-ratelimit-reset` far enough in the future to imply `900000ms`.
- Configure `max_compliant_sleep_ms = 5000`.

Assertions:

- `deps.sleep` is not called with a value greater than `5000`.
- Adapter returns without waiting for the reset window.
- Result contains warning or status for `README_RATE_LIMIT_EXCEEDED`.
- NDJSON includes `readme_rate_limit_sleep_rejected`.
- Production `data/scout_pipeline.json` remains untouched.

### Test 2: Short Backoff Is Allowed Once

Setup:

- Mock README first response as `429` with `retry-after: "2"`.
- Mock second response as `200`.
- Use fake timers and an injected sleep spy.

Assertions:

- `deps.sleep` receives exactly `2000`.
- README retry count is exactly `1`.
- Candidate proceeds to HintGuard and LeadPromotionScorer.
- No `README_RATE_LIMIT_EXCEEDED` warning is emitted.

### Test 3: Global README Phase Budget Stops Loop

Setup:

- Mock Search to return multiple repos.
- Mock README requests to advance injected clock by enough time to cross `45000ms`.
- The first few repos produce pass or guard-filtered decisions.

Assertions:

- Adapter stops fetching additional README after budget exhaustion.
- Already collected promotion inputs are preserved and scored.
- `readme_phase_budget_exhausted` is logged.
- Shadow result contains `GLOBAL_BUDGET_EXHAUSTED` evidence.
- No downstream model/capturer call happens for skipped repos.

### Test 4: Incremental Snapshot Survives Mid-Run Abort

Setup:

- Run adapter with a fileStore spy.
- After one guard-filtered repo and one passed repo, inject an exception or simulate SIGINT boundary at the source adapter call site.

Assertions:

- `source_stage_snapshot.json` was written before failure.
- Snapshot contains the completed `shadow_evidence` entry and promotion input preview.
- Snapshot JSON is parseable.
- Production `data/scout_pipeline.json` remains untouched.

### Test 5: Partial Result Still Reaches Scorer

Setup:

- Collect at least 7 passable candidates.
- Trigger global budget exhaustion before all repos are processed.

Assertions:

- `LeadPromotionScorer` still ranks available promotion inputs.
- `leads.length <= 5`.
- `low_relevance_overflow` is present for candidates outside Top-5.
- Runtime does not hang and returns before the test's virtual wall-clock limit.

### Test 6: Existing Query Timeout Behavior Does Not Regress

Setup:

- Reuse Stage 9 timeout fixture where Search Batch A never resolves and Batch B returns valid repos.

Assertions:

- Batch A remains `QUERY_TIMEOUT_SKIPPED`.
- Batch B still proceeds.
- README budget guard does not mask or reclassify Search timeout evidence.

## 13. Acceptance Criteria

Stage 9.2 is complete only when all of these are true:

- No code path can call `deps.sleep(ms)` with `ms > max_compliant_sleep_ms` during README rate-limit handling.
- README phase cannot exceed `readme_phase_wall_clock_budget_ms` without producing a structured skip or budget-exhausted state.
- At least one parseable `source_stage_snapshot.json` is written before long-running README loops can stall.
- Partial source collection can still produce a scored Top-5 if enough candidates were collected.
- Dry-run and interrupted runs do not touch `data/scout_pipeline.json`.
- Tests use fake timers or injected clocks; no test waits 45 seconds or 5 seconds in real time.
- Existing 40 Sentinel tests remain green after Stage 9.2 implementation.

## 14. Operational Follow-Up

After Stage 9.2 Green, rerun the master probe:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run sentinel:daily -- --live-network=true --live-model=false --live-publish=false
```

Expected operational behavior:

- run exits within the 2 minute probe window;
- if GitHub is unauthenticated and rate-limited, the run exits gracefully with structured `README_RATE_LIMIT_EXCEEDED` or `GLOBAL_BUDGET_EXHAUSTED`;
- `scout_pipeline.shadow.json` or `source_stage_snapshot.json` contains recoverable evidence;
- production `data/scout_pipeline.json` remains unchanged.
