# Project Sentinel v3 Agent07 Runtime Reject Mutation SDD

Date: 2026-06-18
Stage: Agent07 runtime decision consistency hotfix
Scope: feature-required Agent07 project delta only

## Problem

Agent07 now renders the right decision surface from the latest runtime shadow scout result when available. Approve already materializes a runtime-only candidate into the production Sentinel JSON before mutating it. Reject still searches only `Git-Scout/data/scout_pipeline.json`.

This creates a split-brain decision path: the user can see a runtime shadow candidate in Scout Stream, but clicking `流放` posts a repo that does not exist in the production lead array, causing `Agent07 lead not found`.

## Contract

`POST /api/agent07/reject` must support the same visible candidate universe as `GET /api/agent07/status`.

For a repo present in runtime shadow and absent from production JSON:

1. Resolve the runtime capability evidence from `/runtime_shadow`.
2. Require `evidence_state === "READY"` before mutation.
3. Materialize the runtime lead into the locked production state.
4. Remove that repo from `leads`.
5. Persist the repo to `blacklist.repos`.
6. Persist the author to `blacklist.authors` unless `banAuthor === false`.
7. Return the same runtime display payload shape as status and approve.

For a repo absent from both production and READY runtime evidence, keep returning `404`.

## Runtime Display Filtering

Runtime shadow is an evidence source, not an override that may bypass user decisions. `agent07DisplayPayloadForPath` must filter runtime leads against persisted `blacklist.repos` before rendering.

If the filtered runtime list drops below the target top-five count, the response must expose that honestly through the existing recall contract, for example `PARTIAL_RECALL` with `displayed_count < 5`. The hotfix does not invent backfill candidates.

## Concurrency

Reject must run under the existing Agent07 file lock. Runtime materialization, blacklist mutation, and atomic write are one critical section so approve/reject clicks cannot race into divergent JSON state.

## Acceptance Tests

Add a service-level regression test:

- boot a production pipeline that does not contain `real/skill-engine`;
- boot runtime shadow evidence that does contain READY `real/skill-engine`;
- verify status displays `real/skill-engine` from `runtime_shadow`;
- post `/api/agent07/reject` for `real/skill-engine`;
- assert 200 response, repo removed from displayed leads, repo and author persisted in blacklist;
- fetch status again and assert the rejected runtime repo is still hidden.

Existing production reject behavior and approve runtime materialization must continue passing.

## Git Guard

The root workspace contains unrelated dirty changes. Stage only this SDD in the root repository. Implementation and tests belong to the isolated Web QA worktree and must stage only:

- `server.mjs`
- `tests/agent07-service.test.mjs`

