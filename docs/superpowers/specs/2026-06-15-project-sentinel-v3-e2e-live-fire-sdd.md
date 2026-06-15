# Project Sentinel v3 E2E Live-Fire Drill SDD Addendum

Date: 2026-06-15
Status: Draft for red-line specification review
Owner: TZ
Baseline commit: `984ea31`
Parent SDD:
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-14-project-sentinel-v3-design.md`
- `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-16-project-sentinel-v3-capturer-design.md`
Implementation root: `/Users/tristanzh/agent/Git-Scout`

## 1. Objective

E2E Live-Fire Drill is the final production-readiness rehearsal for Project Sentinel v3. It must validate the complete Sentinel chain with realistic repository fixtures:

```text
fixture repo -> Blind Scout -> Capturer -> Headless Gatekeeper -> Hardcore Auditor -> audit_report.md
```

The purpose is not to prove that GitHub, image CDNs, or paid model APIs are available today. The purpose is to prove that Sentinel can process representative real-world repo shapes without corrupting production dashboard state, exceeding token budget, hanging on bad media, or requiring TZ to manually click through the web UI during automated validation.

## 2. Non-Goals

- Do not call live GitHub APIs in deterministic E2E tests.
- Do not download public internet media during E2E tests.
- Do not call real paid strong-reasoning models by default.
- Do not write E2E outputs into `/Users/tristanzh/agent/Git-Scout/data/scout_pipeline.json`.
- Do not mutate the live Agent07 preview data mounted at `http://127.0.0.1:3017/agent07`.
- Do not require an open browser or manual TZ click for automated E2E.
- Do not treat E2E as a replacement for existing unit tests.

## 3. Entry Criteria

E2E implementation may start only when all are true:

- Baseline commit is at or after `984ea31`.
- `cd /Users/tristanzh/agent/Git-Scout && npm test` passes with `18/18`.
- All E2E inputs are local fixtures under `/Users/tristanzh/agent/Git-Scout/tests/fixtures/repositories/`.
- The E2E runner writes only under `/Users/tristanzh/agent/Git-Scout/storage/e2e_sandbox/`.
- The runner has an explicit fixture token budget and defaults to mock strong-model responses.
- Headless Gatekeeper Emulator exists as an injected boundary, not a browser automation dependency.

## 4. Fixture Repository Set

The first E2E suite must use exactly three fixture repos:

| Fixture | Purpose | Required Contents |
| --- | --- | --- |
| `relative-layout-engine` | Positive sample: real layout architecture | `README.md`, `src/layout.ts`, `src/export.ts`, at least one local image artifact |
| `prompt-positioning-wrapper` | Negative sample: prompt guessed coordinates | `README.md`, `src/index.ts`, sample prompt code, weak or fake artifact |
| `broken-media-repo` | Destructive sample: 404/bad PDF/oversized media references | `README.md`, corrupt local PDF fixture, missing image URL fixture, oversized README fragment |

Required fixture layout:

```text
/Users/tristanzh/agent/Git-Scout/tests/fixtures/repositories/
  relative-layout-engine/
    README.md
    src/layout.ts
    src/export.ts
    artifacts/sample-slide.svg
    fixture-manifest.json
  prompt-positioning-wrapper/
    README.md
    src/index.ts
    artifacts/prompt-output.svg
    fixture-manifest.json
  broken-media-repo/
    README.md
    artifacts/corrupt-sample.pdf
    artifacts/oversized-placeholder.bin
    fixture-manifest.json
```

Fixture manifest contract:

```json
{
  "fixture_id": "relative-layout-engine",
  "repo": "fixture/relative-layout-engine",
  "category": "advanced_ppt",
  "expected_gate_decision": "approve",
  "expected_audit_verdict": "REAL_LAYOUT_ENGINE",
  "readme_path": "README.md",
  "source_files": ["src/layout.ts", "src/export.ts"],
  "artifact_sources": [
    {
      "kind": "image",
      "url": "fixture://relative-layout-engine/artifacts/sample-slide.svg",
      "path": "artifacts/sample-slide.svg"
    }
  ]
}
```

## 5. Static Fixture Boundary

All E2E external boundaries must be routed through fixture adapters.

Allowed fixture protocols:

```text
fixture://<fixture_id>/<relative_path>
```

