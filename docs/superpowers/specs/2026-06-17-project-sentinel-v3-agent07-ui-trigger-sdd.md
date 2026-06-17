# Project Sentinel v3 Agent07 UI Trigger SDD

Date: 2026-06-17
Status: Draft for red-line specification review
Owner: TZ
Stage: 10.2 - Agent07 frontend control strip and status injection
Implementation roots:
- `/Users/tristanzh/agent/web`
- `/Users/tristanzh/agent/Git-Scout`

## 1. Scope

Stage 10.2 adds a single Agent07-owned frontend entry point for the already-wired runtime facade:

```text
Agent07 right action area -> POST /api/agent07/runtime/trigger -> safe runtime facade
```

The UI control is a narrow Web publishing delta. It only renders and operates inside the Agent07 page, and it must not change shared layout paradigms, shared theme definitions, other Agent routes, or the Git-Scout production publish path.

The new control starts a safe live-network shadow probe from the browser. The browser request is hard-coded to:

```json
{ "mode": "LIVE_NETWORK_SHADOW_PROBE" }
```

The backend remains responsible for enforcing safe gates:

```json
{
  "dry_run": true,
  "live_network": true,
  "live_model": false,
  "live_publish": false
}
```

## 2. Non-Goals

- Do not run the real Git-Scout production orchestrator directly from Web UI.
- Do not enable live model execution from the browser.
- Do not enable live publish from the browser.
- Do not mutate `/Users/tristanzh/agent/Git-Scout/data/scout_pipeline.json`.
- Do not alter Agent02, Agent03, Agent04, Agent05, Agent06, platform home, shared sidebar, shared shell, or shared theme files.
- Do not replace or refactor Agent07 approve/reject behavior.
- Do not stage, commit, or normalize unrelated dirty workspace files.

## 3. Existing Interface Dependency

Stage 10.1 already owns the backend facade under `/api/agent07/runtime/*`.

Stage 10.2 consumes only:

| Method | Path | UI Usage |
| --- | --- | --- |
| `POST` | `/api/agent07/runtime/trigger` | Start a safe shadow probe. |
| `GET` | `/api/agent07/runtime/status` | Poll whether the facade is `RUNNING` or `IDLE`. |

The UI must not call `/api/agent07/runtime/logs` or `/api/agent07/runtime/shadow` in this stage. Telemetry display can be designed in a later stage after its own SDD and TDD contract.

## 4. DOM Injection Topology

The server-rendered Agent07 HTML template must inject the runtime trigger inside the existing Agent07-only action group:

```html
<div class="agent07-actions">
  <button
    class="agent07-action agent07-runtime-trigger"
    type="button"
    data-agent07-runtime-trigger
  >触发今日拉取</button>
  <button class="agent07-action agent07-action--approve" type="button" data-agent07-approve>批准深挖</button>
  <button class="agent07-action agent07-action--reject" type="button" data-agent07-reject>流放</button>
</div>
<p class="agent07-action-status" data-agent07-action-status>等待 TZ 裁决</p>
<p class="agent07-runtime-status" data-agent07-runtime-status>影子拉取待命</p>
```

Rules:

- `data-agent07-runtime-trigger` must appear exactly once per Agent07 page.
- The runtime trigger must be a child or direct descendant of `.agent07-actions`.
- The runtime trigger must not replace or wrap `data-agent07-approve` or `data-agent07-reject`.
- Runtime status must use `data-agent07-runtime-status`, not overload `data-agent07-action-status`.
- Approve/reject lead mutation status remains owned by `data-agent07-action-status`.
- Runtime status text is operational status only, not audit decision status.

This creates two independent UI status lanes:

```text
Lead decision lane:
  data-agent07-approve / data-agent07-reject -> data-agent07-action-status

Runtime lane:
  data-agent07-runtime-trigger -> data-agent07-runtime-status
```

## 5. CSS Namespace and Theme Token Invariance

All new CSS selectors must be scoped to `.agent07-runtime-*` or an existing Agent07-owned parent.

Allowed new selectors:

```css
.agent07-runtime-trigger
.agent07-runtime-trigger.is-running
.agent07-runtime-status
.agent07-runtime-status[data-agent07-runtime-state="idle"]
.agent07-runtime-status[data-agent07-runtime-state="starting"]
.agent07-runtime-status[data-agent07-runtime-state="running"]
.agent07-runtime-status[data-agent07-runtime-state="error"]
```

Forbidden selectors:

```css
body
:root
.ka-sidebar
.ka-nav
.ka-frame
.agent02-*
.agent03-*
.agent04-*
.agent05-*
.agent06-*
.platform-*
```

Forbidden physical colors:

