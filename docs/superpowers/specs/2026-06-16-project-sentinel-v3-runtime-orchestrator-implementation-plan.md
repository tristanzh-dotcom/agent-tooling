# Project Sentinel v3 Runtime Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Stage 6 production runtime orchestrator so Project Sentinel can run as a safe daily local command with dry-run defaults, shadow execution, resumable checkpoints, structured logs, and two-phase atomic publish.

**Architecture:** Implement the runtime as small TypeScript modules around explicit dependency injection. `runtimeConfig` owns CLI gates, `runtimeCheckpoint` owns resume and stale-lock self-healing, `runtimePublisher` owns atomic publish, `runtimeLogger` owns NDJSON observability, and `runtimeOrchestrator` composes existing Sentinel capabilities without importing E2E fixtures or touching production paths before publish.

**Tech Stack:** TypeScript on Node.js 22+, Vitest, Node `fs/promises`, same-directory temp files with atomic `rename`, NDJSON logs, existing Sentinel JSON contracts, injected source/model/capturer/publisher adapters.

---

## Source of Truth

- SDD: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
- Work root: `/Users/tristanzh/agent/Git-Scout`
- Current stable baseline: `c306f50`
- Required Red commit scope: implementation plan, `runtimeOrchestrator.ts` interface stub, `runtimeOrchestrator.test.ts`
- Existing unrelated dirty files in `/Users/tristanzh/agent` must not be staged, modified, or reverted.

## File Structure

Stage 6 implementation will use these files:

```text
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeConfig.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeCheckpoint.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeLogger.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimePublisher.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts
/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts
/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeConfig.test.ts
/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeCheckpoint.test.ts
/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimePublisher.test.ts
/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeLogger.test.ts
```

Responsibilities:

- `runtimeOrchestrator.ts`: top-level daily runtime composition and injected adapter routing.
- `runtimeConfig.ts`: CLI parsing, gate validation, immutable runtime config creation.
- `runtimeCheckpoint.ts`: checkpoint schema, stale lock detection, resume algorithm, atomic checkpoint writes.
- `runtimeLogger.ts`: append-only NDJSON logging and daily rotation.
- `runtimePublisher.ts`: publish manifest validation and two-phase atomic publish.
- `runtimeOrchestratorCli.ts`: thin CLI wrapper that parses args and prints a final human summary.

## Task 1: TDD Red Contract For Runtime Orchestrator

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts`
- Create: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-implementation-plan.md`

- [ ] **Step 1: Write the failing tests**

Create `runtimeOrchestrator.test.ts` with three tests:

```ts
it("defaults to dry-run gates and routes network/model work to mock adapters", async () => {
  const result = await runRuntimeOrchestrator(inputWithoutLiveFlags);
  expect(result.config.gates).toMatchObject({
    dry_run: true,
    live_network: false,
    live_model: false,
    live_publish: false
  });
  expect(liveSource.fetchCandidates).not.toHaveBeenCalled();
  expect(liveModel.invoke).not.toHaveBeenCalled();
  expect(mockSource.fetchCandidates).toHaveBeenCalled();
  expect(mockModel.invoke).toHaveBeenCalled();
});

it("keeps production scout_pipeline.json unchanged during shadow failure and publishes only after successful two-phase commit", async () => {
  const failed = await runRuntimeOrchestrator(inputWithFailureAfterBlindScout);
  expect(await readFile(productionPipelinePath, "utf8")).toBe(previousProductionJson);
  expect(failed.status).toBe("FAILED_RECOVERABLE");
  expect(await pathExists(failed.shadow_pipeline_path)).toBe(true);

  const published = await runRuntimeOrchestrator(inputWithLivePublishSuccess);
  expect(published.status).toBe("PUBLISHED");
  expect(publisher.atomicRename).toHaveBeenCalled();
});

it("self-heals stale shadow locks and resumes only pending checkpoint steps", async () => {
  await mkdir(staleLockPath, { recursive: true });
  await writeFile(checkpointPath, checkpointWithTwoSuccessAndThreePending);
  const result = await runRuntimeOrchestrator(inputWithResume);
  expect(await pathExists(staleLockPath)).toBe(false);
  expect(result.resume.skipped_steps).toHaveLength(2);
  expect(capturer.captureLead).toHaveBeenCalledTimes(3);
});
```