Forbidden in deterministic E2E tests:

```text
https://api.github.com/
https://raw.githubusercontent.com/
https://github.com/
http://
https://
```

Network client contract:

```ts
type FixtureRepositoryClient = {
  fetchCandidates(): Promise<FixtureCandidate[]>;
  readReadme(repo: string): Promise<string>;
  readSourceFiles(repo: string, paths: string[]): Promise<Array<{ path: string; content: string }>>;
  readArtifact(sourceUrl: string): Promise<{ bytes: Uint8Array; mimeType: string }>;
};
```

Any attempt to use a non-fixture URL in deterministic E2E must fail terminally with:

```text
LIVE_NETWORK_FORBIDDEN_IN_E2E
```

## 6. E2E Sandbox Isolation

All generated files must live under:

```text
/Users/tristanzh/agent/Git-Scout/storage/e2e_sandbox/<run_id>/
```

Required generated layout:

```text
storage/e2e_sandbox/
  fixture_run_20260615T090000Z/
    scout_pipeline.json
    artifacts/
    reports/
    audit_wakeup.jsonl
    e2e_result.json
```

Rules:

- Every E2E run id must start with `fixture_run_`.
- Every candidate written by the E2E runner must include `run_label: "[FIXTURE_RUN]"`.
- Every generated `audit_report.md` must include `[FIXTURE_RUN]` in the header.
- The live dashboard file `/Users/tristanzh/agent/Git-Scout/data/scout_pipeline.json` is read-only during E2E.
- The committed demo artifacts under `/Users/tristanzh/agent/Git-Scout/artifacts/demo/` are read-only during E2E.
- E2E cleanup may delete only the selected `storage/e2e_sandbox/<run_id>/` directory.

## 7. Token Budget Safeguard

E2E runs must use a separate fixture budget ledger:

```json
{
  "run_id": "fixture_run_20260615T090000Z",
  "budget_kind": "fixture_e2e",
  "max_strong_model_calls": 0,
  "max_estimated_input_tokens": 12000,
  "max_estimated_output_tokens": 2000,
  "allow_real_model": false
}
```

Default behavior:

- `allow_real_model = false`.
- Strong model client is a deterministic fixture model returning known audit payloads.
- If a real model is explicitly enabled later, that must require a separate SDD amendment and an environment flag that cannot be true by default.

Pre-flight requirements:

- E2E must run the same local token estimator path used by the production auditor.
- If estimated input tokens exceed fixture budget, E2E must stop before model invocation with:

```text
FIXTURE_TOKEN_BUDGET_EXCEEDED
```

## 8. Headless Gatekeeper Emulator

The emulator replaces manual TZ clicks in automated E2E.

Contract:

```ts
type HeadlessGatekeeperDecision = {
  repo: string;
  decision: "approve" | "reject";
  reason: string;
};

type HeadlessGatekeeper = {
  decide(leads: Array<{ repo: string; title: string; artifacts: unknown }>): Promise<HeadlessGatekeeperDecision[]>;
};
```

Rules:

- The emulator must be deterministic and driven by `fixture-manifest.json`.
- It may call the same dashboard controller functions used by Agent07, or a local controller adapter with identical state mutation semantics.
- It must simulate:
  - approve positive fixture
  - reject negative fixture or broken fixture when manifest demands reject
  - no-op for candidates not selected
- The emulator must never use browser automation to click the UI.

Required decision outcomes for the first E2E suite:

```text
fixture/relative-layout-engine -> approve
fixture/prompt-positioning-wrapper -> approve or reject depending test scenario
fixture/broken-media-repo -> reject or fallback-only scenario
```

## 9. Pipeline Flow

The E2E runner must execute the following deterministic phases:

1. Create `storage/e2e_sandbox/<run_id>/`.
2. Load fixture manifests.
3. Build fixture candidates.
4. Run Blind Scout queue builder with fixture source client.
5. Write sandbox `scout_pipeline.json`.
6. Run Artifact Capturer against fixture artifact sources.
7. Run Headless Gatekeeper Emulator.
8. For approved candidates, run Hardcore Auditor with fixture repository source and fixture strong-model response.
9. Write sandbox `reports/<repo_key>/audit_report.md`.
10. Write `e2e_result.json`.

