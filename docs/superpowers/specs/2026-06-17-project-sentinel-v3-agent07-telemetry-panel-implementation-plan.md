# Project Sentinel v3 Agent07 Telemetry Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Agent07-only Runtime telemetry panel that lazily fetches sanitized shadow evidence, renders bounded category rows and tags, and never leaks host paths or tokens.

**Architecture:** The Agent07 right rail gains an in-place Decision/Runtime segmented view; telemetry fetch happens only after Runtime selection; the Web facade may extend `/api/agent07/runtime/shadow` with compact sanitized DTO rows. Red tests live in the separate Web repository because `/Users/tristanzh/agent/web` is an ignored nested Git workspace.

**Tech Stack:** Node.js `node:test`, local `createAppServer`, static Agent07 JavaScript/CSS, no new runtime dependencies.

---

## Specification Inputs

- SDD: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-sdd.md`
- SDD commit: `a76a549`
- Stage 10.2 Web commits:
  - `2462bbe`
  - `d71f81e`

## Repository Boundary

`/Users/tristanzh/agent/web` has its own `.git` directory and is ignored by the root repository. Stage 10.3 uses two precise commits:

1. Root repository commit for this implementation plan.
2. Web repository commit for `tests/agent07-telemetry-panel.test.mjs`.

Do not try to commit `web/tests/agent07-telemetry-panel.test.mjs` from `/Users/tristanzh/agent`; root `.gitignore` excludes `web/`.

## File Map

- Create: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-implementation-plan.md`
  - Purpose: implementation plan, Red-Green contract, pagination guard, and dirty-workspace staging policy.
- Create: `/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs`
  - Purpose: Red tests for lazy Runtime fetch, telemetry tag rendering, path/token sanitization, row cap, and legacy isolation.
- Later modify: `/Users/tristanzh/agent/web/server.mjs`
  - Purpose: extend `/api/agent07/runtime/shadow` to return compact sanitized telemetry DTO rows without raw evidence.
- Later modify: `/Users/tristanzh/agent/web/app/agent07.js`
  - Purpose: add Decision/Runtime switching, lazy fetch, final browser sanitizer, bounded renderer, and legacy-safe state handling.
- Later modify: `/Users/tristanzh/agent/web/app/agent07.css`
  - Purpose: add `.agent07-telemetry-*` tokenized styles and a bounded scroll region.

## Task 1: Commit Plan Document in Root Repository

**Files:**
- Create: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-implementation-plan.md`

- [ ] **Step 1: Verify the plan file exists**

Run:

```bash
cd /Users/tristanzh/agent
test -f docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-implementation-plan.md
```

Expected: exit code `0`.

- [ ] **Step 2: Stage only the plan file**

Run:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-implementation-plan.md
git diff --cached --name-only
```

Expected staged list includes the plan file. Existing Passenger-Vehicle-Intel entries may already be staged, so the commit command in Step 3 must use a pathspec.

- [ ] **Step 3: Commit only the plan file**

Run:

```bash
cd /Users/tristanzh/agent
git commit docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-implementation-plan.md \
  -m "docs(sentinel): 编写 Stage 10.3 Agent07 影子证据遥测面板实施计划"
```

Expected: one root commit containing only the plan file.

## Task 2: Write Telemetry Panel Red Tests

**Files:**
- Create: `/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs`

- [ ] **Step 1: Add fixture builders**

The test file must create:

```js
function makeTelemetryPayload({ lowQualityCount = 39 } = {}) {
  return {
    version: 1,
    run_id: "runtime_20260617T010000Z",
    generated_at: "2026-06-17T01:00:00.000Z",
    low_quality_filtered_count: lowQualityCount,
    low_relevance_overflow_count: 2,
    readme_skip_count: 1,
    query_timeout_skipped_count: 1,
    categories: {
      low_quality_filtered: [...],
      low_relevance_overflow: [...],
      readme_skipped: [...],
      query_timeout_skipped: [...],
    },
  };
}
```

The fixture must include unsafe strings:

```text
/Users/tristanzh/agent/storage/private
/private/tmp/sentinel
ghp_secret_token_must_not_leak
github_pat_secret_must_not_leak
Authorization: Bearer secret
sk-secret
```

- [ ] **Step 2: Add lazy-load Red test**

Test behavior:

```js
const harness = await loadAgent07TelemetryHarness({ telemetryPayload: makeTelemetryPayload() });
assert.equal(harness.shadowCalls.length, 0);
await harness.runtimeTab.click();
assert.equal(harness.shadowCalls.length, 1);
```

Expected Red before implementation: `runtimeTab` is missing because no telemetry tab exists.

- [ ] **Step 3: Add tag and count Red test**

Test behavior:

```js
await harness.runtimeTab.click();
assert.match(harness.telemetryPanelText(), /39/);
assert.match(harness.telemetryPanelText(), /2/);
assert.match(harness.telemetryPanelText(), /\\[ZIP_DETECTOR\\]/);
assert.match(harness.telemetryPanelText(), /Score: 20 \\| Matched: \\+50 -30/);
assert.match(harness.telemetryPanelText(), /\\[403_RATE_LIMIT\\]/);
assert.match(harness.telemetryPanelText(), /\\[8s_TIMEOUT\\]/);
```

