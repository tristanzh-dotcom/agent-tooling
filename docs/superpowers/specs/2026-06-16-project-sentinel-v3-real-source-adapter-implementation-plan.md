# Real Source Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Project Sentinel v3 real public source adapter that safely ingests bounded GitHub public data through Runtime gates.

**Architecture:** The adapter plugs into the existing Runtime Orchestrator source seam and never bypasses `live_network`, shadow paths, or checkpoint boundaries. It uses an injected HTTP client and injected filesystem/logger adapters so tests can prove no real network, credentials, or production paths are touched. GitHub Repository Search is the first live source; README fetching is a second, throttled phase with blacklist and byte slicing before any downstream token path.

**Tech Stack:** TypeScript, Node.js built-ins, Vitest, existing Sentinel Runtime Orchestrator types, no new production dependency in this stage.

---

## File Structure

- Create `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - Owns public adapter types, `createRealSourceAdapter`, live-network gate checks, source normalization, rate-limit handling, README throttling, and shadow cache writes.
- Create `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
  - Owns Red/Green tests for air-gapped fallback, 403/429 circuit breaker, blacklist-before-spend, and README slicing.
- Future optional split after Green:
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/githubSourceAdapter.ts` for GitHub-specific request construction.
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/sourcePlan.ts` for deterministic query plan builders.

## Task 1: TDD Red Interfaces and Tests

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`

- [ ] **Step 1: Create interface stub**

```ts
export class RealSourceAdapterNotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not implemented`);
    this.name = "RealSourceAdapterNotImplementedError";
  }
}
```

- [ ] **Step 2: Add failing tests for three hard contracts**

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: FAIL with `RealSourceAdapterNotImplementedError`.

- [ ] **Step 3: Verify repository typecheck still passes**

```bash
npm run typecheck
```

Expected: PASS.

- [ ] **Step 4: Commit Red state**

```bash
git add docs/superpowers/specs/2026-06-16-project-sentinel-v3-real-source-adapter-implementation-plan.md \
  Git-Scout/src/sentinel/realSourceAdapter.ts \
  Git-Scout/tests/sentinel/realSourceAdapter.test.ts
git commit -m "test(sentinel): 编写 RealSourceAdapter 公海隔离、限流退避与大长文本截断 TDD 集成测试"
```

## Task 2: Air-Gapped Fallback Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`

- [ ] **Step 1: Implement `live_network=false` gate**

Behavior:
- If `config.runtime.gates.live_network === false`, do not call `http.getJson` or `http.getText`.
- Return fixture candidates from `fixtureFallback`.
- Persist fixture projection to `storage/runtime_shadow/<run_id>/sources/source_candidates.runtime.json`.
- Emit `live_network_gate_blocked` log.

- [ ] **Step 2: Run targeted test**

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts -t "uses local fixture fallback"
```

Expected: PASS for air-gapped test.

## Task 3: GitHub Search and README Pipeline Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`

- [ ] **Step 1: Implement bounded GitHub search request construction**

Behavior:
- Construct `https://api.github.com/search/repositories` URLs with encoded `q`, `sort`, `order`, `per_page`, and `page`.
- Clamp pages to `query.page_limit` and `github.max_pages_per_query`.
- Attach `Accept: application/vnd.github+json`, `X-GitHub-Api-Version`, `User-Agent`, and optional masked Authorization header from env getter.

- [ ] **Step 2: Normalize Search items**

Behavior:
- Drop private repos.
- Dedupe by lowercase `owner/repo`.
- Score using deterministic keywords.
- Preserve full `SourceCandidateEnvelope` in shadow cache.

- [ ] **Step 3: Run targeted test**

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts -t "skips blacklisted repositories"
```

Expected: README and blacklist test progresses to truncation assertions.

## Task 4: README Throttling and Circuit Breaker Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`

- [ ] **Step 1: Implement sequential README fetch**

Behavior:
- README phase must use a concurrency ceiling of `1` by default.
- Blacklisted repos/authors are skipped before any Contents API call.
- If one README request returns secondary limit, retry that repo according to `retry-after` / reset / exponential backoff.
- After three consecutive secondary-limit failures, set adapter status `SOURCE_THROTTLED` and stop issuing README requests.

- [ ] **Step 2: Implement byte slicing**

Behavior:
- Cap raw README text to `github.max_readme_bytes`.
- Cap digest to `github.max_readme_digest_chars`.
- Mark `readme_truncated=true`.
- Never pass original oversized text to `RuntimeCandidate.readme`.

- [ ] **Step 3: Run targeted tests**

```bash
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected: All RealSourceAdapter tests PASS.

## Task 5: Full Regression

**Files:**
- Modify only if tests reveal integration gaps:
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`

- [ ] **Step 1: Run typecheck**

```bash
npm run typecheck
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

```bash
npm test
```

Expected: existing 24 tests plus new RealSourceAdapter tests all PASS.

- [ ] **Step 3: Commit Green implementation**

```bash
git add Git-Scout/src/sentinel/realSourceAdapter.ts Git-Scout/tests/sentinel/realSourceAdapter.test.ts
git commit -m "fix(sentinel): 实现 RealSourceAdapter 公海隔离、限流退避与 README 截断"
```

## Self-Review

- Spec coverage: Covers live-network gate, GitHub 403/429 handling, secondary rate-limit circuit breaker, blacklist-before-README, README byte slicing, shadow cache, logging, and no model/token path.
- Placeholder scan: No placeholder markers or deferred implementation instructions remain.
- Type consistency: The plan uses `RealSourceAdapterConfig`, `RateLimitedHttpClient`, `SourceCandidateEnvelope`, and `RuntimeCandidate` names from the SDD and Red stub.
