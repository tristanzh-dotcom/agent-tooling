# Project Sentinel v3 README Budget Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent GitHub README rate-limit responses from trapping Sentinel daily runtime in long local sleeps, while preserving structured source evidence during interrupted runs.

**Architecture:** Stage 9.2 is a contained `RealSourceAdapter` hardening pass. It adds a capped README backoff decision layer, a 45 second README phase budget, and an incremental `source_stage_snapshot.json` flush path that writes parseable shadow evidence before final source output.

**Tech Stack:** TypeScript, Node.js, Vitest fake timers/injected clocks, existing atomic fileStore adapter, existing NDJSON logger contract.

---

## File Structure

- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - Extend `RealSourceAdapterConfig.github` with README budget fields.
  - Add README rate-limit decision helpers.
  - Add incremental `source_stage_snapshot.json` write helper.
  - Enforce README phase wall-clock budget and capped compliant sleep.
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`
  - Pass default README budget values into `createRealSourceAdapter`.
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
  - Add Stage 9.2 Red tests for long sleep rejection, wall-clock budget, and segmented snapshot survival.
- Do not modify dashboard, Capturer, Auditor, LeadPromotionScorer, or production data files.

## Task 1: README Sleep Cap Contract

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
- Modify later: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`

- [ ] **Step 1: Write failing test for capped compliant sleep**

Add a `describe("Stage 9.2 README Budget Guard TDD contract", ...)` block with this behavior:

```ts
it("rejects README Primary Rate Limit sleeps above 5000ms while allowing short backoff", async () => {
  const config = withReadmeBudget(makeConfig({ live_network: true }));
  const repos = [makeSearchItem("github/long-sleep-repo"), makeSearchItem("github/short-sleep-repo")];
  const deps = makeDeps({
    http: {
      getJson: vi.fn(async <T>() => ({
        status: 200,
        headers: { "x-ratelimit-remaining": "29" },
        body: makeSearchResponse(repos)
      }) as unknown as HttpJsonResult<T>),
      getText: vi
        .fn()
        .mockResolvedValueOnce({
          status: 403,
          headers: {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": String(Math.floor((fixedNow.getTime() + 6000) / 1000))
          },
          body: ""
        })
        .mockResolvedValueOnce({ status: 200, headers: {}, body: highTrustReadme("Long Sleep Repo") })
        .mockResolvedValueOnce({
          status: 429,
          headers: { "retry-after": "2" },
          body: ""
        })
        .mockResolvedValueOnce({ status: 200, headers: {}, body: highTrustReadme("Short Sleep Repo") })
    },
    sleep: vi.fn(async () => undefined)
  });

  const result = (await createRealSourceAdapter(config, deps).fetchCandidates()) as any;

  expect((deps.sleep as unknown as ReturnType<typeof vi.fn>).mock.calls.some(([ms]) => ms > 5000)).toBe(false);
  expect(deps.sleep).toHaveBeenCalledWith(2000);
  expect(result.readme_skip_evidence?.["github/long-sleep-repo"]).toMatchObject({
    status: "README_RATE_LIMIT_EXCEEDED",
    source: "readme_budget_guard"
  });
  expect(deps.logEvents).toEqual(expect.arrayContaining([expect.objectContaining({ event: "readme_rate_limit_sleep_rejected" })]));
});
```

- [ ] **Step 2: Run Red verification**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: FAIL because the current adapter calls `deps.sleep(6000)` and does not emit `readme_rate_limit_sleep_rejected`.

- [ ] **Step 3: Implement capped decision helper**

Add pure helpers:

```ts
function readmeRateLimitKind(status: number, headers: HttpHeaders): ReadmeRateLimitKind {
  if (headers["x-ratelimit-remaining"] === "0") return "PRIMARY_RATE_LIMIT";
  if (status === 403 || status === 429) return "SECONDARY_RATE_LIMIT";
  return "UNKNOWN_RATE_LIMIT";
}

function decideReadmeBackoff(input: {
  status: number;
  headers: HttpHeaders;
  now: Date;
  retryCount: number;
  maxCompliantSleepMs: number;
  maxReadmeRateLimitRetries: number;
}): ReadmeBackoffDecision {
  const requestedSleepMs = rateLimitDelayMs(input.headers, input.now);
  const kind = readmeRateLimitKind(input.status, input.headers);
  if (requestedSleepMs <= input.maxCompliantSleepMs && input.retryCount < input.maxReadmeRateLimitRetries) {
    return { action: "SLEEP_AND_RETRY", sleep_ms: requestedSleepMs, reason: "SHORT_COMPLIANT_BACKOFF" };
  }
  if (kind === "PRIMARY_RATE_LIMIT") {
    return {
      action: "STOP_README_PHASE",
      status: "README_RATE_LIMIT_EXCEEDED",
      reason: "PRIMARY_RATE_LIMIT_LONG_SLEEP",
      requested_sleep_ms: requestedSleepMs
    };
  }
  return {
    action: "SKIP_REPO",
    status: "README_RATE_LIMIT_SKIPPED",
    reason: requestedSleepMs > input.maxCompliantSleepMs ? "COMPLIANT_SLEEP_EXCEEDED" : "README_RETRY_BUDGET_EXHAUSTED",
    requested_sleep_ms: requestedSleepMs
  };
}
```

- [ ] **Step 4: Run target and full verification**

Run:

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
npm test
npm run typecheck
```

Expected after Green: all Sentinel tests pass.

## Task 2: README Phase Wall-Clock Budget

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
- Modify later: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`

