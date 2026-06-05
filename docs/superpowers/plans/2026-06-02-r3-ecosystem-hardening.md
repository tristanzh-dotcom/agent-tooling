# R3 Ecosystem Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the R3 blockers that keep the ecosystem below an 8+ score: non-idempotent PVI tests, missing Pet quality infrastructure, incomplete Pet test coverage in the ecosystem gate, and weak CI coverage.

**Architecture:** Keep every project as an independent git repository. Fix deterministic test behavior before adding broader CI. Treat PetRelatedServices dirty user work as review-required and do not auto-delete or auto-commit it without TZ approval.

**Tech Stack:** Git, Node `node:test`, Python `pytest`, Ruff config, GitHub Actions, Codex-Ops ecosystem quality gate.

---

### Task 1: PVI JLR Test Idempotence

**Files:**
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/src/agent02-adapter.mjs`
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Create: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`
- Test: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`
- Test: `/Users/tristanzh/agent/web/tests/agent02-service.test.mjs`

- [ ] **Step 1: Write failing adapter idempotence test**

Create `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createJlrSalesAgent02Adapter } from "../src/agent02-adapter.mjs";

test("preview writes generated snapshots to the injected output path only", async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), "jlr-adapter-"));
  const snapshotPath = join(tempRoot, "latest_snapshot.json");

  const adapter = createJlrSalesAgent02Adapter({
    projectDir: new URL("..", import.meta.url).pathname,
    rawDir: join(tempRoot, "raw"),
    snapshotPath,
    sendCardsToFeishuBot: async () => {},
    runner: async () => ({
      cards: [{ schema: "2.0" }],
      reportPath: snapshotPath,
      cardSource: "test",
      sent: false,
    }),
  });

  const result = await adapter.preview();

  assert.equal(result.reportPath, snapshotPath);
});
```

Run: `cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales && node --test tests/agent02Adapter.test.js`

Expected now: either PASS with runner injection or FAIL if the adapter cannot guarantee injected output isolation. If it passes immediately, add a second test without `runner` using a temporary `snapshotPath` and assert the tracked `data/latest_snapshot.json` mtime/content is unchanged.

- [ ] **Step 2: Add web contract test for runtime output path**

Add to `/Users/tristanzh/agent/web/tests/agent02-service.test.mjs` near the JLR path tests:

```js
test("agent02 JLR runtime snapshots use an ignored runtime output path", async () => {
  const serverSource = await readFile(new URL("../server.mjs", import.meta.url), "utf8");

  assert.match(serverSource, /JLR_RUNTIME_OUTPUT_DIR|runtime-output|\\.runtime/);
  assert.doesNotMatch(serverSource, /join\\(jlrProjectDir, "data", "latest_snapshot\\.json"\\)/);
});
```

Run: `cd /Users/tristanzh/agent/web && node --test tests/agent02-service.test.mjs`

Expected: FAIL until `server.mjs` stops writing web-triggered snapshots to the tracked PVI data file.

- [ ] **Step 3: Implement runtime output separation**

In `/Users/tristanzh/agent/web/server.mjs`, change `jlrSnapshotPath` from the tracked workflow data file to an ignored runtime path, for example:

```js
const jlrRuntimeOutputDir = process.env.JLR_RUNTIME_OUTPUT_DIR ?? join(jlrProjectDir, ".runtime");
const jlrSnapshotPath = join(jlrRuntimeOutputDir, "latest_snapshot.json");
```

Ensure `Passenger-Vehicle-Intel/.gitignore` already covers `.runtime/`; if not, add:

```gitignore
.runtime/
*/.runtime/
```

- [ ] **Step 4: Verify no dirty state after tests**

Run:

```bash
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel
git restore workflows/jlr-sales/data/latest_snapshot.json
npm --prefix workflows/jlr-sales test
git status --short
```

Expected: tests pass and `git status --short` prints nothing for `workflows/jlr-sales/data/latest_snapshot.json`.

- [ ] **Step 5: Commit**

```bash
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel add workflows/jlr-sales/src/agent02-adapter.mjs workflows/jlr-sales/tests/agent02Adapter.test.js .gitignore
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel commit -m "fix: keep jlr tests from mutating tracked snapshots"
git -C /Users/tristanzh/agent/web add server.mjs tests/agent02-service.test.mjs
git -C /Users/tristanzh/agent/web commit -m "fix: write jlr runtime snapshots outside tracked data"
```

### Task 2: Pet Unified Quality Entry

**Files:**
- Create: `/Users/tristanzh/agent/PetRelatedServices/pyproject.toml`
- Create: `/Users/tristanzh/agent/PetRelatedServices/package.json`
- Create: `/Users/tristanzh/agent/PetRelatedServices/.github/workflows/quality.yml`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tests/test_ecosystem_quality_gate.py`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tools/ecosystem_quality_gate.py`

- [ ] **Step 1: Write failing Codex-Ops tests**

Extend `/Users/tristanzh/agent/Codex-Ops/tests/test_ecosystem_quality_gate.py`:

```python
def test_pet_quality_config_and_ci_are_required():
    root = ROOT.parents[0] / "PetRelatedServices"

    assert (root / "pyproject.toml").exists()
    assert (root / "package.json").exists()
    assert (root / ".github" / "workflows" / "quality.yml").exists()