Expected Red before implementation: no panel text is rendered.

- [ ] **Step 4: Add path and token sanitization Red test**

Test behavior:

```js
await harness.runtimeTab.click();
const text = harness.telemetryPanelText();
assert.match(text, /shadow:\\/\\//);
assert.doesNotMatch(text, /\\/Users\\//);
assert.doesNotMatch(text, /\\/private\\//);
assert.doesNotMatch(text, /ghp_|github_pat_|Authorization:|sk-/);
```

Expected Red before implementation: no runtime tab exists or no sanitized telemetry is rendered.

- [ ] **Step 5: Add bounded rendering Red test**

Test behavior:

```js
const payload = makeTelemetryPayload({ lowQualityCount: 240 });
await harness.runtimeTab.click();
assert.ok(harness.renderDurationMs < 100);
assert.ok(harness.telemetryRows().length <= 30);
assert.match(harness.telemetryPanelText(), /210 remaining|210 hidden|210 folded|其余 210/);
```

Expected Red before implementation: no telemetry rows exist and no row-cap message is rendered.

- [ ] **Step 6: Add legacy isolation Red test**

Test behavior:

```js
assert.equal(Boolean(harness.approveButton), true);
assert.equal(Boolean(harness.rejectButton), true);
assert.equal(Boolean(harness.runtimeTrigger), true);
assert.equal(harness.approveButton.disabled, false);
assert.equal(harness.rejectButton.disabled, false);
```

The test protects Stage 10.2 and approve/reject controls while adding the Runtime segment.

- [ ] **Step 7: Run Red test**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-telemetry-panel.test.mjs
```

Expected: FAIL. The failure must point to missing Runtime tab/panel behavior, not syntax errors.

## Task 3: Verify Existing Web Tests Are Still Stable

**Files:**
- Read only: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`
- Read only: `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`

- [ ] **Step 1: Run Stage 10.2 UI tests**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-ui-dom.test.mjs
```

Expected: PASS.

- [ ] **Step 2: Run Agent07 service tests**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-service.test.mjs
```

Expected: PASS if the existing dirty workspace remains internally consistent. If it fails because of pre-existing local edits, record the exact output and do not modify unrelated files.

## Task 4: Commit Web Red Tests

**Files:**
- Create: `/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs`

- [ ] **Step 1: Inspect Web status**

Run:

```bash
cd /Users/tristanzh/agent/web
git status --short tests/agent07-telemetry-panel.test.mjs app/agent07.js app/agent07.css server.mjs tests/agent07-service.test.mjs
```

Expected before staging:

```text
?? tests/agent07-telemetry-panel.test.mjs
```

Existing unrelated modifications may appear. They must not be staged.

- [ ] **Step 2: Stage only telemetry Red test**

Run:

```bash
cd /Users/tristanzh/agent/web
git add tests/agent07-telemetry-panel.test.mjs
git diff --cached --name-only
```

Expected:

```text
tests/agent07-telemetry-panel.test.mjs
```

- [ ] **Step 3: Commit Web Red test**

Run:

```bash
cd /Users/tristanzh/agent/web
git commit -m "test(sentinel): 编写 Stage 10.3 影子证据与日志遥测面板分类打分、路径脱敏 TDD 集成测试"
```

Expected: one Web repo commit with only `tests/agent07-telemetry-panel.test.mjs`.

## Task 5: Later Green Implementation

**Files:**
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Modify: `/Users/tristanzh/agent/web/app/agent07.js`
- Modify: `/Users/tristanzh/agent/web/app/agent07.css`
- Test: `/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs`
- Test: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`
- Test: `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`

- [ ] **Step 1: Extend server DTO only with compact rows**

Extend `/api/agent07/runtime/shadow` with `categories` arrays. Drop raw evidence fields and sanitize paths/tokens before response.

- [ ] **Step 2: Add right-rail segmented view**

Add Decision/Runtime tabs under Agent07 right rail. Runtime panel starts hidden and empty.

- [ ] **Step 3: Add lazy fetch and browser sanitizer**

When Runtime tab is clicked, fetch `/api/agent07/runtime/shadow`, sanitize all displayed strings again, and render with `textContent`.

- [ ] **Step 4: Add row cap**

Render at most 30 evidence rows. Show a folded summary such as `其余 210 条已折叠` when the payload contains more than 30 rows.

- [ ] **Step 5: Verify Green**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-telemetry-panel.test.mjs
node --test tests/agent07-ui-dom.test.mjs
node --test tests/agent07-service.test.mjs

cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npm test
```

Expected after Green: Stage 10.3, Stage 10.2, Agent07 service, Git-Scout typecheck, and Git-Scout tests pass.

## Self-Review

- Spec coverage: lazy load, tags, sanitization, row cap, and legacy isolation are each mapped to test tasks.
- Placeholder scan: this plan contains no open placeholders.
- Type and selector consistency: selectors match the approved SDD: `data-agent07-telemetry-tab`, `data-agent07-telemetry-panel`, and `.agent07-telemetry-*`.
