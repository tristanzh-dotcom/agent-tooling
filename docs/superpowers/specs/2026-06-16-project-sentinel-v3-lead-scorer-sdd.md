# Project Sentinel v3 Lead Promotion Scorer SDD

Date: 2026-06-16
Status: Draft for red-line specification review
Owner: TZ
Baseline evidence:
- Stage 9 live dry-run: `runtime_20260616T071434Z`
- Observed mainline leads: `yamlresume/yamlresume`, `texlyre/texlyre`, `nteract/semiotic`, `zekunyan/ttgtagcollectionview`, `cosmiciron/vmprint`
- Observed issue: safe and high-quality-but-off-topic candidates can outrank deeper document layout assets.
Parent SDD:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-source-tightening-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-query-timeout-guard-sdd.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-runtime-orchestrator-sdd.md`
Implementation root: `/Users/tristanzh/agent/Git-Scout`

## 1. Objective

Stage 9.1 adds a deterministic relevance ranking layer after `ArtifactHintGuard` and before runtime pipeline promotion. Stage 8 and Stage 9 proved that the system is safe: low-quality and local-pollution candidates are isolated, network hangs are bounded, and production data remains untouched during dry-runs.

The remaining problem is purity, not safety. A repository can be legitimate, maintained, and visually documented while still being strategically irrelevant to Project Sentinel's target: high-end document, presentation, publishing, layout, and multimodal asset generation tools.

The new flow is:

```text
RealSourceAdapter
  -> ArtifactHintGuard removes unsafe or low-trust candidates
  -> LeadPromotionScorer ranks surviving candidates by strategic relevance
  -> Top 5 become RuntimeCandidate leads
  -> Non-promoted candidates are moved to low_relevance_overflow evidence
  -> Blind Scout / Capturer / Dashboard only see the promoted Top 5
```

## 2. Non-Goals

- Do not call any LLM for relevance scoring.
- Do not change GitHub Search query execution or Stage 9 timeout behavior.
- Do not loosen `ArtifactHintGuard`; unsafe candidates must remain filtered before scoring.
- Do not publish live probe results to `data/scout_pipeline.json`.
- Do not hard-reject all off-topic candidates at the guard layer. Stage 9.1 demotes them and records evidence.
- Do not change the Agent07 visual layout.
- Do not clone repositories, install packages, or fetch source trees.

## 3. Problem Statement from Probe Run v3

Probe `runtime_20260616T071434Z` produced a safe but mixed-quality Top 5:

| Repo | Actual fit | Issue |
|---|---|---|
| `cosmiciron/vmprint` | Excellent | Deterministic document layout engine with glyph coordinates and pagination. Should rank first. |
| `texlyre/texlyre` | Strong | Typst/LaTeX local-first editor with visual artifacts and compilation flow. |
| `nteract/semiotic` | Medium | Valuable AI-assisted visualization library, but not a document or presentation layout engine. |
| `yamlresume/yamlresume` | Medium-low | Good resume-to-PDF tool, but narrow resume-only workflow. |
| `zekunyan/ttgtagcollectionview` | Low | Good iOS layout widget, but irrelevant to high-end asset generation. |

The deterministic quality score currently rewards general layout, images, tests, and recent activity. It does not distinguish:

- document/publishing layout engines from UI widgets;
- deterministic pagination from generic rendering;
- multimodal/PPT/document asset tools from chart libraries;
- resume-only utilities from general high-end production pipelines.

Stage 9.1 must preserve safety while enforcing strategic fit.

## 4. Lead Promotion Scorer Boundary

### 4.1 Placement

The scorer runs after README digest creation and after `ArtifactHintGuard` returns `PASS`.

```text
GitHub Search item
  -> README digest
  -> ArtifactHintGuard
    -> LOW_QUALITY_FILTERED: shadow_evidence only
    -> PASS: scoreLeadPromotion()
  -> sort candidates by relevance_score
  -> promote Top 5 to leads
  -> write overflow evidence for demoted candidates
```

### 4.2 Input Contract

```ts
type LeadPromotionInput = {
  repo: string;
  title: string;
  category: string;
  readme_digest: string;
  description: string;
  topics: string[];
  deterministic_score: number;
  artifact_url_candidates: string[];
};
```

The input must be derived only from already-fetched metadata and README digest. The scorer must not perform network calls.

### 4.3 Output Contract

```ts
type LeadPromotionScore = {
  repo: string;
  relevance_score: number;
  base_quality_score: number;
  promote_reason_codes: LeadPromoteReasonCode[];
  demote_reason_codes: LeadDemoteReasonCode[];
  matched_positive_terms: string[];
  matched_negative_terms: string[];
  decision: "PROMOTE_CANDIDATE" | "LOW_RELEVANCE_OVERFLOW";
};
```

The final `RuntimeCandidate` should carry the original `qualityScore` and may add `relevanceScore` in the implementation plan if the existing type needs it for observability. If changing `RuntimeCandidate` has wider blast radius, the score may live in envelope metadata and overflow evidence only.

## 5. Weight Scoring Contract

### 5.1 Base Formula

The scorer computes a deterministic linear score:

```text
relevance_score =
  deterministic_score
  + strategic_positive_weight
  - strategic_negative_weight
  + artifact_bonus
  + topic_bonus