```text
#000000
#050505
#ffffff
#888888
#222222
black
white
red
green
blue
```

All new styling must inherit from existing theme tokens, including but not limited to:

```css
var(--ka-bg-surface)
var(--ka-bg-hover)
var(--ka-text-main)
var(--ka-text-body)
var(--ka-text-muted)
var(--ka-border)
var(--ka-border-strong)
var(--ka-radius-control, 8px)
var(--web-action-primary)
var(--web-status-warning)
var(--web-status-danger)
var(--web-status-success)
```

If the trigger needs a loading visual, the implementation may use opacity, border color, text, or a tokenized pseudo-element. It must not introduce hard-coded gradients, decorative blobs, global animation names with generic names, or unrelated page-level visual systems.

## 6. First-Frame Disable Contract

The click handler must disable the runtime trigger before any awaited operation.

Required micro-order:

```text
click event enters handler
  -> if trigger is already disabled, return
  -> set trigger.disabled = true
  -> set data-agent07-runtime-state = "starting"
  -> change button label to "拉取启动中"
  -> then call fetch("/api/agent07/runtime/trigger", ...)
```

The implementation must not wait for `fetch()`, `await`, `setTimeout()`, or status polling before disabling the button.

This is a first-frame UI failsafe: within the same synchronous event turn, a second user click must see the button as disabled and must not emit a second POST request.

## 7. Runtime Polling State Machine

The runtime lane has five states:

| State | Trigger Disabled | Button Label | Status Text | Exit |
| --- | --- | --- | --- | --- |
| `idle` | false | `触发今日拉取` | `影子拉取待命` | User click |
| `starting` | true | `拉取启动中` | `安全影子拉取启动中` | POST resolves |
| `running` | true | `运行中` | `影子拉取运行中` | Poll sees `IDLE`, timeout, or error |
| `complete` | false | `触发今日拉取` | `影子拉取已完成` | Next user click |
| `error` | false | `重新触发拉取` | Error message | Next user click |

### 7.1 Successful Start

When `POST /api/agent07/runtime/trigger` returns `202`, the UI must:

1. Parse the JSON body.
2. Confirm `body.gates.live_model === false`.
3. Confirm `body.gates.live_publish === false`.
4. Move to `running`.
5. Start polling `GET /api/agent07/runtime/status`.

If the body is malformed or unsafe gates are returned, the UI must move to `error` and release the button. The unsafe response must not trigger follow-up calls.

### 7.2 HTTP 409 Busy

When `POST /api/agent07/runtime/trigger` returns `409` with `status:"ORCHESTRATOR_BUSY"`, the UI must not treat it as a fatal error.

Required behavior:

```text
409 ORCHESTRATOR_BUSY
  -> state = running
  -> trigger remains disabled
  -> status text = "影子拉取已在运行"
  -> start polling /api/agent07/runtime/status
```

This makes the browser idempotent under a busy backend: it joins the visible running state instead of firing more trigger requests.

### 7.3 Polling Cadence and Release

Polling must use `GET /api/agent07/runtime/status`.

Required defaults:

```text
poll interval: 1000 ms
max polls: 45
max visible lock: about 45 seconds
```

Release rules:

- If status returns `IDLE`, move to `complete` and release the button.
- If status returns `RUNNING`, keep disabled and continue polling.
- If polling reaches max polls, move to `error`, release the button, and show a timeout message.
- If polling throws network errors, move to `error`, release the button, and show a network error message.

The implementation must clear any active polling timer before starting a new one.

## 8. JavaScript Boundary

The Agent07 frontend script may add the following local variables/functions:

```js
const runtimeTriggerButton = document.querySelector("[data-agent07-runtime-trigger]");
const runtimeStatusLine = document.querySelector("[data-agent07-runtime-status]");

function setRuntimeState(state, message) {}
async function postAgent07RuntimeTrigger() {}
async function pollAgent07RuntimeStatus() {}
async function triggerAgent07Runtime() {}
```

Rules:

- Existing `mutate()`, `postAgent07Approve()`, and `postAgent07Reject()` behavior must remain intact.
- `setBusy()` must continue to affect only approve/reject buttons.
- Runtime trigger disabling must be independent from approve/reject disabling.
- Runtime requests must use `content-type: application/json`.
- Runtime trigger request body must be exactly:

```json
{ "mode": "LIVE_NETWORK_SHADOW_PROBE" }
```

No date, live model, live publish, dry-run override, repo name, or user-entered value may be sent from the browser in Stage 10.2.

## 9. TDD Contract

Stage 10.2 implementation must begin with Red tests before any production UI code changes.

Required new or extended test file:

```text
/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs
```

