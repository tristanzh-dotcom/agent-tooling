# R3 Ecosystem Hardening V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the R3 blockers with verified assumptions: PVI must stay clean after tests, Pet quality infrastructure must not depend on untracked hidden files, CI must be deterministic, and root boundary changes must be reversible.

**Architecture:** Split the work into an automatic lane and an approval-gated Pet lane. PVI and CI hardening can proceed directly after confirmation. Pet cannot be fully CI-enabled until TZ approves which currently-untracked Pet workflow files become tracked source, because the passing Python tests depend on untracked `workflows/` and root `mcht_ui.py`.

**Tech Stack:** Git, Node `node:test`, Python `pytest`, `requirements.txt`, Ruff config, GitHub Actions, Codex-Ops ecosystem quality gate.

---

## Verified Preflight Facts

- `Passenger-Vehicle-Intel/workflows/jlr-sales/src/agent02-adapter.mjs` already accepts injected `snapshotPath`.
- `latest_snapshot.json` writers are limited to JLR collect scripts and the JLR Agent02 adapter path; no matching `auto_intelligence_agent/` writer was found.
- `Passenger-Vehicle-Intel/hardware-supplier-dashboard/package-lock.json` is currently missing, so `npm ci` requires generating and committing a lockfile first.
- `PetRelatedServices` has no root `requirements.txt`, `pyproject.toml`, or `package.json`.
- Pet Python tests pass locally because they depend on untracked files, including `/Users/tristanzh/agent/PetRelatedServices/mcht_ui.py` and untracked `workflows/mantou-dog/`.
- Root `/Users/tristanzh/agent` is not a git repository; root `AGENTS.md` edits need an explicit versioning/reversibility strategy.

## Time Estimate

| Task | Estimate | Approval Needed |
|---|---:|---|
| Task 1 PVI idempotence | 1.5h | No |
| Task 2 Pet dirty inventory | 0.5h | Produces approval table |
| Task 3 Pet quality gate after approval | 1.5h | Yes, depends on Task 2 |
| Task 4 CI deterministic upgrade | 0.7h | No |
| Task 5 Root boundary reference | 0.4h | Yes, root AGENTS strategy |
| Final verification | 0.5h | No |

Expected automatic-lane gain: R3 7.25 -> about 7.45-7.6. Expected after Pet approval lane: about 7.7. Reaching 8+ still requires Phase 5/6 canonical migration and Pet dirty-state closure.

---

### Task 1: PVI JLR Test Idempotence

**Files:**
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/src/agent02-adapter.mjs`
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/.gitignore`
- Modify: `/Users/tristanzh/agent/web/server.mjs`
- Create: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`
- Test: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`
- Test: `/Users/tristanzh/agent/web/tests/agent02-service.test.mjs`

- [ ] **Step 1: Confirm all JLR snapshot writers before edits**

Run:

```bash
rg -n "latest_snapshot\\.json|writeFile\\(|snapshotPath|outputPath" /Users/tristanzh/agent/Passenger-Vehicle-Intel -g '!node_modules' -g '!venv' -g '!_archive_legacy'
```

Expected: writes are limited to JLR `collect.js`, `sources.js` raw downloads, and `workflows/jlr-sales/src/agent02-adapter.mjs`. If a non-JLR tracked runtime writer appears, stop and revise this task.

- [ ] **Step 2: Write failing web runtime-output contract**

Add to `/Users/tristanzh/agent/web/tests/agent02-service.test.mjs`:

```js
test("agent02 JLR runtime snapshots use an ignored runtime output path", async () => {
  const serverSource = await readFile(new URL("../server.mjs", import.meta.url), "utf8");

  assert.match(serverSource, /JLR_RUNTIME_OUTPUT_DIR|\\.runtime/);
  assert.doesNotMatch(serverSource, /join\\(jlrProjectDir, "data", "latest_snapshot\\.json"\\)/);
});
```

Run:

```bash
cd /Users/tristanzh/agent/web
node --test tests/agent02-service.test.mjs
```

Expected: FAIL until `server.mjs` stops injecting the tracked `data/latest_snapshot.json` as runtime output.

- [ ] **Step 3: Add adapter idempotence test**

