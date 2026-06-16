# Project Sentinel v3 Lead Promotion Scorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic Lead Promotion Scorer that ranks safe GitHub candidates by strategic relevance, promotes only the strongest Top 5, and isolates safe-but-off-topic candidates in `low_relevance_overflow`.

**Architecture:** Add a pure `leadPromotionScorer.ts` module beside `artifactHintGuard.ts`, then integrate it after `ArtifactHintGuard` inside `RealSourceAdapter`. The scorer uses linear substring matching only, returns structured score evidence, and never performs network, model, filesystem, or publish work.

**Tech Stack:** TypeScript, Vitest, existing Project Sentinel runtime types, deterministic string scanning, no new runtime dependency.

---

## File Map

- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/leadPromotionScorer.ts`
  - Owns score contracts, `scoreLeadPromotion`, `rankLeadPromotionCandidates`, overflow evidence, and `LeadPromotionScorerNotImplementedError`.
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/leadPromotionScorer.test.ts`
  - Owns Stage 9.1 Red tests for ranking inversion, Top-5 overflow, downstream zero-call, and composite positive/negative fingerprint evidence.
- Modify in Green phase: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
  - Calls scorer after `ArtifactHintGuard` passes and before returning candidates.
- Modify in Green phase: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`
  - Copies `low_relevance_overflow` into `scout_pipeline.shadow.json` when source adapters provide it.
- Modify in Green phase only if needed: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts`
  - Adds production zero-touch assertion for `low_relevance_overflow`.

## Reviewer Override to SDD Weights

The Red review added one sharper contract after the SDD:

```text
Composite README contains "typesetting pipeline" and "generic chart library"
expected score = base +50 -30
```

Green implementation must satisfy this TDD contract. If SDD and tests differ, update the SDD in a separate docs commit after Green rather than weakening the test.

## Task 1: Red Test and Interface Stub

**Files:**
- Create: `/Users/tristanzh/agent/Git-Scout/src/sentinel/leadPromotionScorer.ts`
- Create: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/leadPromotionScorer.test.ts`

- [ ] **Step 1: Add the interface-only scorer module**

```ts
export class LeadPromotionScorerNotImplementedError extends Error {
  constructor(method: string) {
    super(`${method} is not implemented`);
    this.name = "LeadPromotionScorerNotImplementedError";
  }
}

export type LeadPromotionInput = {
  repo: string;
  title: string;
  category: string;
  readme_digest: string;
  description: string;
  topics: string[];
  deterministic_score: number;
  artifact_url_candidates: string[];
};

export type LeadPromotionScore = {
  repo: string;
  relevance_score: number;
  base_quality_score: number;
  promote_reason_codes: string[];
  demote_reason_codes: string[];
  matched_positive_terms: string[];
  matched_negative_terms: string[];
  decision: "PROMOTE_CANDIDATE" | "LOW_RELEVANCE_OVERFLOW";
};

export function scoreLeadPromotion(_input: LeadPromotionInput): LeadPromotionScore {
  throw new LeadPromotionScorerNotImplementedError("scoreLeadPromotion");
}
```

- [ ] **Step 2: Add Red tests for rank inversion, overflow, and composite fingerprints**

```ts
import { describe, expect, it } from "vitest";
import { rankLeadPromotionCandidates, scoreLeadPromotion } from "../../src/sentinel/leadPromotionScorer.js";

describe("LeadPromotionScorer Stage 9.1 TDD contract", () => {
  it("promotes document layout engines above off-topic widgets and preserves stable order for tied candidates", () => {
    const result = rankLeadPromotionCandidates([iosWidgetLead(), ordinaryC, vmprintLead(), ordinaryD], {
      maxPromoted: 5,
      promotedFloor: 0,
      now: () => fixedNow
    });

    expect(result.promoted[0]?.repo).toBe("cosmiciron/vmprint");
    expect(result.promoted.map((lead) => lead.repo)).toEqual([
      "cosmiciron/vmprint",
      "github/ordinary-c",
      "github/ordinary-d",
      "zekunyan/ttgtagcollectionview"
    ]);
  });
});
```

- [ ] **Step 3: Run the new test to verify Red**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/leadPromotionScorer.test.ts
```

