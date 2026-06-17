# Project Sentinel v3 Agent07 Integration Decision Evidence SDD

## Scope

Agent07's business goal is to identify external skills that can be absorbed into the local PPT/document production system. A candidate is not useful merely because it is a GitHub repo or because its README contains presentation keywords.

The page must answer, for the currently selected Scout Stream candidate:

- what concrete production capability it may add;
- how it could integrate into the local PPT skill/toolchain;
- whether it deserves deep review now;
- which risks should block or downgrade approval.

This is a feature-required Agent07 delta. It is scoped to Agent07 capability API, Agent07 DOM rendering, CSS/tests if needed, and must not alter unrelated agents or shared web theme rules.

## API Contract

`GET /api/agent07/capability?repo=...` must include a `decision_evidence` object for READY runtime evidence:

- `capability_type`: concise user-facing type, e.g. `Editable PPTX skill`, `PPT generation pipeline`, `Office document generator`, or `Generic presentation surface`.
- `integration_path`: how the candidate could enter TZ's local system, e.g. `Package as local Codex skill`, `Merge into PPT-maker generation chain`, `Use as conversion sidecar`, or `Evidence insufficient`.
- `deep_review_recommendation`: one of `PRIORITIZE_DEEP_REVIEW`, `REVIEW_WITH_RISKS`, `DEFER`, `REJECT`.
- `decision_summary`: one sentence explaining why approve/defer/reject is rational.
- `risk_summary`: concise visible risk text derived from fit risk codes and artifact status.

For missing runtime evidence, `decision_evidence.deep_review_recommendation` must be `REJECT` and the summary must state that approval is blocked by missing evidence.

## DOM Contract

Artifacts Theater must render a dedicated integration-decision block with stable selector `data-agent07-integration-evidence`.

The block must update whenever the selected Scout Stream candidate changes. It must be driven by the exact repo capability response, not by demo defaults or a static card.

Minimum visible fields:

- `Capability`
- `Integration`
- `Recommendation`
- `Risk`

The existing README-derived capability facts may remain, but they are supporting detail. The integration-decision block is the primary answer to "should TZ deep review this skill?"

## TDD Matrix

- Service API test: exact repo capability response includes `decision_evidence` with capability type, integration path, recommendation, and risk summary.
- UI DOM test: selected runtime candidate renders the integration-decision text and updates it from `/api/agent07/capability`.
- Regression test: missing/demo-only repo renders `REJECT` or equivalent evidence-insufficient guidance.
- Existing Agent07 tests must remain green.

## Git Guard

Commit only this SDD and Agent07 web QA implementation/tests. Do not commit `Git-Scout/storage/` runtime outputs or unrelated dirty root files.
