# Project Sentinel v3 Agent07 Telemetry Panel SDD

Date: 2026-06-17
Status: Draft for red-line specification review
Owner: TZ
Stage: 10.3 - Agent07 shadow evidence and runtime telemetry panel
Implementation roots:
- `/Users/tristanzh/agent/web`
- `/Users/tristanzh/agent/Git-Scout`

## 1. Scope

Stage 10.3 adds an Agent07-only Runtime telemetry panel that lets TZ inspect sanitized shadow-run evidence after the Stage 10.2 safe trigger exists.

The panel answers one operational question:

```text
What did the latest shadow run filter, downgrade, skip, or time out, and why?
```

It must preserve the Stage 10.2 control boundary:

- the trigger button remains a constrained safe shadow probe;
- the telemetry panel is read-only;
- the panel never starts runs, never calls model clients, and never publishes production data.

## 2. Non-Goals

- Do not parse runtime shadow JSON during initial `/agent07` page load.
- Do not render raw `scout_pipeline.shadow.json` contents in the browser.
- Do not expose GitHub tokens, model keys, local absolute paths, `.env` values, authorization headers, or private host topology.
- Do not add WebSocket, server-sent events, background daemons, or live streaming in Stage 10.3.
- Do not alter Agent07 approve/reject behavior.
- Do not restyle shared `.ka-*` shell, sidebar, navigation, layout, or theme tokens.
- Do not change Agent02, Agent03, Agent04, Agent05, Agent06, platform home, or shared framework files.

## 3. UI Segmented Layout Contract

Stage 10.3 introduces a right-column segmented mode inside the existing Agent07 right rail:

```text
Right rail
  Decision segment
    Token ROI
    approve/reject controls
    Stage 10.2 runtime trigger
  Runtime segment
    latest run summary
    telemetry category counters
    sanitized evidence rows
```

The first rendered page remains in `Decision` mode. The browser must not fetch `/api/agent07/runtime/shadow` until TZ explicitly switches to `Runtime`.

### 3.1 DOM Topology

Allowed new DOM selectors:

```html
<div class="agent07-telemetry-tabs" role="tablist" aria-label="Agent07 right rail mode">
  <button type="button" data-agent07-telemetry-tab="decision" aria-selected="true">Decision</button>
  <button type="button" data-agent07-telemetry-tab="runtime" aria-selected="false">Runtime</button>
</div>

<section class="agent07-telemetry-panel" data-agent07-telemetry-panel hidden>
  <header class="agent07-telemetry-head">
    <small>Runtime Shadow</small>
    <strong data-agent07-telemetry-title>影子证据</strong>
  </header>
  <div class="agent07-telemetry-summary" data-agent07-telemetry-summary></div>
  <div class="agent07-telemetry-list" data-agent07-telemetry-list></div>
</section>
```

Rules:

- `data-agent07-telemetry-tab="decision"` and `data-agent07-telemetry-tab="runtime"` each appear exactly once.
- `data-agent07-telemetry-panel` appears exactly once.
- The Runtime panel is hidden on initial page load.
- The initial boot JSON must not include telemetry evidence rows.
- The panel lives under Agent07 right rail only; no shared sidebar or shell node may be changed.

### 3.2 CSS Namespace and Token Inheritance

All new CSS selectors must be scoped under `.agent07-telemetry-*` or an existing Agent07-owned parent.

Allowed selector family:

```css
.agent07-telemetry-tabs
.agent07-telemetry-panel
.agent07-telemetry-head
.agent07-telemetry-summary
.agent07-telemetry-metric
.agent07-telemetry-list
.agent07-telemetry-row
.agent07-telemetry-tag
.agent07-telemetry-empty
.agent07-telemetry-error
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

Forbidden physical color values:

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

New styling must use existing theme tokens only:

```css
var(--ka-bg-surface)
var(--ka-bg-hover)
var(--ka-text-main)
var(--ka-text-body)
var(--ka-text-muted)
var(--ka-border)
var(--ka-border-strong)
var(--ka-radius-control, 8px)
var(--web-status-warning)
var(--web-status-danger)
var(--web-status-success)
```

## 4. Asynchronous Metadata Loading Contract

Initial `/agent07` page load may render only:

- current leads from `scout_pipeline.json`;
- existing Decision lane controls;
- empty Runtime panel shell.

Runtime telemetry fetch happens only after the Runtime tab is selected:

```text
click Runtime tab
  -> show panel loading state
  -> fetch /api/agent07/runtime/shadow
  -> parse compact sanitized DTO
  -> render counters and evidence rows