Expected:

```text
FAIL tests/sentinel/leadPromotionScorer.test.ts
LeadPromotionScorerNotImplementedError: rankLeadPromotionCandidates is not implemented
LeadPromotionScorerNotImplementedError: scoreLeadPromotion is not implemented
```

- [ ] **Step 4: Run typecheck**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
```

Expected:

```text
tsc --noEmit
```

Exit code must be `0`.

- [ ] **Step 5: Commit Red baseline**

Run:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-16-project-sentinel-v3-lead-scorer-implementation-plan.md \
  Git-Scout/src/sentinel/leadPromotionScorer.ts \
  Git-Scout/tests/sentinel/leadPromotionScorer.test.ts
git commit -m "test(sentinel): 编写 Stage 9.1 线索相关性打分、多维混排与 Top-5 溢出截断 TDD 集成测试"
```

## Task 2: Green Scorer Implementation

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/leadPromotionScorer.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/leadPromotionScorer.test.ts`

- [ ] **Step 1: Implement linear matching dictionaries**

```ts
const POSITIVE_GROUPS = [
  {
    code: "DOCUMENT_LAYOUT_ENGINE",
    weight: 50,
    terms: ["deterministic layout engine", "document layout engine", "layout engine", "pagination engine", "page layout engine"]
  },
  {
    code: "TYPESETTING_PIPELINE",
    weight: 50,
    terms: ["typesetting pipeline", "typesetting", "typst", "latex", "tex", "publishing", "dtp", "print-on-demand"]
  }
] as const;
```

- [ ] **Step 2: Implement `scoreLeadPromotion`**

```ts
export function scoreLeadPromotion(input: LeadPromotionInput): LeadPromotionScore {
  const haystack = normalize(`${input.repo} ${input.title} ${input.description} ${input.topics.join(" ")} ${input.readme_digest}`);
  const positive = collectMatches(haystack, POSITIVE_GROUPS);
  const negative = collectMatches(haystack, NEGATIVE_GROUPS);
  const relevance_score = clamp(input.deterministic_score + positive.weight - negative.weight + bonuses(input, haystack), 0, 200);
  return {
    repo: input.repo,
    relevance_score,
    base_quality_score: input.deterministic_score,
    promote_reason_codes: positive.codes,
    demote_reason_codes: negative.codes,
    matched_positive_terms: positive.terms,
    matched_negative_terms: negative.terms,
    decision: relevance_score >= 60 ? "PROMOTE_CANDIDATE" : "LOW_RELEVANCE_OVERFLOW"
  };
}
```

- [ ] **Step 3: Implement stable ranking and overflow**

```ts
export function rankLeadPromotionCandidates(inputs: LeadPromotionInput[], options: LeadPromotionRankingOptions): LeadPromotionRankingResult {
  const scored = inputs.map((input, index) => ({ input, index, score: scoreLeadPromotion(input) }));
  scored.sort((a, b) =>
    b.score.relevance_score - a.score.relevance_score ||
    b.score.base_quality_score - a.score.base_quality_score ||
    a.index - b.index
  );
  const promoted = scored.slice(0, options.maxPromoted).filter((item) => item.score.relevance_score >= options.promotedFloor);
  const overflow = scored.filter((item) => !promoted.includes(item));
  return buildRankingResult(promoted, overflow, options.now);
}
```

- [ ] **Step 4: Run scorer tests**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/leadPromotionScorer.test.ts
```

Expected:

```text
tests/sentinel/leadPromotionScorer.test.ts
3 passed
```

## Task 3: RealSourceAdapter Integration

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/realSourceAdapter.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/realSourceAdapter.test.ts`

- [ ] **Step 1: Add adapter-level Red test**

Add a test that returns seven safe candidates from GitHub mocks, including `vmprint`, `yamlresume`, and `ttgtagcollectionview`.

Assertions:

```ts
expect(result.candidates.map((candidate) => candidate.repo)[0]).toBe("cosmiciron/vmprint");
expect(result.candidates).toHaveLength(5);
expect(result.candidates.map((candidate) => candidate.repo)).not.toContain("zekunyan/ttgtagcollectionview");
expect(result.low_relevance_overflow["zekunyan/ttgtagcollectionview"]).toMatchObject({
  status: "LOW_RELEVANCE_OVERFLOW"
});
```

- [ ] **Step 2: Integrate scorer after guard pass**

Collect all guard-passed candidate inputs, call `rankLeadPromotionCandidates`, return only `promoted` as `candidates`, and return `low_relevance_overflow` in `RealSourceAdapterResult`.

- [ ] **Step 3: Run adapter tests**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/realSourceAdapter.test.ts
```