Minimum assertions:

1. HTML DOM contract:
   - Fetch `/agent07`.
   - Parse the HTML.
   - Assert `.agent07-actions [data-agent07-runtime-trigger]` count is exactly `1`.
   - Assert `data-agent07-approve` count is exactly `1`.
   - Assert `data-agent07-reject` count is exactly `1`.
   - Assert `data-agent07-runtime-status` count is exactly `1`.

2. Request body contract:
   - Load the Agent07 frontend in a DOM or browser test harness.
   - Stub/intercept `fetch`.
   - Click `data-agent07-runtime-trigger`.
   - Assert the first runtime POST is sent to `/api/agent07/runtime/trigger`.
   - Assert method is `POST`.
   - Assert body parses exactly to:

```json
{ "mode": "LIVE_NETWORK_SHADOW_PROBE" }
```

3. First-frame disable contract:
   - Click the runtime trigger.
   - Before resolving the intercepted fetch promise, assert `button.disabled === true`.
   - Assert the visible label changed from `触发今日拉取` to a loading label.

4. Busy contract:
   - Intercept trigger response with HTTP `409` and body `{ "status": "ORCHESTRATOR_BUSY" }`.
   - Assert UI moves to running/busy status.
   - Assert the trigger remains disabled while status polling reports `RUNNING`.
   - Assert no second POST is emitted by the same click sequence.

5. Approve/reject isolation:
   - Existing approve and reject buttons must still dispatch their original endpoints.
   - Runtime trigger must not call `/api/agent07/approve` or `/api/agent07/reject`.
   - Approve/reject clicks must not call `/api/agent07/runtime/trigger`.

6. CSS token contract:
   - Read `/Users/tristanzh/agent/web/app/agent07.css`.
   - Assert new `.agent07-runtime-*` selectors exist.
   - Assert no forbidden physical colors are introduced by the Stage 10.2 hunk.
   - Assert no shared shell selectors are modified by the Stage 10.2 hunk.

Regression baseline:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-ui-dom.test.mjs
node --test tests/agent07-service.test.mjs
```

## 10. Dirty-Workspace Git Guard

The current `/Users/tristanzh/agent/web` workspace contains many existing dirty files. Stage 10.2 implementation must use selective staging only.

Before implementation:

```bash
cd /Users/tristanzh/agent/web
git status --short
git diff -- app/agent07.js app/agent07.css tests/agent07-service.test.mjs server.mjs
```

During TDD and Green:

- Never run `git add .`.
- Never run `git add app/ tests/ docs/`.
- Never stage Agent02, Agent03, Agent04, Agent05, Agent06, platform, ops, config, or shared framework files.
- Prefer `git add -p` for files that already contain unrelated dirty hunks.
- If the implementation file already has unrelated hunks, inspect with `git diff -- <file>` before staging.
- If a file contains mixed ownership hunks that cannot be safely separated, stop and ask TZ before committing.

Allowed Stage 10.2 implementation files:

```text
/Users/tristanzh/agent/web/server.mjs
/Users/tristanzh/agent/web/app/agent07.js
/Users/tristanzh/agent/web/app/agent07.css
/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs
```

Allowed Stage 10.2 SDD file:

```text
/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-sdd.md
```

The SDD commit must stage only the SDD file:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-sdd.md
git diff --cached --name-only
git commit -m "docs(sentinel): 创建 Agent07 前端操作区控制按钮注入(Stage 10.2)增量系统设计文档(SDD)"
```

The implementation commit, in a later step, must explicitly show the staged file list before commit.

## 11. Acceptance Criteria

This SDD is accepted when:

- The document exists at `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-ui-trigger-sdd.md`.
- The document defines DOM injection under `.agent07-actions`.
- The document requires `.agent07-runtime-*` CSS namespace isolation.
- The document forbids hard-coded physical colors for the new UI.
- The document defines first-frame disabling before network work.
- The document defines HTTP 409 busy behavior as a running state, not a fatal error.
- The document defines polling against `/api/agent07/runtime/status`.
- The document defines selective staging guardrails for the dirty workspace.
- The SDD commit stages no `web/` file.

## 12. Immediate Next Step After SDD Approval

After TZ approves this SDD, Stage 10.2 proceeds in strict SDD/TDD order:

1. Create or extend `/Users/tristanzh/agent/web/tests/agent07-ui-dom.test.mjs`.
2. Run the new test and verify it fails for missing runtime trigger DOM/JS behavior.
3. Implement the smallest Agent07-only HTML/JS/CSS change.
4. Run Agent07 UI DOM test and Agent07 service test.
5. Inspect staged files and commit only Stage 10.2 hunks.
