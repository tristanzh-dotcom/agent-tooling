# Global AGENTS.md - TZ Codex Project Rules

Scope: all Codex-managed projects under `/Users/tristanzh/agent` on this computer.

---

## User Preference

In natural daily replies, call the user `TZ` when context allows.

Use first-principles problem solving. Keep communication direct, practical, and evidence-based. Avoid boilerplate, vague reassurance, and unsupported claims.

---

## Cross-Account Memory Rule

Codex account switching must not break project continuity.

Shift to first principles: maintain centralized, high-density handover files rather than fragmenting project state across redundant logs, to minimize context bloat.

If a local handover file conflicts with prior model memory, assumptions, or historical session impressions, follow the local handover file.

---

## Required Start Routine

When starting ordinary work in any project under `/Users/tristanzh/agent`, follow this routine.

If TZ explicitly asks to read or resume from a `HANDOVER_*.md` file, do **not** execute this ordinary Start Routine first. Instead, immediately follow the **Required Boot/Resume Routine** below.

For ordinary starts:

1. Read `/Users/tristanzh/agent/GLOBAL_MODEL_ROUTING_RECORD.md` before making assumptions about model routing, privacy boundaries, or LLM responsibilities.
2. Check for project-local `AGENTS.md`.
3. Read the current authoritative context file before making assumptions.
4. If no durable context exists, ask TZ which source should be treated as authoritative before creating new project memory.

Do not create or mutate project memory unless the applicable workflow explicitly authorizes it.

---

## Development Workflow

For non-trivial implementation work, follow this sequence:

1. Confirm interface design and expected behavior (SDD).
2. Define acceptance criteria.
3. Generate or update tests (TDD).
4. Implement the smallest correct business logic.
5. Run relevant verification.
6. Report results with evidence.

Do not directly generate business code that lacks design, acceptance criteria, or a test/verification path.

Small changes may be executed quickly, but must still include:

* affected scope
* verification method or verification result
* any unresolved risk

Use relevant Skills when they materially improve correctness, verification quality, or handoff quality. Do not invoke Skills merely for formality.

Relevant Skill guidance:

* `brainstorming` for creative/product/design changes
* `writing-plans` for multi-step implementation
* `test-driven-development` for feature or bugfix code
* `receiving-code-review` for TZ feedback
* `verification-before-completion` before claiming completion

Before claiming completion, provide verification evidence. If tests cannot be run, explain why and provide a manual verification path.

---

## Required End Routine

When TZ asks for handoff, closing, end-of-day, “今日收工”, or similar closing intents:

1. Immediately read and strictly execute `/Users/tristanzh/agent/.ai_skills/handover_skill.md`.
2. Confirm the authoritative project root before scanning or writing.
3. Apply the dual-track evidence chain:

   * Git/file evidence for code changes.
   * User-confirmed dialogue evidence for design decisions.
4. Do not invent completed work, test results, decisions, or unresolved risks.
5. Do not update any memory, changelog, historical handoff, or other project file unless TZ explicitly asks.
6. In the handover document, identify the current development stage:

   * SDD
   * TDD
   * business logic
   * verification
   * handoff/closing

The detailed handover file format and write rules are owned by `/Users/tristanzh/agent/.ai_skills/handover_skill.md`. Do not duplicate that SOP here.

---

## Required Boot/Resume Routine

When a new session starts and TZ asks to read or resume from a `HANDOVER_*.md` file:

1. Treat the local handover file text as the authoritative source for this restart.
2. If the handover file conflicts with prior model memory, assumptions, or historical session impressions, follow the handover file.
3. The first line of the response must be exactly the Markdown H1 title requested by the Boot Prompt in the handover file. Do not prepend greetings, acknowledgements, or boilerplate.
4. Do not summarize the full file. Extract only:

   * core bottleneck
   * current development stage
   * automized next actions
   * uncertainty or confirmation needed from TZ
5. End the response with: `『请 TZ 确认：是按计划执行，还是需要进行微调？』`
6. Then stop. Do not modify files, run commands, propose new solutions, expand task scope, or continue implementation until TZ explicitly authorizes.

---

## Highest Web Publishing Boundary Rule

This is the highest rule for all Codex-managed project work that touches the shared web publishing service.

* Domain/project workflows own business capability, data flow, API contracts, report schemas, and the minimum UI changes needed to make the feature usable and testable.
* The web publishing workflow owns visual system governance: layout paradigms, CSS standards, spacing, visual polish, cross-agent consistency, and publication-level style rules.
* If a domain/project workflow must change a page to complete a feature, the change must be scoped to the relevant route, selectors, CSS file, data attributes, tests, and documentation. It must not alter unrelated agents or shared paradigms by default.
* If a web publishing workflow later edits the same shared web files, it inherits all committed/actual changes made by the domain/project workflow in `/Users/tristanzh/agent/web`.
* `/Users/tristanzh/agent/web` is the shared visible publishing surface. Any change made there is part of the base inherited by future web publishing work unless it is explicitly reverted.
* Project directories outside `/Users/tristanzh/agent/web`, such as `/Users/tristanzh/agent/PetRelatedServices`, are durable business/data/documentation roots. They do not become visible web output until explicitly wired into `/Users/tristanzh/agent/web` or another publishing surface.
* PetRelatedServices intentionally does not expose root `AGENTS.md`; for Agent03/Pet publishing boundary, read `/Users/tristanzh/agent/PetRelatedServices/docs/web-platform-boundary-notice.md`.
* Before any HTML/CSS/layout edit, classify the change as either a feature-required project delta or a web publishing paradigm/style change. If unclear, ask TZ before editing.
* Tests must prove both the intended feature and that unrelated agents did not inherit layout or style changes accidentally.

---

## Data and Reporting Work

For research, reporting, or data products:

* Use source-backed data.
* Record source URLs and confidence.
* Mark uncertain data clearly instead of hiding uncertainty.
* Keep reproducible artifacts in project directories.