```

Hard limits:

- clamp final score to `0..200`;
- never promote a candidate with `decision = LOW_RELEVANCE_OVERFLOW`;
- sort by `relevance_score desc`, then `deterministic_score desc`, then `repo asc` for deterministic tie-breaking.

### 5.2 Positive Strategic Fingerprints

Each matched group adds the listed weight once. Matching is case-insensitive and uses linear substring scanning over:

```text
repo + title + description + topics.join(" ") + readme_digest
```

No compound backtracking regex is allowed.

| Reason code | Weight | Terms |
|---|---:|---|
| `DOCUMENT_LAYOUT_ENGINE` | +50 | `deterministic layout engine`, `document layout engine`, `layout engine`, `pagination engine`, `page layout engine` |
| `GLYPH_COORDINATE_OUTPUT` | +50 | `glyph coordinates`, `glyph x/y`, `text run coordinates`, `box coordinates`, `flat array of exact`, `positioned primitives` |
| `DETERMINISTIC_PAGINATION` | +45 | `deterministic pagination`, `page breaks`, `widow`, `orphan`, `table of contents`, `single-pass toc`, `pagination` |
| `TYPESETTING_PIPELINE` | +40 | `typesetting`, `typst`, `latex`, `tex`, `publishing`, `dtp`, `print-on-demand` |
| `REPORT_GENERATION` | +35 | `report generation`, `document generation`, `pdf generation`, `markdown to pdf`, `html to pdf`, `pdf export` |
| `VECTOR_CANVAS_RENDERING` | +30 | `canvas`, `svg`, `vector graphics`, `webgl`, `gpu draw`, `rendering pipeline` |
| `PPT_OR_SLIDE_EXPORT` | +35 | `pptx`, `powerpoint`, `slide generation`, `presentation generation`, `deck export` |
| `MULTIMODAL_ARTIFACT_OUTPUT` | +25 | `screenshot`, `preview`, `gallery`, `showcase`, `examples`, `generated assets` |

Example expected effect:

```text
cosmiciron/vmprint:
  deterministic_score 75
  + DOCUMENT_LAYOUT_ENGINE 50
  + GLYPH_COORDINATE_OUTPUT 50
  + DETERMINISTIC_PAGINATION 45
  + TYPESETTING_PIPELINE 40
  => clamped 200, must rank above UI widgets and chart libraries
```

### 5.3 Negative Strategic Fingerprints

Demotions reduce rank but do not automatically mark a repo unsafe. They only affect Top-5 eligibility and overflow routing.

| Reason code | Weight | Terms |
|---|---:|---|
| `RESUME_ONLY_NARROWNESS` | -30 | `resume`, `cv builder`, `curriculum vitae`, `jsonresume`, `yaml resume`, `resume template` |
| `IOS_WIDGET_SCOPE` | -45 | `ios`, `cocoapods`, `swiftui`, `uikit`, `collectionview`, `tag view`, `ios widget` |
| `GENERIC_CHART_LIBRARY` | -25 | `chart library`, `react chart`, `data visualization library`, `dashboard charts`, `linechart`, `barchart` |
| `AWESOME_LIST_OR_INDEX` | -45 | `awesome list`, `awesome-`, `curated list`, `resources list` |
| `TASK_APP_OR_DEMO_APP` | -40 | `task app`, `todo app`, `demo app`, `example app`, `starter template`, `boilerplate` |
| `MCP_DIRECTORY_ONLY` | -35 | `awesome mcp`, `mcp servers list`, `directory of servers` |
| `UI_COMPONENT_ONLY` | -30 | `button component`, `tag component`, `ui widget`, `mobile component`, `component library` |

Example expected effect:

```text
zekunyan/ttgtagcollectionview:
  deterministic_score 79
  + VECTOR_CANVAS_RENDERING 0
  - IOS_WIDGET_SCOPE 45
  - UI_COMPONENT_ONLY 30
  => relevance_score 4, should not occupy a Top-5 slot when stronger layout assets exist