def test_pet_verify_runs_python_and_node_tests():
    gate = load_quality_gate()
    specs = {spec.name: spec for spec in gate.PROJECT_SPECS}
    commands = {tuple(command.args) for command in specs["PetRelatedServices"].commands}

    assert ("python3", "-m", "pytest", "workflows/mantou-dog/tests", "-q") in commands
    assert ("npm", "test") in commands
```

Run: `cd /Users/tristanzh/agent/Codex-Ops && python3 -m pytest tests -q`

Expected: FAIL because Pet lacks these files and the ecosystem gate only runs Node root tests.

- [ ] **Step 2: Add Pet Python config**

Create `/Users/tristanzh/agent/PetRelatedServices/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["workflows/mantou-dog/tests"]
pythonpath = ["workflows/mantou-dog"]

[tool.ruff]
target-version = "py39"
line-length = 120
exclude = [
  ".git",
  ".pytest_cache",
  ".ruff_cache",
  "_archive_legacy",
  "venv",
  ".venv",
]

[tool.ruff.lint]
select = ["E", "F", "W"]
```

- [ ] **Step 3: Add Pet Node/Python unified package entry**

Create `/Users/tristanzh/agent/PetRelatedServices/package.json`:

```json
{
  "name": "pet-related-services",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/*.test.mjs && python3 -m pytest workflows/mantou-dog/tests -q",
    "check": "npm test"
  }
}
```

- [ ] **Step 4: Add Pet CI**

Create `/Users/tristanzh/agent/PetRelatedServices/.github/workflows/quality.yml`:

```yaml
name: Pet Related Services Quality

on:
  pull_request:
  push:

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
      - name: Install Python dependencies
        run: |
          python3 -m pip install --upgrade pip
          python3 -m pip install pytest pydantic fastapi starlette httpx tiktoken requests beautifulsoup4
      - name: Run Pet quality gate
        run: npm run check
```

- [ ] **Step 5: Update ecosystem gate**

In `/Users/tristanzh/agent/Codex-Ops/tools/ecosystem_quality_gate.py`, replace Pet commands with:

```python
ProjectSpec(
    name="PetRelatedServices",
    path="PetRelatedServices",
    commands=(
        CommandSpec("PetRelatedServices", ("node", "--test", "tests/*.test.mjs")),
        CommandSpec("PetRelatedServices", ("python3", "-m", "pytest", "workflows/mantou-dog/tests", "-q")),
    ),
),
```

- [ ] **Step 6: Verify and commit**

Run:

```bash
cd /Users/tristanzh/agent/PetRelatedServices
npm run check
cd /Users/tristanzh/agent/Codex-Ops
python3 -m pytest tests -q
python3 tools/ecosystem_quality_gate.py --mode verify --project PetRelatedServices
```

Expected: Pet Node 35 tests and Python 58 tests pass; Codex-Ops tests pass.

Commit:

```bash
git -C /Users/tristanzh/agent/PetRelatedServices add pyproject.toml package.json .github/workflows/quality.yml
git -C /Users/tristanzh/agent/PetRelatedServices commit -m "chore: add pet quality gate"
git -C /Users/tristanzh/agent/Codex-Ops add tools/ecosystem_quality_gate.py tests/test_ecosystem_quality_gate.py
git -C /Users/tristanzh/agent/Codex-Ops commit -m "fix: include pet python tests in ecosystem gate"
```

### Task 3: Pet Dirty Worktree Decision Gate

**Files:**
- Create: `/Users/tristanzh/agent/PetRelatedServices/docs/worktree-review/2026-06-02-r3-dirty-state-inventory.md`
- Modify only after TZ approval: Pet dirty files listed by `git status --short`

- [ ] **Step 1: Inventory dirty state without changing it**

Run:

```bash
cd /Users/tristanzh/agent/PetRelatedServices
git status --short
git diff --stat
find . -path ./venv -prune -o -type f -not -path './.git/*' -print | sort
```

Expected: inventory captures the deleted `PROJECT_RULES.md`, two modified historical docs, and untracked workflow/data/docs files.

- [ ] **Step 2: Create review document**

Create a Markdown table with columns:

```markdown
| Path | Status | Proposed disposition | Reason | Requires TZ approval |
|---|---|---|---|---|
```

Disposition values must be only `commit`, `ignore`, `archive`, or `leave_untracked`.

- [ ] **Step 3: Stop for TZ approval**

Do not commit, delete, archive, or ignore Pet dirty files until TZ approves the disposition table.

### Task 4: CI Coverage Upgrade

**Files:**
- Modify: `/Users/tristanzh/agent/Codex-Ops/.github/workflows/ecosystem-quality.yml`
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/.github/workflows/quality.yml`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tests/test_ecosystem_quality_gate.py`

- [ ] **Step 1: Add failing CI assertions**

Add tests that require:

```python
assert "python3 tools/ecosystem_quality_gate.py --mode verify --project Codex-Ops" in workflow_text
assert "npm ci" in pvi_workflow_text
assert "npm install" not in pvi_workflow_text
```

- [ ] **Step 2: Update workflows**

In Codex-Ops CI, add project-scoped verify:

```yaml
- name: Verify Codex-Ops project
  run: python3 tools/ecosystem_quality_gate.py --mode verify --project Codex-Ops
```

In PVI CI, change hardware supplier dashboard install from `npm install` to `npm ci`.

- [ ] **Step 3: Verify and commit**

Run:

```bash
cd /Users/tristanzh/agent/Codex-Ops
python3 -m pytest tests -q
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier-dashboard
npm run check
```

Commit:

```bash
git -C /Users/tristanzh/agent/Codex-Ops add .github/workflows/ecosystem-quality.yml tests/test_ecosystem_quality_gate.py
git -C /Users/tristanzh/agent/Codex-Ops commit -m "chore: verify codex ops in ci"
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel add .github/workflows/quality.yml
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel commit -m "fix: use deterministic npm ci in pvi workflow"
```

### Task 5: Root Boundary Cross-Reference

**Files:**
- Modify: `/Users/tristanzh/agent/AGENTS.md`
- Modify: `/Users/tristanzh/agent/web/tests/web-platform-notification.test.mjs`

- [ ] **Step 1: Add failing web governance test**

Add an assertion that root AGENTS references Pet's boundary notice:

```js
test("root project rules cross-reference Pet boundary notice", async () => {
  const rootRules = await readFile("/Users/tristanzh/agent/AGENTS.md", "utf8");

  assert.match(rootRules, /PetRelatedServices\\/docs\\/web-platform-boundary-notice\\.md/);
});
```

- [ ] **Step 2: Update root AGENTS**

Add a concise bullet under the Web publishing boundary section:

```markdown
- PetRelatedServices intentionally does not expose root `AGENTS.md`; for Agent03/Pet publishing boundary, read `/Users/tristanzh/agent/PetRelatedServices/docs/web-platform-boundary-notice.md`.
```

- [ ] **Step 3: Verify and commit**

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/web-platform-notification.test.mjs
```

Root `/Users/tristanzh/agent` is not a git repository, so only commit the web test:

```bash
git -C /Users/tristanzh/agent/web add tests/web-platform-notification.test.mjs
git -C /Users/tristanzh/agent/web commit -m "test: require pet boundary cross reference"
```

### Final Verification

- [ ] Run full local ecosystem verification:

```bash
cd /Users/tristanzh/agent/Codex-Ops
python3 tools/ecosystem_quality_gate.py --mode verify
```

- [ ] Restore known test-generated artifacts only if still produced, then fix the producing test before finalizing.
- [ ] Run status check:

```bash
for d in web Passenger-Vehicle-Intel Medical Local-photo-model Webstyle-editor Stratigic-AGI-System Codex-Ops PetRelatedServices; do
  printf '[%s]\n' "$d"
  git -C "/Users/tristanzh/agent/$d" status --short
done
```

Expected:
- All repos clean except Pet dirty files explicitly left pending TZ approval.
- PVI must be clean after running its tests.
- Pet quality gate must run both Node and Python tests.