Create `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/tests/agent02Adapter.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createJlrSalesAgent02Adapter } from "../src/agent02-adapter.mjs";

test("preview writes generated snapshots to the injected output path only", async () => {
  const tempRoot = await mkdtemp(join(tmpdir(), "jlr-adapter-"));
  const projectDir = new URL("..", import.meta.url).pathname;
  const trackedSnapshotPath = join(projectDir, "data", "latest_snapshot.json");
  const before = await readFile(trackedSnapshotPath, "utf8");
  const beforeStat = await stat(trackedSnapshotPath);
  const snapshotPath = join(tempRoot, "latest_snapshot.json");

  const adapter = createJlrSalesAgent02Adapter({
    projectDir,
    rawDir: join(tempRoot, "raw"),
    snapshotPath,
    sendCardsToFeishuBot: async () => {},
  });

  const result = await adapter.preview();
  const after = await readFile(trackedSnapshotPath, "utf8");
  const afterStat = await stat(trackedSnapshotPath);

  assert.equal(result.reportPath, snapshotPath);
  assert.equal(after, before);
  assert.equal(afterStat.mtimeMs, beforeStat.mtimeMs);
});
```

Run:

```bash
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales
node --test tests/agent02Adapter.test.js
```

Expected: PASS once runtime callers inject a temp/ignored `snapshotPath`; if this fails because the adapter writes `join(projectDir, "data")` regardless of `snapshotPath`, fix the adapter mkdir target to `dirname(snapshotPath)`.

- [ ] **Step 4: Implement runtime output separation**

In `/Users/tristanzh/agent/web/server.mjs`, replace the tracked snapshot path with an ignored runtime output path:

```js
const jlrRuntimeOutputDir = process.env.JLR_RUNTIME_OUTPUT_DIR ?? join(jlrProjectDir, ".runtime");
const jlrSnapshotPath = join(jlrRuntimeOutputDir, "latest_snapshot.json");
```

In `/Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales/src/agent02-adapter.mjs`, ensure directory creation follows the injected output path:

```js
await mkdir(dirname(snapshotPath), { recursive: true });
```

Add the import:

```js
import { dirname, join } from "node:path";
```

Add ignore rules to `/Users/tristanzh/agent/Passenger-Vehicle-Intel/.gitignore` if missing:

```gitignore
.runtime/
*/.runtime/
```

- [ ] **Step 5: Verify PVI remains clean**

Run:

```bash
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel restore workflows/jlr-sales/data/latest_snapshot.json
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/workflows/jlr-sales
npm test
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel status --short
```

Expected: JLR tests pass and `latest_snapshot.json` does not appear in status.

- [ ] **Step 6: Commit**

```bash
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel add .gitignore workflows/jlr-sales/src/agent02-adapter.mjs workflows/jlr-sales/tests/agent02Adapter.test.js
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel commit -m "fix: keep jlr tests from mutating tracked snapshots"
git -C /Users/tristanzh/agent/web add server.mjs tests/agent02-service.test.mjs
git -C /Users/tristanzh/agent/web commit -m "fix: write jlr runtime snapshots outside tracked data"
```

### Task 2: Pet Dirty Worktree Inventory And Approval Gate

**Files:**
- Create: `/Users/tristanzh/agent/PetRelatedServices/docs/worktree-review/2026-06-02-r3-dirty-state-inventory.md`

- [ ] **Step 1: Generate focused inventory without noise**

Run:

```bash
cd /Users/tristanzh/agent/PetRelatedServices
git status --short
git diff --stat
find . \
  -path './.git' -prune -o \
  -path './venv' -prune -o \
  -path './node_modules' -prune -o \
  -path './__pycache__' -prune -o \
  -path './.pytest_cache' -prune -o \
  -path './.ruff_cache' -prune -o \
  -type f -print | sort
```

- [ ] **Step 2: Create decision table**

Create `/Users/tristanzh/agent/PetRelatedServices/docs/worktree-review/2026-06-02-r3-dirty-state-inventory.md` with:

```markdown
# PetRelatedServices R3 Dirty State Inventory

Date: 2026-06-02

| Path | Status | Proposed disposition | Reason | Requires TZ approval |
|---|---|---|---|---|
| mcht_ui.py | untracked | commit | Required by workflows/mantou-dog/tests/test_mcht_ui.py | yes |
| workflows/mantou-dog/ | untracked | commit | Required by the 58 Python tests and future Pet CI | yes |
| PROJECT_RULES.md | deleted | archive or accept deletion | Root context exposure rule conflicts with active Pet tests | yes |
```

Complete the table for every dirty path. Allowed dispositions: `commit`, `ignore`, `archive`, `leave_untracked`, `accept_deletion`.

- [ ] **Step 3: Stop for TZ approval**

Do not commit, delete, archive, or ignore Pet dirty files until TZ approves this table. This is a hard stop.

### Task 3: Pet Unified Quality Entry After Approval