```

### 5.4 Artifact and Topic Bonuses

The scorer can add small bonuses for proof quality:

| Signal | Weight |
|---|---:|
| Two or more accepted visual artifact URLs | +10 |
| Topic contains `layout-engine`, `typesetting`, `typst`, `latex`, `pdf-generation`, `publishing`, `pptx`, `svg`, `canvas` | +15 |
| README contains an explicit `Architecture` section and a visual example | +10 |

These bonuses must never compensate for hard local-pollution or low-quality guard failures because those candidates never reach the scorer.

## 6. Top-5 Slicing and Overflow Sandbox

### 6.1 Promotion Algorithm

```text
scored = pass_candidates.map(scoreLeadPromotion)
sorted = scored.sort(relevance desc, deterministic desc, repo asc)
promoted = sorted.slice(0, 5)
overflow = sorted.slice(5).filter(candidate => candidate.relevance_score < promoted_floor)
```

The implementation plan must define `promoted_floor`. Initial contract:

```text
promoted_floor = max(60, score of 5th promoted candidate)
```

If fewer than five candidates score above 60, the system may publish fewer than five leads. It must not fill empty slots with low-relevance candidates just to satisfy a visual count.

### 6.2 Overflow Evidence Contract

Stage 9.1 adds a second evidence bucket distinct from `shadow_evidence`:

```ts
type LowRelevanceOverflowEntry = {
  repo: string;
  status: "LOW_RELEVANCE_OVERFLOW";
  source: "lead_promotion_scorer";
  captured_at: string;
  evidence: LeadPromotionScore;
};

type RuntimePipelineState = {
  // existing fields
  shadow_evidence?: RuntimeShadowEvidence;
  low_relevance_overflow?: Record<string, LowRelevanceOverflowEntry>;
};
```

Rules:

- `LOW_QUALITY_FILTERED` remains for unsafe or low-trust repos.
- `LOW_RELEVANCE_OVERFLOW` is for safe but strategically weak repos.
- Overflow entries must not enter `leads`.
- Overflow entries must not trigger `Blind Scout`, `Capturer`, `Dashboard Approve`, or `Hardcore Auditor`.
- Overflow entries must stay under `storage/runtime_shadow/<run_id>/` in dry-run mode.
- Overflow evidence must be deterministic and JSON-serializable.

### 6.3 Production Data Safety

Dry-run mode must preserve the existing Stage 6 rule:

```text
--live-publish=false
  -> write only runtime_shadow
  -> never mutate data/scout_pipeline.json
```

The scorer must not write directly to production paths. It only influences the data passed into the existing shadow pipeline writer.

## 7. Observability

The scorer must produce structured evidence suitable for NDJSON logging and future Agent07 visualization.

Recommended event names:

```text
lead_promotion_scored
lead_promotion_top5_selected
lead_low_relevance_overflowed
```

Example NDJSON payload:

```json
{
  "timestamp": "2026-06-16T07:20:00.000Z",
  "level": "INFO",
  "component": "leadPromotionScorer",
  "event": "lead_low_relevance_overflowed",
  "meta": {
    "run_id": "runtime_20260616T071434Z",
    "repo": "zekunyan/ttgtagcollectionview",
    "relevance_score": 4,
    "demote_reason_codes": ["IOS_WIDGET_SCOPE", "UI_COMPONENT_ONLY"]
  }
}
```

The log must not contain GitHub tokens, raw README bodies, or full user environment snapshots.

## 8. Integration Boundaries

### 8.1 RealSourceAdapter

`RealSourceAdapter` should remain responsible for:

- GitHub Search;
- README fetch;
- UTF-8 safe truncation;
- `ArtifactHintGuard`;
- producing `SourceCandidateEnvelope`.

The scorer can be invoked inside `RealSourceAdapter` after candidate construction, or as a small pure helper called by `RuntimeOrchestrator` before creating `RuntimePipelineLead[]`. The implementation plan must choose the smaller blast radius.

Preferred initial placement:

```text
RealSourceAdapter fetchCandidates()
  -> build all PASS candidates
  -> apply LeadPromotionScorer
  -> return candidates = promotedTop5
  -> return low_relevance_overflow evidence
