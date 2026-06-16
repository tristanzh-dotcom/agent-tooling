# Project Sentinel v3 Source Tightening and Artifact Fingerprint Guard SDD

Date: 2026-06-16
Status: Draft for red-line specification review
Owner: TZ
Baseline commit: `35fb31e`
Parent SDD:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-real-source-adapter-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
Implementation root: `/Users/tristanzh/agent/Git-Scout`
Live probe evidence:
- `/Users/tristanzh/agent/Git-Scout/storage/runtime_shadow/runtime_probe_live_20260616T103100Z/scout_pipeline.shadow.json`
- rejected probe pattern: README links that repeatedly point to downloadable ZIP payloads instead of architecture, examples, or inspectable generated assets.

## 1. Objective

Stage 8 tightens the Real Source Adapter after the first live GitHub dry-run. The live probe proved the network path works, but it also showed that broad keyword search admits low-value repositories whose README files are dominated by "download this ZIP" flows instead of visible architecture, tests, examples, or layout engine evidence.

This stage adds a deterministic upstream quality guard:

```text
GitHub Query Matrix
  -> Raw README fetch
  -> Artifact Hint Guard
  -> Trust-chain fingerprint score
  -> LOW_QUALITY_FILTERED or RuntimeCandidate
  -> Blind Scout / Capturer / Dashboard
```

The goal is not to make the adapter "smart." The goal is to reject obvious low-quality and local-pollution candidates before they consume token budget, Capturer bandwidth, or TZ attention.

## 2. Source Facts and Query Constraints

This SDD relies on GitHub's official repository search and REST Search documentation.

Usable repository search qualifiers include:

- `stars:` for star count thresholds and ranges.
- `pushed:` for last repository activity dates.
- `topic:` for repository topics.
- `in:name`, `in:description`, `in:topics`, and `in:readme` for search scope.
- `is:public`, `archived:false`, `template:false`, and `mirror:false` for repository shape.
- `language:` and `license:` for optional future narrowing.

GitHub documents that repository search can search repository name, description, topics, and README content, and that `pushed` uses ISO date syntax such as `YYYY-MM-DD`. The REST Search API remains the transport, but query construction must stay within bounded, deterministic query packs.

References:
- GitHub repository search qualifiers: https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories
- GitHub REST Search API: https://docs.github.com/en/rest/search/search

## 3. Non-Goals

- Do not introduce LLM-based quality scoring in this stage.
- Do not fetch source trees, clone repositories, install packages, or execute code.
- Do not call Tier-3 Auditor before TZ approval.
- Do not publish live probe output directly to Agent07.
- Do not remove Runtime dry-run/live-network/live-model/live-publish gates.
- Do not rely on GitHub HTML Trending.
- Do not treat `stars:>100` as proof of quality. It is a coarse hygiene threshold only.

## 4. Problem Statement from Probe

The live dry-run found two repositories:

```text
muhammadfaisalshareef/pdf2ppt
wozzeck16621/pptx-from-layouts-skill
```

Both matched broad presentation/PDF keywords. Both also exhibited low-trust public-source signals:

- README repeatedly routes users to a raw ZIP download.
- visible artifact hints point to archive payloads, not inspectable screenshots, docs, or generated examples.
- README reads like installation marketing rather than architecture or implementation evidence.
- no upstream signal that the project contains a layout engine, constraint system, rendering pipeline, tests, or examples worth spending strong-reasoning budget on.

Stage 7 was correct to keep these candidates inside `runtime_shadow`. Stage 8 makes this pattern mechanically rejectable.

## 5. Design Alternatives

### Option A: Tighten GitHub Query Matrix Only

Use stricter GitHub search qualifiers such as `stars:>100`, `pushed:>2026-05-01`, `topic:layout-engine`, `archived:false`, `template:false`, and `in:readme`.

Pros:
- Cheap and upstream.
- Reduces noisy search pages.
- Uses official query syntax.

Cons:
- Star thresholds can miss new high-value projects.
- Topics are inconsistently applied by repository owners.
- Does not catch ZIP-dominated README spam when it still passes query filters.

### Option B: Add README Artifact Fingerprint Guard Only

Keep broad search, then classify README and artifact hints with deterministic regex and score gates.

Pros:
- Directly catches observed bad probe pattern.
- Works even when GitHub topics are weak.

Cons:
- Still spends Search and README fetches on broad queries.
- Requires careful false-positive handling.