Expected:

```text
tests/sentinel/realSourceAdapter.test.ts
all tests passed
```

## Task 4: Runtime Shadow Pipeline Integration

**Files:**
- Modify: `/Users/tristanzh/agent/Git-Scout/src/sentinel/runtimeOrchestrator.ts`
- Test: `/Users/tristanzh/agent/Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts`

- [ ] **Step 1: Add runtime test for `low_relevance_overflow` propagation**

```ts
const sourceOverflow = {
  "zekunyan/ttgtagcollectionview": {
    repo: "zekunyan/ttgtagcollectionview",
    status: "LOW_RELEVANCE_OVERFLOW",
    source: "lead_promotion_scorer",
    captured_at: fixedNow.toISOString(),
    evidence: { demote_reason_codes: ["IOS_WIDGET_SCOPE", "UI_COMPONENT_ONLY"] }
  }
};
```

Assert the shadow pipeline includes `low_relevance_overflow` and production JSON remains unchanged.

- [ ] **Step 2: Copy overflow evidence through runtime source payload**

Extend `RuntimeSourceClient.fetchCandidates` result union to accept:

```ts
{
  candidates: RuntimeCandidate[];
  shadow_evidence?: RuntimeShadowEvidence;
  low_relevance_overflow?: Record<string, LowRelevanceOverflowEntry>;
}
```

- [ ] **Step 3: Run runtime tests**

Run:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test -- tests/sentinel/runtimeOrchestrator.test.ts
```

Expected:

```text
tests/sentinel/runtimeOrchestrator.test.ts
all tests passed
```

## Task 5: Full Verification and Commit

**Files:**
- Verify all touched files.

- [ ] **Step 1: Run full typecheck**

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
```

- [ ] **Step 2: Run full test suite**

```bash
cd /Users/tristanzh/agent/Git-Scout
npm test
```

- [ ] **Step 3: Run diff hygiene**

```bash
cd /Users/tristanzh/agent
git diff --check -- Git-Scout/src/sentinel/leadPromotionScorer.ts \
  Git-Scout/src/sentinel/realSourceAdapter.ts \
  Git-Scout/src/sentinel/runtimeOrchestrator.ts \
  Git-Scout/tests/sentinel/leadPromotionScorer.test.ts \
  Git-Scout/tests/sentinel/realSourceAdapter.test.ts \
  Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts
```

- [ ] **Step 4: Commit only Stage 9.1 files**

```bash
cd /Users/tristanzh/agent
git add Git-Scout/src/sentinel/leadPromotionScorer.ts \
  Git-Scout/src/sentinel/realSourceAdapter.ts \
  Git-Scout/src/sentinel/runtimeOrchestrator.ts \
  Git-Scout/tests/sentinel/leadPromotionScorer.test.ts \
  Git-Scout/tests/sentinel/realSourceAdapter.test.ts \
  Git-Scout/tests/sentinel/runtimeOrchestrator.test.ts
git commit -m "fix(sentinel): 实现 Lead Promotion Scorer 相关性排序与低相关溢出隔离"
```

## Self-Review

Spec coverage:

- Ranking inversion is covered by Task 1 and Task 2.
- Top-5 overflow is covered by Task 1 and Task 3.
- Composite positive/negative fingerprint output is covered by Task 1 and Task 2.
- Downstream zero-call is covered by Task 1 and Task 4.
- Production zero-touch is covered by Task 4.

Placeholder scan:

- This plan contains no unresolved placeholder markers.

Type consistency:

- `LeadPromotionInput`, `LeadPromotionScore`, `LowRelevanceOverflowEntry`, and `low_relevance_overflow` match the Stage 9.1 SDD naming.