- [ ] **Step 2: Create interface stub**

Create `runtimeOrchestrator.ts` exporting:

```ts
export class RuntimeOrchestratorNotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not implemented`);
    this.name = "RuntimeOrchestratorNotImplementedError";
  }
}

export async function runRuntimeOrchestrator(_input: RunRuntimeOrchestratorInput): Promise<RuntimeRunResult> {
  throw new RuntimeOrchestratorNotImplementedError("runRuntimeOrchestrator");
}
```

Also define all public types used by the tests: gates, config, adapters, checkpoint step, runtime result, publisher, capturer, source and model clients.

- [ ] **Step 3: Verify Red**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npx vitest run tests/sentinel/runtimeOrchestrator.test.ts
```

Expected:

```text
typecheck passes
runtimeOrchestrator.test.ts fails with RuntimeOrchestratorNotImplementedError
```

- [ ] **Step 4: Commit Red**

```bash
cd /Users/tristanzh/agent
git add \
  docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-implementation-plan.md \
  Git-Scout/src/sentinel/runtimeOrchestrator.ts \
  Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts
git commit -m "test(sentinel): 编写 Orchestrator 生产编排器闸门控制、原子发布与自检续传 TDD 集成测试"
```

## Task 2: Runtime Config Gates

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeConfig.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeConfig.test.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`

- [ ] **Step 1: Write failing config tests**

Create tests for:

```ts
parseRuntimeArgs([])
parseRuntimeArgs(["--dry-run", "--live-publish"])
parseRuntimeArgs(["--live-model"])
parseRuntimeArgs(["--live-network", "--live-model", "--live-publish", "--date", "2026-06-16"])
```

Assertions:

```ts
expect(defaultConfig.gates.dry_run).toBe(true);
expect(defaultConfig.gates.live_network).toBe(false);
expect(() => parseRuntimeArgs(["--dry-run", "--live-publish"])).toThrow("RUNTIME_GATE_CONFLICT");
expect(() => parseRuntimeArgs(["--live-model"])).toThrow("LIVE_MODEL_REQUIRES_EXPLICIT_SOURCE_MODE");
```

- [ ] **Step 2: Implement minimal parser**

Implement manual parsing using `process.argv`-style string arrays. Do not add `commander` or `yargs`.

- [ ] **Step 3: Verify**

Run:

```bash
npx vitest run tests/sentinel/runtimeConfig.test.ts tests/sentinel/runtimeOrchestrator.test.ts
npm run typecheck
```

Expected: all runtime config tests pass; runtime orchestrator tests remain Green if Task 3 is already implemented or fail only where later modules are still stubs.

## Task 3: Checkpoint Resume And Stale Lock Self-Healing

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeCheckpoint.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeCheckpoint.test.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`

- [ ] **Step 1: Write failing checkpoint tests**

Create tests for:

```ts
loadOrCreateCheckpoint({ resume: true })
healRuntimeShadow({ staleLockTtlMs: 86_400_000 })
markStaleRunningStepsRetryable(checkpoint)
nextPendingSteps(checkpoint)
```

Assertions:

```ts
expect(await pathExists(staleLockPath)).toBe(false);
expect(resume.skipped_steps.map((step) => step.step_id)).toEqual(["capture:tool-1", "capture:tool-2"]);
expect(retryable.steps.find((step) => step.status === "STEP_FAILED_RETRYABLE")).toBeDefined();
```

- [ ] **Step 2: Implement atomic checkpoint writes**

Use same-directory temp file, `fs.rename`, and parent directory fsync. Do not read `.tmp` files as authoritative checkpoint data.

- [ ] **Step 3: Verify**

Run:

```bash
npx vitest run tests/sentinel/runtimeCheckpoint.test.ts tests/sentinel/runtimeOrchestrator.test.ts
npm run typecheck
```

Expected: checkpoint and orchestrator resume tests pass.