### Option C: Query Matrix + Fingerprint Guard

First narrow the source plan with GitHub qualifiers, then apply deterministic README and artifact hint fingerprints before candidates enter Blind Scout.

Pros:
- Reduces network waste and token waste.
- Directly encodes live-probe failures.
- Keeps all judgments reproducible and testable.

Cons:
- More moving parts and thresholds to test.

### Decision

Implement Option C. The Query Matrix reduces broad garbage; the Artifact Hint Guard catches low-trust README patterns that still pass search.

## 6. Query Matrix v2

The SourcePlan becomes a multi-matrix rather than one broad query. Each query must be narrow, explainable, and individually capped.

```ts
type SourcePlanV2 = {
  version: 2;
  date: string;
  query_window: {
    pushed_after: string;
    min_stars_default: 100;
    min_stars_fresh_breakout: 20;
  };
  max_candidates_before_blind_scout: number;
  github_query_matrix: QueryMatrixEntry[];
};

type QueryMatrixEntry = {
  id: string;
  intent:
    | "layout_engine"
    | "vector_graphics"
    | "typesetting"
    | "pptx_generation"
    | "document_renderer"
    | "multimodal_artifact";
  q: string;
  sort: "updated" | "stars";
  order: "desc";
  page_limit: number;
  per_page: number;
  min_quality_floor: number;
  enabled: boolean;
};
```

### 6.1 Default Query Matrix

The implementation must generate query strings from deterministic templates. The initial matrix:

```text
topic:layout-engine stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
topic:vector-graphics stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
topic:typesetting stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
("constraint layout" OR "layout engine") in:readme stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
("pptx" "layout") in:readme stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
("pdf" "renderer" "layout") in:readme stars:>100 pushed:>2026-05-01 archived:false template:false mirror:false is:public
```

Fresh breakout exception:

```text
("relative layout" OR "constraint engine") in:readme stars:>20 pushed:>2026-06-01 archived:false template:false mirror:false is:public
```

This exception allows new projects to enter only when they carry high-intent technical phrases, not generic `pptx` or `pdf` tokens.

### 6.2 Query Rejection Rules

SourcePlan builder must reject query entries that:

- omit `pushed:`;
- omit `is:public`;
- omit `archived:false`;
- omit `template:false`;
- use only generic terms such as `ppt`, `pdf`, `slide`, or `presentation` without an architectural modifier;
- request more than `page_limit=2`;
- request more than `per_page=50`.

## 7. Artifact Hint Guard

The guard runs after raw README fetch and before creating a `RuntimeCandidate`.

```ts
type ArtifactHintGuardResult = {
  status: "PASS" | "LOW_QUALITY_FILTERED";
  roi_multiplier: number; // 0 for hard-filtered repos
  trust_score: number;    // 0..100 deterministic score
  positive_fingerprints: string[];
  negative_fingerprints: string[];
  checkpoint_marker?: "LOW_QUALITY_FILTERED";
  reason_codes: ArtifactGuardReasonCode[];
};

type ArtifactGuardReasonCode =
  | "ZIP_DOWNLOAD_DOMINATED"
  | "LOCAL_INSTALL_POLLUTION"
  | "NO_ARCHITECTURE_SIGNAL"
  | "NO_TEST_OR_EXAMPLE_SIGNAL"
  | "NO_VISUAL_ARTIFACT_SIGNAL"
  | "ARCHIVE_AS_PRIMARY_ARTIFACT"
  | "PROMPT_WRAPPER_LANGUAGE"
  | "PASS_HIGH_TRUST_ARCHITECTURE"
  | "PASS_VISUAL_EXAMPLES"
  | "PASS_TESTS_AND_DOCS";
```

## 8. Negative Fingerprint Rules

The guard must scan README text, markdown links, image URLs, and extracted artifact hints.

### 8.1 ZIP Download Dominance

Hard-filter when either condition is true:

- more than 50% of artifact hints end in `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.exe`, `.dmg`, `.pkg`, or `.msi`;
- README contains repeated download-action language and the primary calls to action point at archive payloads.

Patterns:

```text
download zip manually
download the zip
download package
extract files
double-click the file
run the application
visit the releases page to download
raw/refs/heads/*/*.zip
```

### 8.2 Local Environment Pollution

Hard-filter when README asks users to place files into unsafe or host-specific locations.

Patterns:

```text
place in root folder
copy to C:\
extract to C:\
run as administrator
disable antivirus
chmod 777
sudo curl
curl ... | sh
```

### 8.3 Prompt Wrapper Language

Score penalty when README describes prompt-only positioning without code-level layout evidence.

Patterns:

```text
prompt determines position
AI decides placement
generate slides with a prompt
no code required
just describe your desired layout
```

This is not an automatic hard filter by itself. It becomes hard-filtered when combined with no architecture/test/example signal.

### 8.4 Missing Trust Chain

Hard-filter when all of these are absent:

- architecture section or architecture diagram;
- layout/rendering pipeline description;
- examples or gallery with inspectable images/PDFs;
- tests, benchmark, snapshot, or golden output mention;
- exported artifacts that are not archives.

## 9. Positive Fingerprint Rules

Positive signals raise trust score and allow fresh projects through even when star count is modest.

### 9.1 Architecture Evidence

Patterns:

```text
architecture
rendering pipeline
layout engine
constraint solver
relative coordinates
flow layout
grid layout
auto layout
typesetting engine
scene graph
measure / arrange
```

### 9.2 Test and Example Evidence

Patterns:

```text
test
snapshot
golden
fixture
examples/
gallery
demo
benchmark
visual regression
```

### 9.3 Inspectable Visual Artifacts

Accepted primary artifact hints:

```text
.png
.jpg
.jpeg
.webp
.svg
.pdf
githubusercontent.com
docs/
examples/
gallery/
```

Archive artifacts may remain as secondary links, but they must not dominate the artifact set.

## 10. Trust Score Formula

The guard computes a deterministic 0..100 score:

| Component | Points |
| --- | ---: |
| architecture evidence | +30 |
| test/example evidence | +20 |
| inspectable visual artifacts | +25 |
| high-intent query match | +15 |
| maintained project metadata | +10 |
| ZIP/download dominance | -45 |
| local pollution pattern | -100 |
| missing trust chain | -40 |
| prompt-wrapper language without architecture | -25 |

Decision:

```text
trust_score <= 0 -> LOW_QUALITY_FILTERED, roi_multiplier=0
hard negative present -> LOW_QUALITY_FILTERED, roi_multiplier=0
trust_score < 45 -> LOW_QUALITY_FILTERED, roi_multiplier=0
trust_score >= 45 -> PASS
trust_score >= 70 -> PASS_HIGH_TRUST
```

## 11. Checkpoint and Envelope Contract

Filtered repositories must be retained in shadow evidence but excluded from `RuntimeCandidate[]`.

```ts
type SourceCandidateEnvelopeV2 = SourceCandidateEnvelope & {
  guard: ArtifactHintGuardResult;
};
```

Source checkpoint readme entries gain a filter state:

```ts
type ReadmeCheckpointStatus =
  | "PENDING"
  | "FETCHED"
  | "TRUNCATED"
  | "LOW_QUALITY_FILTERED"
  | "FAILED_RETRYABLE"
  | "FAILED_TERMINAL"
  | "SKIPPED_BLACKLIST";
```

Rules:

- `LOW_QUALITY_FILTERED` repos are not sent to Blind Scout.
- `LOW_QUALITY_FILTERED` repos are not sent to Capturer.
- `LOW_QUALITY_FILTERED` repos do not count toward the Top-5 user-facing candidate limit.
- They remain in `source_candidates.envelope.json` with reason codes for audit.
- They may optionally be added to a soft blacklist after repeated appearances, but not in this stage.

## 12. Runtime CLI Integration

`runtimeOrchestratorCli.ts` must stop constructing one broad query. It must call a SourcePlan builder:

```ts
buildDefaultSourcePlanV2({
  date: config.date,
  pushed_after: "2026-05-01",
  min_stars_default: 100,
  min_stars_fresh_breakout: 20,
  max_candidates_before_blind_scout: config.limits.max_candidates
});
```

No CLI flag should expose arbitrary raw query text in this stage. Query plans remain source-controlled and testable.

## 13. Observability

Required NDJSON events:

```text
source_query_matrix_built
source_query_rejected
artifact_guard_scanned
artifact_guard_filtered
artifact_guard_passed
source_candidates_filtered_summary
```

Example:

```json
{
  "timestamp": "2026-06-16T10:40:00.000Z",
  "level": "INFO",
  "component": "realSourceAdapter.guard",
  "event": "artifact_guard_filtered",
  "meta": {
    "run_id": "runtime_20260616T104000Z",
    "repo": "muhammadfaisalshareef/pdf2ppt",
    "status": "LOW_QUALITY_FILTERED",
    "trust_score": 0,
    "reason_codes": ["ZIP_DOWNLOAD_DOMINATED", "NO_ARCHITECTURE_SIGNAL"],
    "github_token_status": "unset"
  }
}
```

## 14. Security Boundaries

- Negative fingerprint regex must run on bounded README digest only.
- Regex must be static and source-controlled; no user-provided regex in CLI.
- URLs are still only hints; Capturer must re-check URL safety before download.
- `.zip`, `.exe`, `.dmg`, `.pkg`, and `.msi` links must not be passed to Capturer as primary visual artifacts.
- No automatic permanent blacklist in this stage; hard filters are shadow-run decisions until TZ accepts them.

## 15. TDD Matrix for Next Phase

### Test 1: Query Matrix Rebuild

Given a fixed date, `buildDefaultSourcePlanV2` must emit only bounded queries that include `pushed:>2026-05-01`, `is:public`, `archived:false`, `template:false`, and either a high-purity topic or an architecture modifier. Assert no broad `pptx layout pushed:>=date` query remains.

### Test 2: Query Rejection

Given a query missing `pushed:` or using only generic `pptx pdf presentation` terms, validator rejects it with `SOURCE_QUERY_TOO_BROAD`.

### Test 3: ZIP Download Dominance Filter

Use the real dry-run style README pattern where multiple CTA links point to `.zip`. Assert guard returns `LOW_QUALITY_FILTERED`, `roi_multiplier=0`, and reason codes include `ZIP_DOWNLOAD_DOMINATED`.

### Test 4: Local Pollution Filter

README containing `copy to C:\`, `run as administrator`, or `curl ... | sh` must hard-filter with `LOCAL_INSTALL_POLLUTION`.

### Test 5: Missing Trust Chain Filter

README that mentions presentation generation but has no architecture, examples, tests, or inspectable visual artifact hints must be `LOW_QUALITY_FILTERED`.

### Test 6: High-ROI Layout Engine Retention

README containing architecture evidence, relative coordinates, tests, examples, and SVG/PDF artifact hints must pass with `trust_score >= 70`.

### Test 7: Prompt Wrapper Penalty

README with prompt-only placement language but also real architecture and tests must be penalized but not automatically hard-filtered. Assert score remains deterministic.

### Test 8: Envelope Retention

Filtered repos must appear in `source_candidates.envelope.json` with guard reason codes but must not appear in `source_candidates.runtime.json`.

### Test 9: Capturer Isolation

Archive-dominated candidates must not pass archive URLs to Capturer. Assert Capturer call count remains 0 for `LOW_QUALITY_FILTERED` repos.

### Test 10: Runtime CLI SourcePlan Binding

`npm run sentinel:daily -- --live-network=true --dry-run` must use SourcePlan v2 builder and record `source_query_matrix_built` in logs.

## 16. Acceptance Criteria

Stage 8 is accepted when:

- all new TDD tests pass;
- all existing 30 Sentinel tests pass;
- `npm run typecheck` passes;
- the two low-quality probe repositories are filtered in a deterministic fixture test;
- high-trust layout-engine fixtures still pass;
- live dry-run produces either zero candidates or only candidates with `PASS` guard status;
- no filtered repository reaches Blind Scout, Capturer, Dashboard Controller, or Hardcore Auditor.

## 17. Expected Implementation Files

```text
Git-Scout/src/sentinel/sourcePlan.ts
Git-Scout/src/sentinel/artifactHintGuard.ts
Git-Scout/src/sentinel/realSourceAdapter.ts
Git-Scout/src/sentinel/runtimeOrchestratorCli.ts
Git-Scout/tests/sentinel/sourceTightening.test.ts
Git-Scout/tests/fixtures/sources/low-quality-zip-readme.md
Git-Scout/tests/fixtures/sources/high-trust-layout-readme.md
```

## 18. Open Decisions

1. The initial `stars:>100` floor is a hygiene default, not a quality proof. The fresh breakout query permits `stars:>20` only with high-intent technical phrases.
2. Archive links are not globally evil; they are disallowed as primary visual artifacts and as dominant README trust evidence.
3. This stage should not auto-blacklist filtered repos permanently. Permanent blacklist remains a TZ dashboard decision unless a future SDD introduces repeated-observation quarantine.

