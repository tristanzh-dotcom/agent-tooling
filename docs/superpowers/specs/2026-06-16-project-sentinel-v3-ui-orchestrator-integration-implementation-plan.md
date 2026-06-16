# Project Sentinel v3 UI Orchestrator Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe Agent07 runtime control surface that can trigger live-network shadow probes, display runtime telemetry, and prove production data stays untouched.

**Architecture:** Add a narrow `agent07RuntimeController.ts` service in `Git-Scout` that owns trigger gating, execution mutex, runtime status, shadow evidence summaries, and log reads. Wire that service into Agent07 web APIs in a later task while preserving the route-scoped visual boundary and platform theme inheritance.

**Tech Stack:** TypeScript, Vitest, Node filesystem APIs, existing RuntimeOrchestrator, existing Agent07 web route and node:test browser/service tests.

---

## File Structure

- Create `/Users/tristanzh/agent/Git-Scout/src/sentinel/agent07RuntimeController.ts`
  - Owns Stage 10 API-level contracts.
  - Provides the future backend adapter for `/api/agent07/runtime/status`, `/logs`, `/shadow`, and `/trigger`.
  - Exposes only safe trigger semantics: `live_network=true`, `live_model=false`, `live_publish=false`, `dry_run=true`.
- Create `/Users/tristanzh/agent/Git-Scout/tests/sentinel/agent07RuntimeController.test.ts`
  - First TDD red target for backend gate locking, mutex, telemetry counts, and production isolation.
- Later implementation phase modifies `/Users/tristanzh/agent/web/server.mjs`
  - Mounts HTTP endpoints to the controller.
- Later implementation phase modifies `/Users/tristanzh/agent/web/app/agent07.js`
  - Adds trigger button behavior, status polling, log rendering, and shadow evidence rendering.
- Later implementation phase modifies `/Users/tristanzh/agent/web/app/agent07.css`
  - Adds route-scoped `.agent07-runtime-*` styles using platform variables only.
- Later implementation phase updates `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`
  - Verifies HTTP route behavior.
- Later implementation phase updates `/Users/tristanzh/agent/web/tests/agent07-browser-interaction.test.mjs`
  - Verifies frontend click state, polling, and theme inheritance.