```

No Stage 10.3 code may synchronously read shadow files or embed shadow evidence in the page template.

### 4.1 Two-Stage Parsing

The browser performs two bounded stages after the async fetch:

1. Summary normalization:
   - read counts: `low_quality_filtered_count`, `low_relevance_overflow_count`, `readme_skip_count`, `query_timeout_skipped_count`;
   - render metric chips immediately;
   - if the payload has no row arrays, render a clear empty-state that says only aggregate telemetry is available.
2. Row derivation:
   - normalize each compact row into a fixed `TelemetryRow` shape;
   - generate reason tags from known fields;
   - run a final text sanitizer on every rendered value;
   - render rows grouped by category.

The panel must tolerate partial payloads. Missing row arrays are not fatal if aggregate counts exist.

## 5. Backend DTO Contract

Stage 10.1 Web facade currently returns aggregate counts only. Stage 10.3 may extend `/api/agent07/runtime/shadow` to return compact sanitized row arrays. It must still not return raw shadow blobs.

Allowed response shape:

```ts
type Agent07RuntimeShadowPanelResponse = {
  version: 1;
  run_id: string | null;
  generated_at: string;
  low_quality_filtered_count: number;
  low_relevance_overflow_count: number;
  readme_skip_count: number;
  query_timeout_skipped_count: number;
  categories: {
    low_quality_filtered: TelemetryRow[];
    low_relevance_overflow: TelemetryRow[];
    readme_skipped: TelemetryRow[];
    query_timeout_skipped: TelemetryRow[];
  };
};

type TelemetryRow = {
  repo: string;
  status:
    | "LOW_QUALITY_FILTERED"
    | "LOW_RELEVANCE_OVERFLOW"
    | "README_RATE_LIMIT_SKIPPED"
    | "QUERY_TIMEOUT_SKIPPED";
  label: string;
  tags: string[];
  score?: number;
  matched_positive?: number;
  matched_negative?: number;
  source?: string;
  sanitized_ref?: string;
};
```

Required server-side rules:

- `categories.*` arrays contain compact derived rows only.
- Raw `evidence` objects are not forwarded.
- Absolute local paths are rewritten before leaving the server.
- Token-like values are masked before leaving the server.
- Unknown fields are dropped by allow-list, not copied through.

## 6. Tagging Algorithm

The UI renders stable, high-resolution tags derived from compact DTO fields.

### 6.1 LOW_QUALITY_FILTERED

Rows with `status:"LOW_QUALITY_FILTERED"` must display at least one quality tag.

Mapping:

| Input reason/source | UI Tag |
| --- | --- |
| `LOCAL_INSTALL_POLLUTION` | `[ZIP_DETECTOR]` |
| `NO_ARTIFACT_SIGNAL` | `[NO_ARCH_SIGNAL]` |
| `README_FINGERPRINT_TIMEOUT` | `[README_TIMEOUT]` |
| unknown low-quality reason | `[LOW_QUALITY]` |

### 6.2 LOW_RELEVANCE_OVERFLOW

Rows with `status:"LOW_RELEVANCE_OVERFLOW"` must display a score neutralization tag:

```text
[Score: <score> | Matched: +<matched_positive> -<matched_negative>]
```

If `matched_positive` or `matched_negative` is absent, use `0`. If `score` is absent, use `Score: n/a`.

### 6.3 README and Query Skips

Rows derived from README guard skips:

| Status/source | UI Tag |
| --- | --- |
| `README_RATE_LIMIT_SKIPPED` | `[403_RATE_LIMIT]` |
| `COMPLIANT_SLEEP_EXCEEDED` | `[README_BUDGET]` |

Rows derived from query checkpoint timeouts:

| Status/source | UI Tag |
| --- | --- |
| `QUERY_TIMEOUT_SKIPPED` | `[8s_TIMEOUT]` |

## 7. Sanitization Engine

Sanitization is defense-in-depth: both server and browser apply it.

### 7.1 Server Sanitization

The Web facade must sanitize before JSON response:

```text
/Users/<name>/...             -> shadow://local-path/<basename>
/private/...                  -> shadow://local-path/<basename>
/var/folders/...              -> shadow://local-path/<basename>
<drive-letter>:\...           -> shadow://local-path/<basename>
ghp_<token>                   -> [MASKED_GITHUB_TOKEN]
github_pat_<token>            -> [MASKED_GITHUB_TOKEN]
sk-<token>                    -> [MASKED_MODEL_TOKEN]
Authorization: Bearer <value> -> Authorization: Bearer [MASKED]
```

### 7.2 Browser Sanitization

Before writing any string into DOM, the browser must run a final text sanitizer:

```text
absolute path pattern -> shadow://local-path/redacted
token pattern         -> [MASKED]
```

The renderer must use `textContent` or escaped HTML. It must not use raw `innerHTML` for untrusted telemetry values.

### 7.3 Render Invariant

The final DOM for the Runtime panel must not contain:

```text
/Users/
/private/
/var/folders/
ghp_
github_pat_
Authorization:
sk-
```

## 8. TDD Matrix

Stage 10.3 implementation must begin with Red tests before UI or server code changes.

Required test file:

```text
/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs
```

### 8.1 Async Load Test

Test:

- load `/agent07`;
- assert no request to `/api/agent07/runtime/shadow` happens before Runtime tab click;
- click Runtime tab;
- assert exactly one request to `/api/agent07/runtime/shadow`.

Expected Red before implementation: no Runtime tab exists.

### 8.2 Fixture Classification Test

Use a fixture containing:

- 39 `LOW_QUALITY_FILTERED` rows;
- 2 `LOW_RELEVANCE_OVERFLOW` rows;
- 1 README skip row;
- 1 query timeout row.

Assertions:

- DOM includes `39`, `2`, `1`, and `1` in the telemetry metrics;
- DOM includes `[ZIP_DETECTOR]` or `[NO_ARCH_SIGNAL]`;
- DOM includes a score tag matching `Score: 20 | Matched: +50 -30`;
- DOM includes `[403_RATE_LIMIT]`;
- DOM includes `[8s_TIMEOUT]`.

### 8.3 Sanitization Test

The fixture must include unsafe strings:

```text
/Users/tristanzh/agent/Git-Scout/storage/runtime_shadow/private
/private/tmp/sentinel
ghp_secret_token_must_not_leak
github_pat_secret_must_not_leak
Authorization: Bearer secret
sk-secret
```

Assertions:

- rendered DOM contains `shadow://`;
- rendered DOM does not contain any forbidden unsafe string or prefix.