**Files:**
- Create: `/Users/tristanzh/agent/PetRelatedServices/requirements.txt`
- Create: `/Users/tristanzh/agent/PetRelatedServices/pyproject.toml`
- Create: `/Users/tristanzh/agent/PetRelatedServices/package.json`
- Create: `/Users/tristanzh/agent/PetRelatedServices/.github/workflows/quality.yml`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tests/test_ecosystem_quality_gate.py`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tools/ecosystem_quality_gate.py`

- [ ] **Step 1: Only start after Task 2 approval**

Minimum approval needed: commit the files required by `workflows/mantou-dog/tests`, including `mcht_ui.py` and `workflows/mantou-dog/`.

- [ ] **Step 2: Write failing Codex-Ops tests**

Add tests requiring:

```python
def test_pet_quality_config_and_ci_are_required():
    root = ROOT.parents[0] / "PetRelatedServices"

    assert (root / "requirements.txt").exists()
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

- [ ] **Step 3: Add pinned Pet requirements**

Create `/Users/tristanzh/agent/PetRelatedServices/requirements.txt` from the currently passing local venv direct dependencies:

```text
fastapi==0.128.8
httpx==0.28.1
pandas==2.3.3
pydantic==2.13.4
pytest==8.4.2
python-multipart==0.0.20
requests==2.32.5
starlette==0.49.3
streamlit==1.50.0
tiktoken==0.13.0
uvicorn==0.39.0
```

- [ ] **Step 4: Add Pet quality config and scripts**

Create `/Users/tristanzh/agent/PetRelatedServices/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["workflows/mantou-dog/tests"]
pythonpath = [".", "workflows/mantou-dog"]

[tool.ruff]
target-version = "py39"
line-length = 120
exclude = [".git", ".pytest_cache", ".ruff_cache", "_archive_legacy", "venv", ".venv"]

[tool.ruff.lint]
select = ["E", "F", "W"]
```

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

- [ ] **Step 5: Add Pet CI using requirements.txt**

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
          node-version: "24.x"
      - name: Install Python dependencies
        run: |
          python3 -m pip install --upgrade pip
          python3 -m pip install -r requirements.txt
      - name: Run Pet quality gate
        run: npm run check
```

- [ ] **Step 6: Update ecosystem gate**

Pet commands become:

```python
ProjectSpec(
    name="PetRelatedServices",
    path="PetRelatedServices",
    commands=(
        CommandSpec("PetRelatedServices", ("npm", "test")),
        CommandSpec("PetRelatedServices", ("python3", "-m", "pytest", "workflows/mantou-dog/tests", "-q")),
    ),
),
```

If `npm test` already runs Python tests, prefer a single `CommandSpec("PetRelatedServices", ("npm", "test"))` and assert that `package.json` includes both test commands.

- [ ] **Step 7: Verify and commit**

Run:

```bash
cd /Users/tristanzh/agent/PetRelatedServices
npm run check
cd /Users/tristanzh/agent/Codex-Ops
python3 -m pytest tests -q
python3 tools/ecosystem_quality_gate.py --mode verify --project PetRelatedServices
```

Commit approved Pet source/config only:

```bash
git -C /Users/tristanzh/agent/PetRelatedServices add requirements.txt pyproject.toml package.json .github/workflows/quality.yml
git -C /Users/tristanzh/agent/PetRelatedServices commit -m "chore: add pet quality gate"
git -C /Users/tristanzh/agent/Codex-Ops add tools/ecosystem_quality_gate.py tests/test_ecosystem_quality_gate.py
git -C /Users/tristanzh/agent/Codex-Ops commit -m "fix: include pet python tests in ecosystem gate"
```

### Task 4: CI Determinism Upgrade

**Files:**
- Modify: `/Users/tristanzh/agent/Codex-Ops/.github/workflows/ecosystem-quality.yml`
- Modify: `/Users/tristanzh/agent/Codex-Ops/tests/test_ecosystem_quality_gate.py`
- Modify: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/.github/workflows/quality.yml`
- Create: `/Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier-dashboard/package-lock.json`

- [ ] **Step 1: Write failing CI assertions**

Add tests requiring Codex-Ops project-scoped verify and deterministic PVI install:

```python
def test_codex_ops_ci_runs_project_scoped_verify():
    workflow = ROOT / ".github" / "workflows" / "ecosystem-quality.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "python3 tools/ecosystem_quality_gate.py --mode verify --project Codex-Ops" in text


def test_pvi_hardware_dashboard_ci_uses_npm_ci_with_lockfile():
    workflow = ROOT.parents[0] / "Passenger-Vehicle-Intel" / ".github" / "workflows" / "quality.yml"
    package_lock = ROOT.parents[0] / "Passenger-Vehicle-Intel" / "hardware-supplier-dashboard" / "package-lock.json"
    text = workflow.read_text(encoding="utf-8")

    assert package_lock.exists()
    assert "npm ci" in text
    assert "npm install" not in text