```

Reason: Stage 9.1 is source-quality filtering. Keeping it beside `ArtifactHintGuard` prevents weak candidates from reaching downstream runtime components.

### 8.2 RuntimeOrchestrator

If `RealSourceAdapterResult` gains `low_relevance_overflow`, `RuntimeOrchestrator` must copy it into `scout_pipeline.shadow.json` the same way it copies `shadow_evidence`.

No other runtime behavior should change.

### 8.3 Capturer

Capturer must only receive promoted leads. It must not download artifacts for overflow candidates.

### 8.4 Dashboard

Agent07 should continue to read `leads` as before. A future UI stage may display overflow evidence, but Stage 9.1 does not require UI changes.

## 9. TDD Matrix for Next Stage

### 9.1 Positive-vs-Off-Topic Ranking Regression

Fixture candidates:

- `cosmiciron/vmprint`: README contains deterministic layout engine, glyph coordinates, pagination, report generation, canvas/vector output.
- `zekunyan/ttgtagcollectionview`: README contains iOS, Swift, CocoaPods, CollectionView, tag layout component.
- `nteract/semiotic`: README contains chart library and AI-assisted visualization.
- `yamlresume/yamlresume`: README contains resume, CV, YAML resume, LaTeX PDF.

Assertions:

```text
score(vmprint).relevance_score > score(texlyre).relevance_score
score(vmprint).relevance_score > score(ttgtagcollectionview).relevance_score
sorted[0].repo === "cosmiciron/vmprint"
ttgtagcollectionview is not promoted when five stronger layout/document candidates exist
```

### 9.2 Top-5 Slicing and Overflow Evidence

Input:

- seven safe candidates;
- five contain document/layout/publishing signals;
- two contain off-topic widget/chart/resume signals.

Assertions:

```text
promoted.length === 5
promoted are sorted by relevance_score descending
overflow contains the two demoted candidates with status LOW_RELEVANCE_OVERFLOW
overflow evidence contains demote_reason_codes and matched_negative_terms
```

### 9.3 Downstream Zero-Call Contract

Use injected spies for Blind Scout, Capturer, and Auditor.

Assertions:

```text
overflow candidates do not call Blind Scout
overflow candidates do not call Capturer
overflow candidates do not call Auditor
```

If the implementation keeps scoring inside `RealSourceAdapter`, this can be asserted by verifying the returned `candidates` array only includes promoted repos and downstream runtime receives only that array.

### 9.4 Production Zero-Touch

Run runtime in:

```bash
npm run sentinel:daily -- --live-network=true --live-model=false --live-publish=false
```

With mocked source data and file stores.

Assertions:

```text
storage/runtime_shadow/<run_id>/scout_pipeline.shadow.json contains low_relevance_overflow
data/scout_pipeline.json remains byte-for-byte unchanged
```

### 9.5 Tie-Break Determinism

Input:

- three candidates with identical `relevance_score`;
- different deterministic quality scores and repo names.

Assertions:

```text
sort order is relevance_score desc, deterministic_score desc, repo asc
repeated runs produce byte-identical promoted repo order
```

### 9.6 No Regex ReDoS Regression

Input:

- one 50KB README with long repeated punctuation and no whitespace;
- one normal positive README.

Assertions:

```text
scoring completes without blocking
no heavy regex is required
normal positive candidate still ranks correctly
```

The implementation should reuse the Stage 8 rule: linear `includes` scanning only.

## 10. Acceptance Criteria

Stage 9.1 is complete only when:

- a pure `scoreLeadPromotion()` or equivalent helper exists with deterministic positive and negative fingerprints;
- `vmprint`-style candidates outrank iOS widgets, resume-only tools, and generic chart libraries;
- `leads` are sorted by `relevance_score desc`;
- `leads` contain at most five candidates;
- safe but weak candidates move to `low_relevance_overflow`;
- overflow candidates do not trigger downstream token, capture, or audit work;
- dry-run mode leaves `data/scout_pipeline.json` unchanged;
- all existing tests remain green;
- new TDD tests fail before implementation and pass after implementation.

## 11. Red-Line Rules

- No LLM relevance scoring.
- No production publish in scorer tests.
- No network calls inside scorer.
- No hard rejection of safe candidates solely for being off-topic; use overflow evidence.
- No regex patterns capable of catastrophic backtracking.
- No silent discard: every demoted safe candidate must carry evidence.
- No Top-5 fill with low relevance candidates below the initial `60` floor.

## 12. Self-Review

Spec coverage:

- Positive promotion weights are defined in section 5.2.
- Soft demotion weights are defined in section 5.3.
- Top-5 slicing and overflow sandbox are defined in section 6.
- Production zero-touch is defined in sections 6.3 and 9.4.
- TDD matrix includes ranking regression, overflow evidence, downstream zero-call, production safety, deterministic tie-breaking, and ReDoS safety.

Placeholder scan:

- This SDD contains no unresolved implementation placeholders.

Type consistency:

- `LeadPromotionInput`, `LeadPromotionScore`, `LowRelevanceOverflowEntry`, and `RuntimePipelineState.low_relevance_overflow` use consistent field names across the document.