### 8.4 Legacy Behavior Isolation Test

Assertions:

- approve/reject buttons still exist and dispatch original endpoints;
- Stage 10.2 runtime trigger still exists and still posts `{ mode: "LIVE_NETWORK_SHADOW_PROBE" }`;
- switching Runtime tab does not disable approve/reject buttons;
- returning to Decision tab does not clear selected lead state.

### 8.5 CSS Namespace Test

Assertions:

- `app/agent07.css` contains `.agent07-telemetry-*` selectors;
- no Stage 10.3 hunk adds forbidden physical color values;
- no shared `.ka-*`, `.platform-*`, or other Agent selectors are modified for telemetry.

Regression commands:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent07-telemetry-panel.test.mjs
node --test tests/agent07-ui-dom.test.mjs
node --test tests/agent07-service.test.mjs
```

Backend regression:

```bash
cd /Users/tristanzh/agent/Git-Scout
npm run typecheck
npm test
```

## 9. Dirty-Workspace Git Guard

The root repo and Web repo both have existing unrelated dirty or staged state. Stage 10.3 must keep commits narrow.

### 9.1 SDD Commit Guard

Only this SDD may be committed from root:

```bash
cd /Users/tristanzh/agent
git add docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-sdd.md
git diff --cached --name-only
git commit docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-sdd.md \
  -m "docs(sentinel): 创建 Agent07 影子证据与日志遥测面板(Stage 10.3)增量系统设计文档(SDD)"
```

Because root index may already contain Passenger-Vehicle-Intel staged files, the commit command must include the SDD pathspec.

### 9.2 TDD and Green Commit Guard

Allowed Stage 10.3 implementation files:

```text
/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs
/Users/tristanzh/agent/web/server.mjs
/Users/tristanzh/agent/web/app/agent07.js
/Users/tristanzh/agent/web/app/agent07.css
```

Rules:

- Never run `git add .`.
- Never run broad `git add app tests docs`.
- Use `git diff --cached --name-only` before every commit.
- If `server.mjs` or `agent07.css` contains unrelated dirty hunks, stage only Stage 10.3 hunks with `git add -p` or `git apply --cached`.
- Do not stage Agent02, Agent03, Agent04, Agent05, Agent06, platform, ops, config, or shared framework files.

## 10. Acceptance Criteria

This SDD is accepted when:

- the document exists at `/Users/tristanzh/agent/docs/superpowers/specs/2026-06-17-project-sentinel-v3-agent07-telemetry-panel-sdd.md`;
- the document requires Runtime telemetry to load only after Runtime tab selection;
- the document defines `.agent07-telemetry-*` namespace and token-only styling;
- the document defines compact sanitized DTO rows rather than raw shadow JSON;
- the document defines tags for low-quality filters, low-relevance overflow, README skips, and query timeouts;
- the document defines server and browser sanitization invariants;
- the document defines `agent07-telemetry-panel.test.mjs` TDD coverage;
- the document defines root/Web Git guard rules for existing dirty and staged state.

## 11. Immediate Next Step After SDD Approval

After TZ approves this SDD, Stage 10.3 proceeds in strict SDD/TDD order:

1. Create `/Users/tristanzh/agent/web/tests/agent07-telemetry-panel.test.mjs`.
2. Run it and verify Red failures for missing Runtime tab, missing async fetch, missing tags, and missing sanitization.
3. Extend `/api/agent07/runtime/shadow` only as needed for compact sanitized DTO rows.
4. Add Agent07-only Runtime panel DOM, JS renderer, and tokenized CSS.
5. Run the Stage 10.3 Web tests, Stage 10.2 UI tests, Agent07 service tests, Git-Scout typecheck, and Git-Scout tests.
