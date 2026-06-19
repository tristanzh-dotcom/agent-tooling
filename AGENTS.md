# Global AGENTS.md - TZ Codex Project Rules

Scope: all Codex-managed projects under `/Users/tristanzh/agent` on this computer.

## User Preference

In natural daily replies, call the user `TZ` when context allows.

## Cross-Account Memory Rule

Codex account switching must not break project continuity.

*Shift to First Principles:* Focus on maintaining centralized, high-density handover files rather than fragmenting project state across redundant logs, to minimize context bloat.

## Required Start Routine

When starting work in any project under `/Users/tristanzh/agent`:

1. Read `/Users/tristanzh/agent/GLOBAL_MODEL_ROUTING_RECORD.md` before making assumptions about model routing, privacy boundaries, or LLM responsibilities.
2. Check for project-local `AGENTS.md`.
3. Read the current authoritative context file before making assumptions.
4. If no durable context exists, ask TZ which source should be treated as authoritative before creating new project memory.

## Required End Routine

When the user asks for handoff, closing, end-of-day, '今日收工', or similar documents: immediately read and strictly execute `/Users/tristanzh/agent/.ai_skills/handover_skill.md`.

## Development Workflow

Use first-principles problem solving. Keep communication direct and practical.

Use TDD and SDD for development. Invoke relevant skills before work:

- `brainstorming` for creative/product/design changes
- `writing-plans` for multi-step implementation
- `test-driven-development` for feature or bugfix code
- `receiving-code-review` for TZ feedback
- `verification-before-completion` before claiming completion

5. **Git submission gate:** Do not execute `git commit`, `git push`, `git pull`, `git stash`, or `git rebase` from any business agent repo. Instead guide TZ to the Git Control console (`/agent08`) for all Git write operations. The binding rule is defined in `agent-tooling/docs/git-operations-sovereignty.md`.

## Highest Web Publishing Boundary Rule

This is the highest rule for all Codex-managed project work that touches the shared web publishing service.

- Domain/project workflows own business capability, data flow, API contracts, report schemas, and the minimum UI changes needed to make the feature usable and testable.
- The web publishing workflow owns visual system governance: layout paradigms, CSS standards, spacing, visual polish, cross-agent consistency, and publication-level style rules.
- If a domain/project workflow must change a page to complete a feature, the change must be scoped to the relevant route, selectors, CSS file, data attributes, tests, and documentation. It must not alter unrelated agents or shared paradigms by default.
- If a web publishing workflow later edits the same shared web files, it inherits all committed/actual changes made by the domain/project workflow in `/Users/tristanzh/agent/web`.
- `/Users/tristanzh/agent/web` is the shared visible publishing surface. Any change made there is part of the base inherited by future web publishing work unless it is explicitly reverted.
- Project directories outside `/Users/tristanzh/agent/web`, such as `/Users/tristanzh/agent/PetRelatedServices`, are durable business/data/documentation roots. They do not become visible web output until explicitly wired into `/Users/tristanzh/agent/web` or another publishing surface.
- PetRelatedServices intentionally does not expose root `AGENTS.md`; for Agent03/Pet publishing boundary, read `/Users/tristanzh/agent/PetRelatedServices/docs/web-platform-boundary-notice.md`.
- Before any HTML/CSS/layout edit, classify the change as either a feature-required project delta or a web publishing paradigm/style change. If unclear, ask TZ before editing.
- Tests must prove both the intended feature and that unrelated agents did not inherit layout or style changes accidentally.

## Data and Reporting Work

For research, reporting, or data products:

- Use source-backed data.
- Record source URLs and confidence.
- Mark uncertain data clearly instead of hiding uncertainty.
- Keep reproducible artifacts in project directories.