No phase may write to live Agent07 data.

## 10. E2E Result Contract

`e2e_result.json`:

```json
{
  "version": 1,
  "run_id": "fixture_run_20260615T090000Z",
  "label": "[FIXTURE_RUN]",
  "status": "PASSED",
  "started_at": "2026-06-15T09:00:00Z",
  "completed_at": "2026-06-15T09:00:03Z",
  "pipeline_path": "storage/e2e_sandbox/fixture_run_20260615T090000Z/scout_pipeline.json",
  "checks": [
    {
      "name": "fixture candidates selected",
      "status": "PASSED"
    }
  ],
  "outputs": {
    "artifact_count": 3,
    "audit_reports": [
      "storage/e2e_sandbox/fixture_run_20260615T090000Z/reports/fixture_relative-layout-engine/audit_report.md"
    ]
  }
}
```

Allowed status values:

```text
PASSED
FAILED
BLOCKED_BY_BUDGET
BLOCKED_BY_FIXTURE_CONTRACT
```

## 11. Failure Semantics

E2E must fail fast on contract violations:

- Missing fixture manifest.
- Live network URL used in deterministic mode.
- E2E output path outside `storage/e2e_sandbox/`.
- Missing `[FIXTURE_RUN]` label in generated report.
- Strong model client invoked when `allow_real_model = false`.
- Token estimate exceeds fixture budget.

E2E must not fail the whole run for expected fixture media failures:

- Broken image or corrupt PDF in `broken-media-repo` should result in fallback path and recorded error.
- Rejected fixture repo should trigger cleanup and no audit report.

## 12. TDD Matrix

The next implementation step must create Red tests before any E2E runner code.

| Test | Fixture Setup | Required Assertion |
| --- | --- | --- |
| Static fixture source blocks live network | Candidate source includes `https://api.github.com/repos/x/y` | E2E fails with `LIVE_NETWORK_FORBIDDEN_IN_E2E`; no network mock is called |
| Sandbox isolation | Run E2E with `run_id = fixture_run_test` | All outputs are under `storage/e2e_sandbox/fixture_run_test/`; live `data/scout_pipeline.json` unchanged |
| Token safeguard | Fixture model budget sets `max_strong_model_calls = 0` | Real model client is not called; fixture model response is used |
| Headless approve flow | `relative-layout-engine` manifest says approve | Candidate transitions to `AUDITING` then `COMPLETED`; report is created |
| Headless reject flow | `broken-media-repo` manifest says reject | Repo enters blacklist; artifact directory is cleaned or absent; no audit report created |
| Capturer fallback integration | `broken-media-repo` has corrupt PDF and missing image | `artifacts.local_thumb_path` points to fallback; errors include `REMOTE_404` or `DECODE_FAILED` |
| Auditor verdict integration | fixture model returns `REAL_LAYOUT_ENGINE` | `audit_report.md` and JSON `audit_report.verdict` match expected verdict |
| Fixture run label | Full E2E completes | `scout_pipeline.json`, `audit_report.md`, and `e2e_result.json` contain `[FIXTURE_RUN]` |
| Reproducibility | Run the same fixture suite twice with fixed clock | Deterministic fields match except allowed run directory name |

## 13. Proposed Files for TDD Red Phase

```text
/Users/tristanzh/agent/Git-Scout/tests/sentinel/e2eLiveFire.test.ts
/Users/tristanzh/agent/Git-Scout/src/sentinel/e2eLiveFire.ts
/Users/tristanzh/agent/Git-Scout/tests/fixtures/repositories/relative-layout-engine/
/Users/tristanzh/agent/Git-Scout/tests/fixtures/repositories/prompt-positioning-wrapper/
/Users/tristanzh/agent/Git-Scout/tests/fixtures/repositories/broken-media-repo/
```

The first Red commit must include:

- fixture manifests
- minimal fixture README/source/artifact files
- E2E runner interface stubs
- Red tests proving the runner is not implemented yet

No Green implementation may be written until the Red tests fail for the expected missing-implementation reason.

## 14. Approval Gate

This addendum authorizes SDD review only. The next step is a TDD Red commit for fixture files, E2E runner interface stubs, and offline E2E tests.

Business implementation must not start until that Red commit has been reviewed.