```

- [ ] **Step 2: Generate hardware dashboard lockfile**

Run:

```bash
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier-dashboard
npm install --package-lock-only
```

Expected: creates `package-lock.json` without installing new tracked source.

- [ ] **Step 3: Update workflows**

In PVI workflow, change hardware dashboard step:

```yaml
run: |
  npm ci
  npm run check
```

In Codex-Ops workflow, add:

```yaml
- name: Verify Codex-Ops project
  run: python3 tools/ecosystem_quality_gate.py --mode verify --project Codex-Ops
```

- [ ] **Step 4: Verify and commit**

Run:

```bash
cd /Users/tristanzh/agent/Codex-Ops
python3 -m pytest tests -q
cd /Users/tristanzh/agent/Passenger-Vehicle-Intel/hardware-supplier-dashboard
npm ci
npm run check
```

Commit:

```bash
git -C /Users/tristanzh/agent/Codex-Ops add .github/workflows/ecosystem-quality.yml tests/test_ecosystem_quality_gate.py
git -C /Users/tristanzh/agent/Codex-Ops commit -m "chore: verify codex ops in ci"
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel add .github/workflows/quality.yml hardware-supplier-dashboard/package-lock.json
git -C /Users/tristanzh/agent/Passenger-Vehicle-Intel commit -m "fix: use deterministic npm ci in pvi workflow"
```

### Task 5: Root Boundary Cross-Reference Strategy

**Files:**
- Create: `/Users/tristanzh/agent/Codex-Ops/docs/root-governance/2026-06-02-root-agents-pet-boundary-patch.md`
- Modify after TZ approval: `/Users/tristanzh/agent/AGENTS.md`
- Modify: `/Users/tristanzh/agent/web/tests/web-platform-notification.test.mjs`

- [ ] **Step 1: Do not initialize root git in this phase**

Reason: `/Users/tristanzh/agent` contains multiple nested git repositories, local archives, venvs, and generated artifacts. Root `git init` is a separate governance migration and should not be mixed into R4 hardening.

- [ ] **Step 2: Create tracked reversible patch record in Codex-Ops**

Create `/Users/tristanzh/agent/Codex-Ops/docs/root-governance/2026-06-02-root-agents-pet-boundary-patch.md`:

```markdown
# Root AGENTS Pet Boundary Patch

Date: 2026-06-02

Target file: `/Users/tristanzh/agent/AGENTS.md`

Reason: PetRelatedServices intentionally avoids root `AGENTS.md`; web publishing workers need an explicit root-level pointer to the Pet boundary notice.

Patch:

```diff
+- PetRelatedServices intentionally does not expose root `AGENTS.md`; for Agent03/Pet publishing boundary, read `/Users/tristanzh/agent/PetRelatedServices/docs/web-platform-boundary-notice.md`.
```
```

- [ ] **Step 3: Stop for TZ approval before editing root AGENTS**

After approval, apply the one-line root `AGENTS.md` edit and add a web governance test:

```js
test("root project rules cross-reference Pet boundary notice", async () => {
  const rootRules = await readFile("/Users/tristanzh/agent/AGENTS.md", "utf8");

  assert.match(rootRules, /PetRelatedServices\\/docs\\/web-platform-boundary-notice\\.md/);
});
```

- [ ] **Step 4: Commit tracked parts**

```bash
git -C /Users/tristanzh/agent/Codex-Ops add docs/root-governance/2026-06-02-root-agents-pet-boundary-patch.md
git -C /Users/tristanzh/agent/Codex-Ops commit -m "docs: record root pet boundary patch"
git -C /Users/tristanzh/agent/web add tests/web-platform-notification.test.mjs
git -C /Users/tristanzh/agent/web commit -m "test: require pet boundary cross reference"
```

### Final Verification

- [ ] Run:

```bash
cd /Users/tristanzh/agent/Codex-Ops
python3 tools/ecosystem_quality_gate.py --mode audit
python3 tools/ecosystem_quality_gate.py --mode verify
```

- [ ] Check repository cleanliness:

```bash
for d in web Passenger-Vehicle-Intel Medical Local-photo-model Webstyle-editor Stratigic-AGI-System Codex-Ops PetRelatedServices; do
  printf '[%s]\n' "$d"
  git -C "/Users/tristanzh/agent/$d" status --short
done
```

Expected:
- PVI clean after its tests.
- Pet remaining dirty state matches TZ-approved inventory only.
- Codex-Ops, web, and other projects clean.
