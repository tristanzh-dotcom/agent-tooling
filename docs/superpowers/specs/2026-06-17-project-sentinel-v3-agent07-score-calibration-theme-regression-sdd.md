# Project Sentinel v3 Agent07 Score Calibration and Theme Regression SDD

## Scope

This is a corrective design for two production-readiness regressions in Agent07:

1. `Project Fit` currently saturates to `100/100` for all five visible runtime candidates, preventing a user from deciding which candidate deserves deeper review first.
2. The Agent07 page shell hard-codes a black visual theme, overriding the shared web publishing theme tokens and regressing the previously restored light publishing style.

The change is limited to Agent07 scoring, Agent07 route styling, and their tests. It must not alter unrelated agents or shared theme definitions.

## Score Contract

User-visible scoring has exactly one primary scale: `Project Fit Score`, an integer from `0` to `100`.

Interpretation:

- `90-100`: strong fit, prioritize deep review.
- `70-89`: viable fit, review risks before approval.
- `50-69`: marginal fit, only continue with a specific reason.
- `<50`: poor fit, default to reject/defer.

The score must not be a direct clamp of an unbounded internal promotion score. It must be calibrated from first-principles factors:

- direct PPT/PPTX generation capability;
- editable output evidence;
- template/layout control;
- Codex/Claude skill reuse surface;
- local automation surface;
- evidence confidence;
- negative caps for side-path PDF conversion, static/image-only conversion, viewer-only tools, generic collections, and broad agent platforms.

The visible Top5 must not all return `100/100` unless the underlying evidence is genuinely identical across all major factors, which current runtime evidence is not.

Runtime shadow output must persist the same score contract on every visible lead. `scout_pipeline.shadow.json` must not degrade to captured-only shells; each lead must carry `token_roi_estimate`, `roi_label`, `source_kind`, and `capability.project_fit` so the web layer can render decision evidence without recomputing or guessing score semantics.

## Theme Contract

Agent07 CSS must inherit from the shared Web theme token contract. The page shell, panels, cards, text, borders, and actions must use tokens such as `var(--web-bg)`, `var(--web-surface)`, `var(--web-text-main)`, `var(--web-border-soft)`, and `var(--web-action-primary)`.

Hard-coded black/white/gray values are forbidden in Agent07 route CSS for normal page surfaces and text. The route must render correctly under `data-web-theme="light-tech"` and must not force a black dashboard.

## TDD Matrix

- Project Fit calibration test: representative current Top5 candidates must produce differentiated scores, ordered by business fit rather than all clamped to `100`.
- Runtime orchestrator test: shadow pipeline leads must persist `Project Fit x/100` and bounded project-fit capability details instead of captured-only records.
- Runtime adapter test: user-visible runtime candidate score fields must remain within `0-100`.
- Web service test: runtime status must expose only `Project Fit x/100` labels and clamped score fields.
- Agent07 UI/theme test: `app/agent07.css` must not contain hard-coded black/white/gray literals and must include shared theme tokens for page shell surfaces and text.

## Git Guard

Commit only:

- `Git-Scout/src/sentinel/projectFitScorer.ts`
- `Git-Scout/src/sentinel/runtimeOrchestrator.ts`
- relevant Git-Scout tests
- `web` QA worktree Agent07 CSS/server/tests
- this SDD

Do not commit `Git-Scout/storage/` live shadow output or unrelated dirty files.