## Task 1: Backend Runtime Controller TDD Contract

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/agent07RuntimeController.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/agent07RuntimeController.test.ts`

- [ ] **Step 1: Write failing trigger gate and mutex test**

```ts
it("forces safe trigger gates and rejects concurrent trigger requests", async () => {
  const deferred = createDeferred<Agent07RuntimeRunResult>();
  const invocations: Agent07RuntimeSafeTriggerConfig[] = [];
  const mutex: Agent07RuntimeMutex = { active_run_id: null };

  const first = handleAgent07RuntimeTrigger(
    { mode: "LIVE_NETWORK_SHADOW_PROBE", date: "2026-06-16", live_model: true, live_publish: true },
    {
      mutex,
      now: () => fixedNow,
      invokeRuntime: async (config) => {
        invocations.push(config);
        return deferred.promise;
      }
    }
  );

  const second = await handleAgent07RuntimeTrigger(
    { mode: "LIVE_NETWORK_SHADOW_PROBE", date: "2026-06-16" },
    {
      mutex,
      now: () => fixedNow,
      invokeRuntime: async () => {
        throw new Error("second invocation must not run");
      }
    }
  );

  expect(second).toMatchObject({
    ok: false,
    status: "ORCHESTRATOR_BUSY",
    http_status: 409
  });

  deferred.resolve(makeRuntimeResult("runtime_20260616T080000Z"));
  const firstResult = await first;

  expect(firstResult).toMatchObject({ ok: true, status: "STARTING" });
  expect(invocations[0]).toMatchObject({
    gates: {
      dry_run: true,
      live_network: true,
      live_model: false,
      live_publish: false
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: FAIL with `Agent07RuntimeControllerNotImplementedError`.

- [ ] **Step 3: Implement minimal controller trigger logic**

Required implementation details:

```ts
export async function handleAgent07RuntimeTrigger(
  request: Agent07RuntimeTriggerRequest,
  deps: Agent07RuntimeControllerDeps
): Promise<Agent07RuntimeTriggerResponse> {
  if (deps.mutex.active_run_id) {
    return {
      version: 1,
      ok: false,
      http_status: 409,
      status: "ORCHESTRATOR_BUSY",
      run_id: deps.mutex.active_run_id,
      status_url: "/api/agent07/runtime/status"
    };
  }

  const runId = `runtime_${deps.now().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "")}`;
  deps.mutex.active_run_id = runId;
  void deps
    .invokeRuntime({
      run_id: runId,
      date: request.date,
      gates: {
        dry_run: true,
        live_network: true,
        live_model: false,
        live_publish: false
      }
    })
    .finally(() => {
      if (deps.mutex.active_run_id === runId) deps.mutex.active_run_id = null;
    });

  return {
    version: 1,
    ok: true,
    http_status: 202,
    run_id: runId,
    status: "STARTING",
    status_url: "/api/agent07/runtime/status"
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: PASS for trigger gate and mutex test.

## Task 2: Shadow Evidence Summary

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/agent07RuntimeController.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/agent07RuntimeController.test.ts`

- [ ] **Step 1: Write failing shadow summary test**

```ts
it("summarizes shadow evidence counts and reason metadata for runtime visualization", async () => {
  const shadowDir = await seedShadowRun({
    shadowEvidenceCount: 39,
    lowRelevanceOverflowCount: 2,
    readmeSkipCount: 1,
    queryTimeoutSkippedCount: 1
  });

  const summary = await readAgent07RuntimeShadowSummary({
    run_id: "runtime_20260616T080000Z",
    run_shadow_dir: shadowDir
  });

  expect(summary).toMatchObject({
    version: 1,
    run_id: "runtime_20260616T080000Z",
    low_quality_filtered_count: 39,
    low_relevance_overflow_count: 2,
    readme_skip_count: 1,
    query_timeout_skipped_count: 1
  });
  expect(summary.shadow_evidence[0]).toMatchObject({
    status: "LOW_QUALITY_FILTERED",
    reasons: expect.arrayContaining(["LOCAL_INSTALL_POLLUTION"])
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: FAIL with `Agent07RuntimeControllerNotImplementedError`.

- [ ] **Step 3: Implement summary reader**

Implementation reads:

```text
scout_pipeline.shadow.json
source_query_checkpoint.json
sources/source_stage_snapshot.json
```

It tolerates missing files and returns warnings instead of throwing for absent optional artifacts.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: PASS for trigger and shadow summary tests.

## Task 3: Production Zero-Touch Runtime Trigger

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/agent07RuntimeController.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/agent07RuntimeController.test.ts`

- [ ] **Step 1: Write failing zero-touch test**

```ts
it("keeps production scout_pipeline.json byte-identical when UI trigger runs a shadow probe", async () => {
  const productionPath = await seedProductionPipeline();
  const before = await readFile(productionPath, "utf8");
  const beforeStat = await stat(productionPath);

  await handleAgent07RuntimeTrigger(
    { mode: "LIVE_NETWORK_SHADOW_PROBE", date: "2026-06-16" },
    {
      mutex: { active_run_id: null },
      now: () => fixedNow,
      production_pipeline_path: productionPath,
      invokeRuntime: async (config) => {
        expect(config.gates.live_publish).toBe(false);
        return makeRuntimeResult(config.run_id);
      }
    }
  );

  const after = await readFile(productionPath, "utf8");
  const afterStat = await stat(productionPath);
  expect(after).toBe(before);
  expect(afterStat.mtimeMs).toBe(beforeStat.mtimeMs);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: FAIL before implementation.

- [ ] **Step 3: Implement zero-touch guard**

The controller must never write to `production_pipeline_path`. It only passes `live_publish=false` to RuntimeOrchestrator and returns trigger status.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/agent07RuntimeController.test.ts
```

Expected: PASS for all controller tests.

## Task 4: Web Route Binding and Theme-Safe UI

**Files:**
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Modify: `/Users/tristanzh/agent/web/app/agent07.js`
- Modify: `/Users/tristanzh/agent/web/app/agent07.css`
- Modify: `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`
- Modify: `/Users/tristanzh/agent/web/tests/agent07-browser-interaction.test.mjs`

- [ ] **Step 1: Write failing web service tests**

Required assertions:

```js
assert.equal(triggerResponse.status, 202);
assert.equal(busyResponse.status, 409);
assert.equal(status.runtime.latest_run.shadow_evidence_count, 39);
assert.equal(productionAfter, productionBefore);
```

- [ ] **Step 2: Implement `/api/agent07/runtime/*` route bindings**

Routes delegate to `agent07RuntimeController.ts`. Server code must not construct live model or publish gates from client body.

- [ ] **Step 3: Write failing frontend tests**

Required assertions:

```js
assert.match(js, /\/api\/agent07\/runtime\/trigger/);
assert.match(js, /\/api\/agent07\/runtime\/status/);
assert.match(css, /\.agent07-runtime-/);
assert.doesNotMatch(css, /#000000|#ffffff|#888888|#222222/i);
```

- [ ] **Step 4: Implement runtime strip and log drawer**

The button disables within one frame, status polling starts while running, and output is labeled `Shadow probe complete`.

## Task 5: Full Verification and Commit

**Files:**
- All files touched above.

- [ ] **Step 1: Run Sentinel tests**

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test
npm run typecheck
```

Expected: all Sentinel tests pass and TypeScript exits 0.

- [ ] **Step 2: Run Agent07 web tests**

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-service.test.mjs
node --test tests/agent07-browser-interaction.test.mjs
```

Expected: Agent07 route and browser interaction tests pass.

- [ ] **Step 3: Stage exact files only**

```bash
cd /Users/tristanzh/agent
git add \
  docs/superpowers/specs/2026-06-16-project-sentinel-v3-ui-orchestrator-integration-implementation-plan.md \
  Git-Scout/src/sentinel/agent07RuntimeController.ts \
  Git-Scout/tests/sentinel/agent07RuntimeController.test.ts \
  web/server.mjs \
  web/app/agent07.js \
  web/app/agent07.css \
  web/tests/agent07-service.test.mjs \
  web/tests/agent07-browser-interaction.test.mjs
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(sentinel): 打通 Agent07 Runtime 手动触发与状态可视化"
```

## Self-Review

- Spec coverage: covers safe trigger, mutex, runtime status, logs, shadow evidence, frontend polling, route-scoped CSS, and production zero-touch.
- Placeholder scan: no unfinished placeholders remain.
- Type consistency: `Agent07Runtime*` names are reserved for the new controller; existing RuntimeOrchestrator types remain unchanged.
- Scope check: plan is limited to Agent07 runtime integration and does not change shared web paradigms.