- [ ] **Step 1: Write failing test for global README budget**

Add this behavior:

```ts
it("stops README fetching when the 45s phase budget is exhausted and preserves partial candidates", async () => {
  let nowMs = fixedNow.getTime();
  let readmeCalls = 0;
  const config = withReadmeBudget(makeConfig({ live_network: true }));
  const repos = [1, 2, 3, 4, 5].map((index) => makeSearchItem(`github/budget-repo-${index}`));
  const deps = makeDeps({
    now: () => new Date(nowMs),
    http: {
      getJson: vi.fn(async <T>() => ({
        status: 200,
        headers: { "x-ratelimit-remaining": "29" },
        body: makeSearchResponse(repos)
      }) as unknown as HttpJsonResult<T>),
      getText: vi.fn(async () => {
        readmeCalls += 1;
        nowMs += readmeCalls <= 2 ? 20_000 : 6001;
        return { status: 200, headers: {}, body: highTrustReadme(`Budget Repo ${readmeCalls}`) };
      })
    }
  });

  const result = (await createRealSourceAdapter(config, deps).fetchCandidates()) as any;

  expect(deps.http.getText).toHaveBeenCalledTimes(3);
  expect(result.candidates.map((candidate: RuntimeCandidate) => candidate.repo)).toEqual([
    "github/budget-repo-1",
    "github/budget-repo-2"
  ]);
  expect(result.readme_skip_evidence?.GLOBAL_README_PHASE).toMatchObject({
    status: "GLOBAL_BUDGET_EXHAUSTED"
  });
  expect(deps.logEvents).toEqual(expect.arrayContaining([expect.objectContaining({ event: "readme_phase_budget_exhausted" })]));
});
```

- [ ] **Step 2: Run Red verification**

Run:

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: FAIL because the current adapter fetches README for all repos and has no global budget evidence.

- [ ] **Step 3: Implement budget check**

Add a README phase started timestamp before iterating repos. Check elapsed time before each repo and after each successful fetch. On budget exhaustion, write evidence and break to scorer with collected promotion inputs.

- [ ] **Step 4: Verify**

Run target test, full suite, and typecheck.

## Task 3: Segmented Source Snapshot

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
- Modify later: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`

- [ ] **Step 1: Write failing test for incremental snapshot**

Add this behavior:

```ts
it("flushes a parseable source_stage_snapshot after each state transition before an injected abort", async () => {
  const config = withReadmeBudget(makeConfig({ live_network: true }));
  const repos = [
    makeSearchItem("github/captured-layout-engine"),
    makeSearchItem("github/zip-filtered"),
    makeSearchItem("github/abort-after-snapshot")
  ];
  const deps = makeDeps({
    http: {
      getJson: vi.fn(async <T>() => ({
        status: 200,
        headers: { "x-ratelimit-remaining": "29" },
        body: makeSearchResponse(repos)
      }) as unknown as HttpJsonResult<T>),
      getText: vi
        .fn()
        .mockResolvedValueOnce({ status: 200, headers: {}, body: highTrustReadme("Captured Layout Engine") })
        .mockResolvedValueOnce({
          status: 200,
          headers: {},
          body: "# Zip Filtered\n\nDownload the zip file manually and place it in the root folder.\n\n![Preview](docs/preview.png)"
        })
        .mockRejectedValueOnce(new Error("SIGINT_AFTER_INCREMENTAL_SNAPSHOT"))
    }
  });

  await expect(createRealSourceAdapter(config, deps).fetchCandidates()).rejects.toThrow("SIGINT_AFTER_INCREMENTAL_SNAPSHOT");

  expect(deps.fileStore.writeJsonAtomic).toHaveBeenCalledWith(
    expect.stringContaining("source_stage_snapshot.json"),
    expect.objectContaining({
      status: expect.stringMatching(/^SOURCE_/),
      promotion_inputs_preview: expect.arrayContaining([expect.objectContaining({ repo: "github/captured-layout-engine" })]),
      shadow_evidence: expect.objectContaining({
        "github/zip-filtered": expect.objectContaining({ status: "LOW_QUALITY_FILTERED" })
      })
    })
  );
});
```

- [ ] **Step 2: Run Red verification**

Run:

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: FAIL because the current adapter only writes final source outputs and does not flush `source_stage_snapshot.json` mid-run.

- [ ] **Step 3: Implement throttled state-transition flush**

Create a `flushSourceStageSnapshot()` helper that writes a compact JSON snapshot through `fileStore.writeJsonAtomic`. Call it after real state transitions only:

- promotion input added;
- guard evidence added;
- readme skip evidence added;
- global budget exhausted;
- source status changes.

Do not flush on every log line. Do not use synchronous file writes.

- [ ] **Step 4: Verify**

Run:

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
npm test
npm run typecheck
```

## Self-Review Checklist

- Spec coverage: capped sleep, 45s budget, incremental snapshot, zero production pollution, and fake/injected time are all represented.
- Placeholder scan: no deferred-work markers and no vague catch-all implementation steps.
- Type consistency: test names use `source_stage_snapshot.json`, `README_RATE_LIMIT_EXCEEDED`, `README_RATE_LIMIT_SKIPPED`, and `GLOBAL_BUDGET_EXHAUSTED`, matching the SDD.
- Commit discipline: stage only the implementation plan, updated test file, and any explicit Stage 9.2 interface stubs. Never stage `/Users/tristanzh/agent/Git-Scout/storage/`.
