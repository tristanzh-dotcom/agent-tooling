# Project Sentinel v3 Agent07 UI Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Agent07-only safe runtime trigger button that disables on the first frame, posts a fixed shadow-probe body, polls runtime status, and recovers from backend faults without locking the UI.

**Architecture:** The server-rendered Agent07 page owns the DOM injection inside `.agent07-actions`; `app/agent07.js` owns the runtime lane state machine independently from approve/reject mutation state; `app/agent07.css` owns only `.agent07-runtime-*` tokenized styling. Red tests live in the separate Web repository because `/Users/tristanzh/agent/web` is a nested ignored Git workspace.

**Tech Stack:** Node.js `node:test`, Web server `server.mjs`, static Agent07 frontend JavaScript/CSS, no new runtime dependencies.

---

## Specification Inputs

- SDD: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-sdd.md`
- Root repo latest approved SDD commit: `9719921`
- Web repo Stage 10.1 baseline commits:
  - `4f612b1`
  - `514ba07`

## Repository Boundary

`/Users/tristanzh/agent/web` is ignored by the root repository and has its own `.git` directory. Stage 10.2 therefore uses two precise commits:

1. Root repository commit for this implementation plan.
2. Web repository commit for `tests/agent07-ui-dom.test.mjs`.

Do not try to stage `web/tests/agent07-ui-dom.test.mjs` from `/Users/tristanzh/agent`; root `.gitignore` excludes `web/`.

## File Map

- Create: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-implementation-plan.md`
  - Purpose: implementation steps, Red-Green contract, and dirty-workspace staging guard.
- Create: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`
  - Purpose: Red tests for Agent07 runtime trigger DOM topology, first-frame disable, fixed POST body, 500 recovery, and approve/reject isolation.
- Later modify: `/Users/tristanzh/agent/web/server.mjs`
  - Purpose: inject runtime trigger button and status line into Agent07 HTML only.
- Later modify: `/Users/tristanzh/agent/web/app/agent07.js`
  - Purpose: runtime lane event handler, fixed trigger request, status polling, 409 busy handling, 500 recovery.
- Later modify: `/Users/tristanzh/agent/web/app/agent07.css`
  - Purpose: `.agent07-runtime-*` tokenized styling only.

## Task 1: Commit Plan Document in Root Repository

**Files:**
- Create: `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-implementation-plan.md`

- [ ] **Step 1: Write the plan file**

Use this document as the implementation plan. It deliberately names exact repos and files because root and Web have separate Git state.

- [ ] **Step 2: Verify root staged file list**

Run:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-implementation-plan.md
git diff --cached --name-only
```

Expected:

```text
docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-implementation-plan.md
```

- [ ] **Step 3: Commit root plan**

Run:

```bash
cd /Users/tristanzh/agent
git commit -m "docs(sentinel): 编写 Stage 10.2 Agent07 前端控制按钮实施计划"
```

Expected: one root commit with only the plan file.

## Task 2: Write Agent07 UI Red Tests

**Files:**
- Create: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`

- [ ] **Step 1: Add DOM topology Red test**

The test must start a local `createAppServer`, load `/agent07`, and assert:

```js
assert.equal(count(actionsHtml, /data-agent07-runtime-trigger/g), 1);
assert.equal(count(actionsHtml, /data-agent07-approve/g), 1);
assert.equal(count(actionsHtml, /data-agent07-reject/g), 1);
assert.equal(count(html, /data-agent07-runtime-status/g), 1);
```

Current expected Red failure before implementation:

```text
0 !== 1
```

- [ ] **Step 2: Add first-frame disable and fixed body Red test**

The test must evaluate `/Users/tristanzh/agent/web/app/agent07.js` in a minimal DOM harness that includes a fake `data-agent07-runtime-trigger` button. Then:

```js
runtimeTrigger.click();
assert.equal(runtimeTrigger.disabled, true);
assert.deepEqual(JSON.parse(runtimeCall.options.body), { mode: "LIVE_NETWORK_SHADOW_PROBE" });
```

Current expected Red failure before implementation:

```text
false !== true
```

- [ ] **Step 3: Add HTTP 500 recovery Red test**

The test must make the runtime trigger request return HTTP 500 and assert:

```js
assert.equal(runtimeTrigger.disabled, false);
assert.match(runtimeStatus.textContent, /异常|重试|失败/);
assert.equal(timerSpy.activeIntervals.size, 0);
assert.ok(timerSpy.clearIntervalCalls.length >= 1);
```

Current expected Red failure before implementation: no runtime trigger request is emitted, no state recovery runs, and no interval cleanup happens.

- [ ] **Step 4: Add approve/reject isolation assertion**

The same DOM harness must click approve and reject buttons and assert they still call their original endpoints:

```js
assert.ok(calls.some((call) => call.url === "/api/agent07/approve"));
assert.ok(calls.some((call) => call.url === "/api/agent07/reject"));
assert.equal(calls.filter((call) => call.url === "/api/agent07/runtime/trigger").length, 0);
```

This protects existing card decision behavior while the runtime trigger is added.

- [ ] **Step 5: Run Red test**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-ui-dom.test.mjs
```

