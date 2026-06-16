# Source Tightening and Artifact Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic SourcePlan v2 query tightening and Artifact Hint Guard filtering before low-quality GitHub candidates reach Blind Scout, Capturer, Dashboard, or Auditor.

**Architecture:** Split the work into two pure modules: `sourcePlan.ts` builds and validates GitHub query matrices, while `artifactHintGuard.ts` scans bounded README text and artifact hints into `PASS` or `LOW_QUALITY_FILTERED`. `realSourceAdapter.ts` will later call both modules after README fetch and retain filtered candidates in shadow evidence only. Tests first lock down matrix qualifiers, low-quality filtering evidence, downstream zero-call behavior, and regex timeout fallback.

**Tech Stack:** TypeScript, Vitest, Node.js built-ins, existing Sentinel Runtime/RealSourceAdapter contracts, no new runtime dependency.

---

## File Structure

- Create `/Users/tristanzh/agent/Git-Scout/src/sentinel/sourcePlan.ts`
  - Builds SourcePlan v2 query matrix and validates query entries.
- Create `/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactHintGuard.ts`
  - Defines Artifact Hint Guard types and scan/apply functions.
- Create `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactHintGuard.test.ts`
  - Red tests for query matrix, low-quality filtering evidence, and timeout fallback.
- Create `/Users/tristanzh/agent/Git-Scout/tests/fixtures/sources/low-quality-zip-readme.md`
  - Fixture modeled after the live dry-run ZIP-download pattern.
- Create `/Users/tristanzh/agent/Git-Scout/tests/fixtures/sources/high-trust-layout-readme.md`
  - Fixture for future Green retention tests.
- Later Green modifications:
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`

## Task 1: Red Tests and Interface Stubs

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/sourcePlan.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactHintGuard.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactHintGuard.test.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/fixtures/sources/low-quality-zip-readme.md`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/fixtures/sources/high-trust-layout-readme.md`

- [ ] **Step 1: Add interface stubs that intentionally throw**

```ts
export class ArtifactHintGuardNotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not implemented`);
    this.name = "ArtifactHintGuardNotImplementedError";
  }
}
```

- [ ] **Step 2: Add failing tests**

```bash
npm test -- tests/sentinel/artifactHintGuard.test.ts
```

Expected: FAIL with `SourcePlanNotImplementedError` and `ArtifactHintGuardNotImplementedError`.

- [ ] **Step 3: Verify typecheck**

```bash
npm run typecheck
```

Expected: PASS.

- [ ] **Step 4: Verify old suite stays green except new Red test**

```bash
npm test -- tests/sentinel/storageBase.test.ts tests/sentinel/blindScout.test.ts tests/sentinel/dashboardController.test.ts tests/sentinel/hardcoreAuditor.test.ts tests/sentinel/artifactCapturer.test.ts tests/sentinel/sentinelE2E.test.ts tests/sentinel/runtimeOrchestrator.test.ts tests/sentinel/realSourceAdapter.test.ts tests/sentinel/runtimeOrchestratorCli.test.ts
```

Expected: PASS, 30 existing tests green.

- [ ] **Step 5: Commit Red state**

```bash
git add docs/superpowers/specs/2026-06-16-project-sentinel-v3-source-tightening-implementation-plan.md \
  Git-Scout/src/sentinel/sourcePlan.ts \
  Git-Scout/src/sentinel/artifactHintGuard.ts \
  Git-Scout/tests/sentinel/artifactHintGuard.test.ts \
  Git-Scout/tests/fixtures/sources/low-quality-zip-readme.md \
  Git-Scout/tests/fixtures/sources/high-trust-layout-readme.md
git commit -m "test(sentinel): 编写 Stage 8 检索矩阵升级、低质指纹拦截与抗回溯超时 TDD 单元测试"
```

## Task 2: Query Matrix v2 Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/sourcePlan.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactHintGuard.test.ts`

- [ ] **Step 1: Implement `buildDefaultSourcePlanV2`**

Required behavior:
- Generate bounded query entries using `stars:>100`, `pushed:>2026-05-01`, `archived:false`, `template:false`, `mirror:false`, and `is:public`.
- Include high-purity topics and architecture modifiers.
- Include a fresh breakout query with `stars:>20` only for high-intent phrases.
- Do not generate broad `pptx layout pushed:>=<date>` query.

- [ ] **Step 2: Implement `validateQueryMatrixEntry`**

Required behavior:
- Reject missing `pushed:`.
- Reject missing `is:public`, `archived:false`, or `template:false`.
- Reject broad generic-only search terms.
- Reject `page_limit > 2` and `per_page > 50`.

- [ ] **Step 3: Run focused test**

```bash
npm test -- tests/sentinel/artifactHintGuard.test.ts -t "builds SourcePlan v2"
```

Expected: PASS for Query Matrix test.

## Task 3: Artifact Guard Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactHintGuard.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactHintGuard.test.ts`

- [ ] **Step 1: Implement deterministic scan**

Required behavior:
- Detect ZIP/archive dominance.
- Detect local-pollution terms.
- Detect prompt-wrapper language.
- Detect missing architecture, test/example, and visual artifact signals.
- Compute deterministic `trust_score` and reason codes.

- [ ] **Step 2: Implement shadow evidence application**

Required behavior:
- `LOW_QUALITY_FILTERED` candidates write evidence through injected `writeEnvelopeEvidence`.
- `LOW_QUALITY_FILTERED` candidates do not call Blind Scout, Capturer, or Auditor callbacks.

- [ ] **Step 3: Run focused test**

```bash
npm test -- tests/sentinel/artifactHintGuard.test.ts -t "filters low-quality"
```

Expected: PASS for low-quality/evidence test.

## Task 4: Timeout Guard Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/artifactHintGuard.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/artifactHintGuard.test.ts`

- [ ] **Step 1: Implement bounded scanner timeout path**

Required behavior:
- Accept an injected scanner function for tests.
- Race scan against `maxScanMs`.
- On timeout or scanner exception, return `LOW_QUALITY_FILTERED` with `REGEX_SCAN_TIMEOUT`.
- Write NDJSON-compatible log event through injected logger.

- [ ] **Step 2: Run focused test**

```bash
npm test -- tests/sentinel/artifactHintGuard.test.ts -t "times out malformed"
```

Expected: PASS for timeout guard test.

## Task 5: Adapter/CLI Integration Green

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestratorCli.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestratorCli.test.ts`

- [ ] **Step 1: Call guard after README fetch**

Required behavior:
- Keep filtered candidates in envelope evidence.
- Exclude filtered candidates from runtime candidates.
- Do not pass archive-dominated artifact URLs to Capturer.

- [ ] **Step 2: Bind CLI to SourcePlan v2**

Required behavior:
- Replace broad query builder with `buildDefaultSourcePlanV2`.
- Log `source_query_matrix_built`.

- [ ] **Step 3: Run full verification**

```bash
npm run typecheck
npm test
```

Expected: all Sentinel tests PASS.

## Self-Review

- Spec coverage: Covers Query Matrix v2, query rejection, low-quality ZIP/prompt/local pollution filtering, shadow evidence, downstream zero-call assertions, timeout fallback, and CLI SourcePlan binding.
- Placeholder scan: No deferred implementation markers remain.
- Type consistency: Planned functions are `buildDefaultSourcePlanV2`, `validateQueryMatrixEntry`, `scanArtifactHintGuard`, and `applyArtifactHintGuard`.

