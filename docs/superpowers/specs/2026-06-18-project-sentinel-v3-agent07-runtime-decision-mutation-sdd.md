# Project Sentinel v3 Agent07 Runtime Decision Mutation SDD

## Scope

Agent07 now displays Top5 candidates from `runtime_shadow`, while Approve/Reject originally mutate only the production `scout_pipeline.json`. This creates a split-brain state: the page can show a runtime candidate that the mutation endpoint cannot find, causing `Agent07 lead not found`.

This fix is scoped to Agent07 decision mutation APIs and display overlay logic. It must not publish runtime shadow data externally, weaken the shadow-only runtime gate, or alter unrelated agents.

## Contract

- `POST /api/agent07/approve` must accept a repo currently visible from runtime shadow.
- If the repo does not exist in production pipeline but has READY runtime evidence, the server must materialize a normalized local lead from runtime evidence before applying the approval mutation.
- Approved runtime leads must persist in local `scout_pipeline.json` as `APPROVED`, `AUDITING`, and `locked`.
- The response and future `/api/agent07/status` calls must preserve the runtime Top5 display while overlaying persisted decision state by repo.
- Existing production-pipeline approve behavior must remain unchanged.
- Missing repos with no production or runtime evidence must still return 404.

## TDD Matrix

- Runtime approve API test: approving a runtime-only repo returns 200, wakes auditor, and marks that visible repo as `APPROVED/AUDITING/locked`.
- Refresh persistence test: after approving a runtime-only repo, `/api/agent07/status` still uses `runtime_shadow` but overlays the approved state instead of resetting to `PENDING`.
- Existing production approve/reject tests remain green.

## Git Guard

Commit only this SDD and Agent07 web QA implementation/tests. Do not commit `Git-Scout/storage/` runtime outputs or unrelated dirty files.