Expected: FAIL. The first failing assertion should point to the missing `data-agent07-runtime-trigger` DOM contract or the missing first-frame disabled behavior.

## Task 3: Verify Existing Agent07 Service Baseline

**Files:**
- Read only: `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`
- Read only: `/Users/tristanzh/agent/web/server.mjs`

- [ ] **Step 1: Run current Agent07 service test**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-service.test.mjs
```

Expected: PASS if the existing dirty workspace is internally consistent. If this fails, record the failure exactly and do not modify unrelated files.

## Task 4: Commit Web Red Tests

**Files:**
- Create: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`

- [ ] **Step 1: Inspect Web status**

Run:

```bash
cd /Users/tristanzh/agent/web
git status --short tests/agent07-ui-dom.test.mjs app/agent07.js app/agent07.css server.mjs
```

Expected before staging:

```text
?? tests/agent07-ui-dom.test.mjs
```

Existing unrelated modifications in `app/agent07.css` or `server.mjs` may appear, but they must not be staged by this task.

- [ ] **Step 2: Stage only the Red test file**

Run:

```bash
cd /Users/tristanzh/agent/web
git add tests/agent07-ui-dom.test.mjs
git diff --cached --name-only
```

Expected:

```text
tests/agent07-ui-dom.test.mjs
```

- [ ] **Step 3: Commit Web Red test**

Run:

```bash
cd /Users/tristanzh/agent/web
git commit -m "test(sentinel): 编写 Stage 10.2 前端按钮置灰、第一帧锁死与异常复位 TDD 集成测试"
```

Expected: one Web repo commit with only `tests/agent07-ui-dom.test.mjs`.

## Task 5: Later Green Implementation

**Files:**
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Modify: `/Users/tristanzh/agent/web/app/agent07.js`
- Modify: `/Users/tristanzh/agent/web/app/agent07.css`
- Test: `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`
- Test: `/Users/tristanzh/agent/web/tests/agent07-service.test.mjs`

- [ ] **Step 1: Inject DOM in Agent07 template**

Add one `data-agent07-runtime-trigger` button under `.agent07-actions` and one `data-agent07-runtime-status` status line after the existing action status line.

- [ ] **Step 2: Implement first-frame runtime state transition**

Before any awaited operation in the click handler:

```js
runtimeTriggerButton.disabled = true;
runtimeTriggerButton.textContent = "拉取启动中";
runtimeStatusLine.dataset.agent07RuntimeState = "starting";
runtimeStatusLine.textContent = "安全影子拉取启动中";
```

- [ ] **Step 3: Implement fixed trigger request**

Send exactly:

```js
JSON.stringify({ mode: "LIVE_NETWORK_SHADOW_PROBE" })
```

No date, model, publish, dry-run, repo, or user-entered values may be sent.

- [ ] **Step 4: Implement 409 and 500 behavior**

For `409 ORCHESTRATOR_BUSY`, keep the trigger disabled and join polling. For HTTP 500 or thrown fetch errors, clear active polling, release the button, and render an error message that includes `异常` or `重试`.

- [ ] **Step 5: Verify Green**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-ui-dom.test.mjs
node --test tests/agent07-service.test.mjs
```

Expected after Green: both commands pass.

## Self-Review

- Spec coverage: DOM topology, CSS namespace, first-frame disable, fixed POST body, 409 busy state, polling, 500 recovery, and dirty-workspace staging are each mapped to a task.
- Placeholder scan: this plan contains no open placeholders.
- Type and selector consistency: selectors match the approved SDD: `data-agent07-runtime-trigger`, `data-agent07-runtime-status`, and `.agent07-runtime-*`.
