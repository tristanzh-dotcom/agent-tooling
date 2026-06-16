# Project Sentinel v3 UI Orchestrator Integration SDD

Date: 2026-06-16
Status: Draft for red-line specification review
Owner: TZ
Sentinel baseline commit: `650d054`
Web baseline:
- `/Users/tristanzh/agent/web/docs/superpowers/specs/2026-06-15-agent07-sentinel-dashboard-sdd.md`
- `/Users/tristanzh/agent/web/docs/superpowers/specs/2026-06-16-agent07-theme-inheritance-sdd.md`
Parent Sentinel SDDs:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-query-timeout-guard-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-lead-scorer-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-readme-budget-guard-sdd.md`
Implementation roots:
- Sentinel runtime: `/Users/tristanzh/agent/Git-Scout`
- Publishing surface: `/Users/tristanzh/agent/web`

## 1. Objective

Stage 10 turns Agent07 from a passive Sentinel judgment board into a production runtime control surface.

The dashboard must expose:

```text
Runtime status -> Recent structured logs -> Shadow run evidence -> Safe manual pull trigger
```

It must not weaken any Stage 6-9.2 operational gates. The UI is an observer and a constrained trigger. It is not allowed to call RealSourceAdapter, model clients, Capturer, or publish code directly.

## 2. Scope Classification

This is a feature-required project delta for Agent07 only.

Allowed change surfaces for the later implementation phase:

- `/Users/tristanzh/agent/Git-Scout/src/sentinel/*` for a narrow runtime status/control adapter.
- `/Users/tristanzh/agent/Git-Scout/tests/sentinel/*` for TDD coverage.
- `/Users/tristanzh/agent/web/app/agent07.js` and `/Users/tristanzh/agent/web/app/agent07.css` for route-scoped UI binding.
- `/Users/tristanzh/agent/web/tests/*agent07*` for route-scoped service/browser tests.
- `/Users/tristanzh/agent/web/config/agents/agent07.contract.json` only if the route contract must expose new fields.

Forbidden change surfaces:

- Do not restyle shared `.ka-*` shell, sidebar, navigation, layout, or theme tokens.
- Do not introduce Agent07 hard-coded black/white/gray palettes. Agent07 must inherit platform theme variables.
- Do not alter unrelated agents or shared publishing paradigms.
- Do not add a long-running background daemon or websocket in this stage.
- Do not expose a UI path that can silently set `--live-model=true` or `--live-publish=true`.

## 3. First-Principles Product Contract

The dashboard user has three operational questions:

1. Is Sentinel currently running, blocked, or idle?
2. If the last run degraded, why did it degrade?
3. Can I safely start a fresh pull without polluting production data or spending model tokens?

Stage 10 therefore prioritizes observability and controlled initiation. It does not add richer aesthetic treatment to the Artifact Theater, and it does not change approve/reject semantics.

## 4. Runtime Control Safety Gates

### 4.1 Manual Trigger Mode

The primary Agent07 button is:

```text
Trigger Today's Pull
```

The button must map to a safe runtime mode:

```ts
{
  live_network: true,
  live_model: false,
  live_publish: false,
  dry_run: true
}
```

This is intentionally "Live Network / Mock Model / Shadow Only". It proves the public-source pipeline and produces inspectable shadow results without invoking real model spend or mutating `data/scout_pipeline.json`.

### 4.2 Forbidden UI Gate Escalation

The Agent07 UI must not provide a one-click path to:

```text
--live-model=true
--live-publish=true
```

If future work needs a publish button, it requires a separate SDD with:

- explicit two-step confirmation,
- visible target run id,
- production diff preview,
- token budget estimate,
- rollback plan.

### 4.3 Single-Flight Runtime Lock

Manual trigger requests must be single-flight per local runtime:

```ts
type RuntimeTriggerState =
  | "IDLE"
  | "STARTING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "BLOCKED_BY_EXISTING_RUN";
```

If a run is active, a second click must return:

```json
{
  "ok": false,
  "error": "RUNTIME_ALREADY_RUNNING",
  "active_run_id": "runtime_20260616T..."
}
```

The frontend must disable the trigger button immediately on click and keep it disabled until the service reports `IDLE`, `COMPLETED`, or `FAILED`.

## 5. Backend API Contract

Stage 10 adds a thin Agent07 runtime service. The service composes RuntimeOrchestrator and filesystem observers through dependency injection.

### 5.1 GET `/api/agent07/runtime/status`

Returns the latest operational state without starting work.

```ts
type Agent07RuntimeStatusResponse = {
  version: 1;
  generated_at: string;
  active_run: null | {
    run_id: string;
    date: string;
    status: RuntimeTriggerState;
    started_at: string;
    elapsed_ms: number;
    gates: {
      live_network: boolean;
      live_model: boolean;
      live_publish: boolean;
      dry_run: boolean;
    };
  };
  latest_run: null | {
    run_id: string;
    date: string;
    status: RuntimeTriggerState | "DRY_RUN_COMPLETED" | "PUBLISHED" | "FAILED_RECOVERABLE" | "FAILED_TERMINAL";
    completed_at?: string;
    shadow_dir: string;
    lead_count: number;
    shadow_evidence_count: number;
    low_relevance_overflow_count: number;
    readme_skip_count: number;
    query_timeout_skipped_count: number;
    warnings: string[];
  };
  budget: {
    query_timeout_ms: 8000;
    max_compliant_sleep_ms: 5000;
    readme_phase_wall_clock_budget_ms: 45000;
  };
  production: {
    pipeline_path: string;
    last_modified_at: string | null;
    untouched_by_last_dry_run: boolean;
  };
};
```

### 5.2 GET `/api/agent07/runtime/logs?run_id=<id>&limit=50`

Returns the newest NDJSON events already written by RuntimeOrchestrator.

```ts
type Agent07RuntimeLogEvent = {
  timestamp: string;
  level: "DEBUG" | "INFO" | "WARN" | "ERROR";
  component: string;
  event: string;
  meta: Record<string, unknown>;
};

type Agent07RuntimeLogsResponse = {
  version: 1;
  run_id: string;
  events: Agent07RuntimeLogEvent[];
  truncated: boolean;
};
```

Sensitive fields must remain masked. The UI must never render raw GitHub tokens, model keys, full Authorization headers, or `.env` values.

### 5.3 GET `/api/agent07/runtime/shadow?run_id=<id>`

Returns a compact evidence view for the latest shadow run.

```ts
type Agent07ShadowEvidenceSummary = {
  version: 1;
  run_id: string;
  leads: Array<{
    repo: string;
    title: string;
    status: string;
    relevance_score?: number;
    matched_tags?: string[];
  }>;
  shadow_evidence: Array<{
    repo: string;
    status: "LOW_QUALITY_FILTERED";
    reasons: string[];
  }>;
  low_relevance_overflow: Array<{
    repo: string;
    status: "LOW_RELEVANCE_OVERFLOW";
    relevance_score: number;
    matched_tags: string[];
  }>;
  readme_skip_evidence: Array<{
    repo: string;
    status: "README_RATE_LIMIT_SKIPPED" | "README_RATE_LIMIT_EXCEEDED" | "GLOBAL_BUDGET_EXHAUSTED";
    requested_sleep_ms?: number;
    reason?: string;
  }>;
};
```

This endpoint reads shadow outputs only. It must not mutate production state.

### 5.4 POST `/api/agent07/runtime/trigger`

Starts a constrained dry-run live-network pull.

Request:

```json
{
  "mode": "LIVE_NETWORK_SHADOW_PROBE",
  "date": "2026-06-16"
}
```

Server-enforced config:

```ts
{
  dry_run: true,
  live_network: true,
  live_model: false,
  live_publish: false
}
```

The server must ignore any client-provided `live_model` or `live_publish` fields and log a `runtime_trigger_gate_sanitized` warning if they are present.

Response:

```ts
type Agent07RuntimeTriggerResponse = {
  version: 1;
  ok: boolean;
  run_id: string;
  status: "STARTING" | "RUNNING" | "BLOCKED_BY_EXISTING_RUN";
  status_url: "/api/agent07/runtime/status";
};
```

The endpoint must return quickly. The runtime may continue asynchronously, but the service must expose deterministic status polling. If implementation chooses in-process async execution, tests must prove the Promise is tracked and errors are surfaced in status instead of being swallowed.

## 6. Frontend Information Architecture

Agent07 keeps the existing three-column Sentinel dashboard. Stage 10 adds a compact runtime strip above or within the current topbar.

### 6.1 Runtime Strip

Required fields:

- `Runtime`: `Idle`, `Running`, `Completed`, `Failed`, or `Blocked`.
- `Run ID`: latest or active run id.
- `Budget`: visual summary of `8s query`, `5s sleep cap`, `45s README phase`.
- `Evidence`: counts for `LOW_QUALITY_FILTERED`, `LOW_RELEVANCE_OVERFLOW`, `README_RATE_LIMIT_*`, `QUERY_TIMEOUT_SKIPPED`.
- `Trigger Today's Pull`: primary route-scoped button.

The strip must be dense, operational, and scan-first. It must not become a marketing hero or decorative card.

### 6.2 Log Drawer

Stage 10 adds a route-scoped log drawer or inline panel:

- newest events first;
- max 50 rows by default;
- severity color uses platform status tokens;
- event names shown as literal monospace text;
- metadata collapsed by default if long;
- no token leakage.

### 6.3 Shadow Evidence Panel

The existing right column may include a tab or segmented control:

- `Decision`: existing approve/reject detail panel.
- `Runtime`: latest run evidence, overflow, README skips, query skips.

This avoids a fourth column and preserves the current 25/55/20 layout.

## 7. UX State Machine

Manual trigger frontend flow:

```text
Idle
  -> click trigger
  -> Optimistic STARTING within one frame
  -> POST /api/agent07/runtime/trigger
  -> poll /api/agent07/runtime/status every 1500ms while RUNNING
  -> refresh /api/agent07/status after COMPLETED
  -> keep production leads unchanged unless live publish exists in a future stage
```

Failure flow:

```text
RUNNING
  -> FAILED
  -> show latest ERROR/WARN log event
  -> keep trigger disabled for 2 seconds
  -> return to IDLE after status confirms no active run
```

The UI must never imply that shadow results have been published. Copy must say `Shadow probe complete` instead of `Updated`.

## 8. Data Consistency and Atomicity

Runtime status endpoints read these files:

```text
storage/runtime_shadow/<run_id>/runtime_result.json
storage/runtime_shadow/<run_id>/checkpoint.json
storage/runtime_shadow/<run_id>/scout_pipeline.shadow.json
storage/runtime_shadow/<run_id>/sources/source_stage_snapshot.json
storage/logs/sentinel_daily_<date>.log
data/scout_pipeline.json
```

Rules:

- Reads must tolerate missing files and return partial status with warnings.
- Writes remain owned by RuntimeOrchestrator and existing atomic writers.
- Status API must never rewrite RuntimeOrchestrator files.
- Trigger API may create a new run directory through RuntimeOrchestrator only.
- Production `data/scout_pipeline.json` must remain unchanged for Stage 10 manual trigger.

## 9. Observability Events

Stage 10 must display, but not reinterpret, these event names:

- `github_query_timeout_skipped`
- `github_rate_limit_backoff`
- `readme_rate_limit_sleep_rejected`
- `readme_phase_budget_exhausted`
- `source_candidate_filtered`
- `lead_low_relevance_overflow`
- `runtime_publish_skipped_dry_run`
- `runtime_trigger_started`
- `runtime_trigger_failed`
- `runtime_trigger_completed`

If an event is missing because the current baseline did not emit it, the UI must degrade to counts inferred from shadow JSON. It must not fabricate event history.

## 10. Security and Local Safety

- Runtime trigger is local-only. If the web server is later exposed beyond `127.0.0.1`, the trigger endpoint must be disabled by default until a separate auth SDD exists.
- No API response may include raw environment variables.
- No API response may expose full absolute paths outside the project root except documented project paths needed for local debugging.
- The trigger endpoint must reject request bodies larger than 4KB.
- Polling must stop when the browser tab is hidden for more than 60 seconds, then refresh once on visibility restore.

## 11. Testing Matrix for Next Stage

The TDD Red phase must add tests before implementation.

### 11.1 Backend Runtime API Tests

Required assertions:

1. `POST /api/agent07/runtime/trigger` forces `live_model=false` and `live_publish=false` even if the client attempts to set them.
2. A second trigger while a run is active returns `RUNTIME_ALREADY_RUNNING`.
3. `GET /api/agent07/runtime/status` reads runtime shadow files and reports counts for leads, shadow evidence, low relevance overflow, README skips, and query timeout skips.
4. Missing or partial shadow files return warnings instead of throwing uncaught exceptions.
5. Log endpoint masks tokens and limits output length.

### 11.2 Frontend Interaction Tests

Required assertions:

1. Clicking `Trigger Today's Pull` disables the button within one frame and renders `STARTING`.
2. While status is `RUNNING`, the frontend polls status and does not call approve/reject endpoints.
3. On `COMPLETED`, the frontend refreshes normal Agent07 status but labels output as `Shadow probe complete`.
4. On `FAILED`, the latest WARN/ERROR log appears and the UI returns to an actionable idle state.
5. Theme tests prove new runtime strip, log drawer, and evidence panel inherit platform tokens and do not introduce hard-coded Agent07 palettes.

### 11.3 Production Isolation Tests

Required assertions:

1. Manual trigger does not mutate `/Users/tristanzh/agent/Git-Scout/data/scout_pipeline.json`.
2. Manual trigger writes only into `storage/runtime_shadow/<run_id>/` and `storage/logs/`.
3. Route-scoped CSS selectors are prefixed with `.agent07-`.
4. Unrelated agent pages do not inherit Agent07 layout or runtime controls.

## 12. Implementation Plan Preview

The next implementation plan should split work into three milestones:

1. Runtime status/control service contracts and tests.
2. Agent07 frontend runtime strip, log drawer, and shadow evidence panel tests.
3. Integration tests proving manual trigger safety, polling behavior, theme inheritance, and production zero-mutation.

No business implementation should begin until that implementation plan and TDD Red tests are approved.

## 13. Spec Self-Review

- Placeholder scan: no unfinished placeholders remain.
- Internal consistency: UI trigger is shadow-only and cannot publish or invoke live models.
- Scope check: focused on Agent07 runtime observability and manual trigger; no shared web paradigm changes.
- Ambiguity check: API names, gate semantics, status schema, and test requirements are explicit.