## Task 4: Two-Phase Runtime Publisher

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimePublisher.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimePublisher.test.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`

- [ ] **Step 1: Write failing publisher tests**

Tests:

```ts
it("does not mutate production pipeline before final atomic rename", async () => {});
it("publishes shadow pipeline with production thumb paths after manifest validation", async () => {});
it("leaves production json parseable when injected failure occurs before rename", async () => {});
```

Required assertions:

```ts
expect(JSON.parse(await readFile(productionPipelinePath, "utf8"))).toMatchObject(previousState);
expect(published.artifacts.local_thumb_path).toContain("/agent07-artifacts/storage/");
await expect(readFile(lockPath)).rejects.toMatchObject({ code: "ENOENT" });
```

- [ ] **Step 2: Implement publisher**

Implement:

```ts
validatePublishManifest(manifest)
publishRuntimeShadow(manifest, options)
rewriteShadowThumbPathsForProduction(pipeline)
```

All output path checks must reject traversal outside `Git-Scout`.

- [ ] **Step 3: Verify**

Run:

```bash
npx vitest run tests/sentinel/runtimePublisher.test.ts tests/sentinel/runtimeOrchestrator.test.ts
npm run typecheck
```

Expected: publisher and orchestrator publish tests pass.

## Task 5: Structured Runtime Logger

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeLogger.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeLogger.test.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`

- [ ] **Step 1: Write failing logger tests**

Tests:

```ts
it("writes required runtime events as NDJSON records", async () => {});
it("rotates daily log when size threshold is exceeded", async () => {});
it("records stale lock self-healing and publish aborts with structured context", async () => {});
```

Required assertions:

```ts
const lines = logBody.trim().split("\n").map((line) => JSON.parse(line));
expect(lines).toEqual(expect.arrayContaining([
  expect.objectContaining({ event: "RUNTIME_STARTED" }),
  expect.objectContaining({ event: "CHECKPOINT_RESUME" }),
  expect.objectContaining({ event: "PUBLISH_ABORTED" })
]));
```

- [ ] **Step 2: Implement logger**

Implement append-only JSONL writes and simple size-based rotation. The CLI wrapper may print a final summary, but core runtime modules must use the logger.

- [ ] **Step 3: Verify**

Run:

```bash
npx vitest run tests/sentinel/runtimeLogger.test.ts tests/sentinel/runtimeOrchestrator.test.ts
npm run typecheck
```

Expected: logger and orchestrator observability assertions pass.

## Task 6: CLI Wrapper And Package Command

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/package.json`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts`

- [ ] **Step 1: Add CLI wrapper tests**

The test must execute the CLI module with injected argv and assert:

```ts
expect(result.status).toBe("DRY_RUN_COMPLETED");
expect(result.gates.live_publish).toBe(false);
```

- [ ] **Step 2: Implement thin wrapper**

`runtimeOrchestratorCli.ts` must:

1. Parse args via `runtimeConfig.ts`.
2. Construct injected adapters.
3. Await `runRuntimeOrchestrator`.
4. Print one concise JSON summary.
5. Set non-zero exit code for terminal runtime failures.

- [ ] **Step 3: Add package script**

Modify `package.json`:

```json
{
  "scripts": {
    "sentinel:daily": "tsx src/sentinel/runtimeOrchestratorCli.ts"
  }
}
```

If implementation avoids `tsx`, use a compiled Node entry and document the choice in the test.

- [ ] **Step 4: Verify all Stage 6 tests**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npm test
```

Expected:

```text
All existing Sentinel tests pass.
All Stage 6 runtime tests pass.
```

## Self-Review Checklist

- SDD coverage: CLI gates, two-phase publish, checkpoint resume, stale lock self-healing, structured logs, E2E/production isolation all map to tasks above.
- Placeholder scan: no unresolved marker text or vague implementation steps are allowed in this plan.
- Type consistency: all Stage 6 public runtime types are introduced first in Task 1 and split into focused files in later tasks.
- Scope control: no live provider credentials, no scheduler daemon, no web UI changes, and no real network/model implementation are included in this phase.
