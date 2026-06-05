# Agent Ecosystem Quality White Paper

> **Audit Date:** 2026-06-01
> **Scope:** `/Users/tristanzh/agent/` — all subprojects, workspaces, symlinks, and loose files.
> **Auditor:** AI Systems Architect (explore subagent, full-depth scan)
> **Classification:** Internal — Do Not Distribute

---

## Ecosystem Map

```
/Users/tristanzh/agent/
├── web/                         # Node.js Express + React/Vite — Agent publishing hub (port 3000)
│   ├── app/                     # Static frontend assets per agent
│   ├── config/agents/           # Agent02/03/04 contract JSONs
│   ├── editor/                  # TypeScript/React visual editor (172 MB node_modules)
│   ├── kongagent-ui-framework/  # Shared CSS/JS framework
│   └── tests/                   # 13 .test.mjs files
│
├── Webstyle-editor/             # TypeScript/React/Vite — Visual web publishing editor (port 3001)
│   ├── src/                     # Near-identical to web/editor/src
│   ├── dist/                    # Built assets
│   └── tests/                   # 7 test files
│
├── Passenger-Vehicle-Intel/     # Python + Node.js — Vehicle market intelligence
│   ├── auto_intelligence_agent/ # Python sales collector, data processors, Feishu cards
│   ├── jlr-sales/               # Node.js JLR sales data (xlsx)
│   ├── hardware-supplier-dashboard/
│   ├── workflows/
│   │   ├── domestic-sales/      # DUPLICATE of auto_intelligence_agent/
│   │   ├── jlr-sales/           # DUPLICATE of top-level jlr-sales/
│   │   └── foreign-jv-china-watch/  # SKELETON — data only, no code
│   └── tests/                   # 3 test files
│
├── PetRelatedServices/          # Python Streamlit + Node.js — Pet care (turtles, fish, dogs)
│   │                            # ONLY PROJECT WITH .git REPO
│   ├── workflows/               # Agent03 adapters per pet domain
│   ├── venv/                    # 318 MB virtualenv
│   └── tests/                   # 19 test files
│
├── AnimalCareHub/               # SYMLINK → PetRelatedServices
├── DiamondTurtles/              # SYMLINK → PetRelatedServices
│
├── Assistant/                   # Coordination symlink hub
│   ├── Daily-Auto-Report/       # SYMLINK → Passenger-Vehicle-Intel
│   ├── JLR_data_statistic/      # SYMLINK → Passenger-Vehicle-Intel/jlr-sales
│   └── tools/                   # IDENTICAL to Codex-Ops/tools/
│
├── Codex-Ops/                   # Operations scripts
│   └── tools/                   # codex_session_audit.py, dependency_key_audit.py,
│                                # workspace_precheck.py
│
├── Medical/                     # Python PDF builders — supplement marketing posters
│   ├── .env.local               # ⚠️ LIVE API KEYS (see Blocker B1)
│   └── tests/                   # 8 test files
│
├── Stratigic-AGI-System/        # TypeScript strict mode — PPT generation, artifact versioning
│   ├── tsconfig.json            # strict: true, ES2022
│   └── tests/                   # 23 test files (unit + integration + regression)
│
├── Local-photo-model/           # Python FastAPI — Local photo search (Apple Photos, SQLite FTS)
│   ├── backend/                 # 16 Python files
│   ├── .cache/                  # 1.2 GB thumbnails
│   ├── data/limb_ark.sqlite3    # ~10 MB indexed photos
│   └── tests/                   # 16 test files
│
├── Material/                    # Reference PDFs/docs (no code)
├── docs/                        # Governance docs, model configs
├── .ai_skills/                  # handover_skill.md, vibe-clean scripts
├── _archive/                    # Archived Assistant weekly project (23 MB)
├── web_backup_before_remove_agent01_20260527_085749/  # 206 MB stale backup
│
└── Root loose files:            # .DS_Store, *.pptx, *.bak.md, *.bak.txt,
                                 # rollback_agent03_deepclean.sh, GLOBAL_*.md
```

### Cross-Project Dependencies (wired via `web/server.mjs`)

```
web (port 3000)
 ├── imports Passenger-Vehicle-Intel/workflows/domestic-sales/src/agent02-adapter.mjs
 ├── imports Passenger-Vehicle-Intel/workflows/jlr-sales/src/agent02-adapter.mjs
 ├── imports PetRelatedServices/workflows/diamondback-terrapin/src/agent03-adapter.mjs
 ├── imports PetRelatedServices/workflows/ornamental-fish/src/agent03-adapter.mjs
 ├── spawns Local-photo-model FastAPI backend (port 8004)
 ├── references Passenger-Vehicle-Intel/config/agent02-workflow-cards.json
 ├── references PetRelatedServices/config/agent03-workflow-cards.json
 └── mounts Passenger-Vehicle-Intel daily-auto workflow paths
```

---

## Blockers (致命缺陷)

### B1 — LIVE API KEYS EXPOSED ON DISK [CRITICAL]

**File:** `Medical/.env.local`

```
DEEPSEEK_API_KEY=<redacted>
PEXELS_API_KEY=<redacted>
PIXABAY_API_KEY=<redacted>
```

**Risk:** Three LIVE, unredacted API keys stored in plaintext on the local filesystem. Although `Medical/.gitignore` excludes `.env.*`, the file persists on disk. Any backup script, accidental `git add -A`, or malware scan that traverses this directory would exfiltrate production credentials.

**Action:** Rotate all three keys immediately with each provider. Delete `Medical/.env.local` and migrate secrets to macOS Keychain or a proper secrets manager. Replace with a `.env.example` template containing only placeholders.

---

### B2 — NO VERSION CONTROL FOR 6 OF 7 ACTIVE PROJECTS [CRITICAL]

Only `PetRelatedServices/` has a `.git` repository. The following mission-critical projects have ZERO git history:

| Project | Risk |
|---|---|
| `web/` | Central publishing hub — no change history |
| `Passenger-Vehicle-Intel/` | Vehicle intelligence data pipelines |
| `Medical/` | Marketing assets with API key exposure risk |
| `Local-photo-model/` | Photo search engine with 1.2 GB cache |
| `Webstyle-editor/` | Visual editor with 174 MB deps |
| `Stratigic-AGI-System/` | Artifact system — no rollback capability |

**Risk:** No rollback, no collaboration trail, no `git bisect` for regression hunting. A single `rm -rf` or bad refactor could destroy days of work.

**Action:** `git init` every active project. Create `.gitignore` files excluding `node_modules/`, `venv/`, `.cache/`, `.env.local`, `.DS_Store`, `*.pyc`, `__pycache__/`.

---

### B3 — 206 MB STALE WEB BACKUP [CRITICAL]

**Directory:** `web_backup_before_remove_agent01_20260527_085749/`

Full copy of `web/` from 2026-05-27, including a complete duplicate `node_modules/`. This directory has no documented purpose and silently consumes 206 MB of disk.

**Action:** Archive to `_archive/` or delete. If this was an intentional pre-change snapshot, move it to external storage.

---

### B4 — 1.2 GB THUMBNAIL CACHE IN PROJECT ROOT [CRITICAL]

**Directory:** `Local-photo-model/.cache/` (1.2 GB of generated thumbnails)

**Risk:** Generated data inside the project root. If `.git` is initialized without proper `.gitignore`, this could accidentally be staged. Also inflates backup sizes and confuses the boundary between source code and runtime state.

**Action:** Move `.cache/` outside the project tree (e.g., `~/.cache/local-photo-model/`) or ensure it is explicitly `gitignore`d and documented as ephemeral.

---

## Warnings (隐患代码)

### W1 — Hardcoded Stale Report Date

**Files:**
- `Passenger-Vehicle-Intel/auto_intelligence_agent/main.py:34` — `REPORT_DATE = "2026-05-19"`
- `Passenger-Vehicle-Intel/workflows/domestic-sales/auto_intelligence_agent/main.py:34` (duplicate) — `REPORT_DATE = "2026-05-19"`

**Risk:** The sales collector will perpetually operate on a stale date. Every report generation uses a fixed historical date instead of `datetime.now()`.

**Action:** Replace with `datetime.date.today().isoformat()` or accept `--report-date` as a CLI argument.

---

### W2 — Hardcoded Host-Specific Paths in Production Server

**File:** `web/server.mjs`

| Line | Value |
|---|---|
| 51 | `/Users/tristanzh/Pictures/Photos Library.photoslibrary/originals` |
| 65 | `/Users/tristanzh/.local/node-v24.15.0-darwin-arm64/bin` |
| 66 | `/Applications/Codex.app/Contents/Resources/codex` |
| 242 | `/Users/tristanzh/Pictures/Photos Library.photoslibrary/originals` |

**Risk:** These absolute paths bind the entire publishing hub to one machine, one user, and one filesystem layout. Any account migration, machine change, or CI container would irrecoverably break the server.

**Action:** Extract all host-specific paths into a `.env` file or `config/server.json` and reference via `process.env` or a config loader with sensible defaults.

---

### W3 — Pinned to Unstable Node.js Version

**File:** `web/server.mjs:65` — `v24.15.0` (pre-release/unstable channel)

**Risk:** Node v24 is not an LTS release (v22 LTS and v24 are active development lines as of 2026). Pinning to a specific pre-release path means the server could break on any Node patch update.

**Action:** Use `nvm` or `asdf` for version management. Specify a version range in `.nvmrc` or `package.json.engines`. Do not hardcode binary paths.

---

### W4 — Mass Code Duplication (6 Instances)

| Duplicate Set | Files | Severity |
|---|---|---|
| Sales agent code | `auto_intelligence_agent/` ↔ `workflows/domestic-sales/auto_intelligence_agent/` | High |
| JLR sales code | `jlr-sales/` ↔ `workflows/jlr-sales/` | High |
| Visual editor source | `web/editor/src/` ↔ `Webstyle-editor/src/` | High |
| Ops tools | `Assistant/tools/` ↔ `Codex-Ops/tools/` | Medium |
| Agent03 adapters | `PetRelatedServices/` × 2 symlinks | Low (symlinks, but confusing) |

**Risk:** Bug fixes applied in one copy are silently missing in the other. Divergent evolution creates subtle incompatibilities. Increases maintenance burden by 2–3× across duplicated modules.

**Action:** Establish a single source of truth for each module. Remove duplicates and use symlinks or package references. Decide canonically which editor (`web/editor/` vs `Webstyle-editor/`) is authoritative.

---

### W5 — Triple-Symlink Identity Confusion

`AnimalCareHub/` and `DiamondTurtles/` are both symlinks to `PetRelatedServices/`. Three names resolve to one project on disk.

**Risk:** Logs, configs, and documentation referencing different names create cognitive overhead. A future script or developer could assume `AnimalCareHub` is a separate project with its own state.

**Action:** Either (a) remove the symlinks and use `PetRelatedServices` as the sole canonical name, or (b) document explicitly in `AGENTS.md` why each alias exists and what conceptual boundary it represents.

---

### W6 — `any` Type Escapes in Strict TypeScript Project

**File:** `Stratigic-AGI-System/strategic-artifact-system/src/engines/ppt_generator_engine/slide_renderer.ts:55-57`

```typescript
addImage: (options: any) => any;
addText: (text: string, options: any) => any;
addShape: (shape: any, options: any) => any;
```

**Risk:** Despite `tsconfig.json` having `strict: true`, these `any` types create a gaping hole in the type system for all PPTX rendering operations. Any invalid parameter silently passes through.

**Action:** Define proper interfaces for PPTX library options (`PptxImageOptions`, `PptxTextOptions`, `PptxShapeOptions`) or import types from the upstream library if available.

---

### W7 — Zero Linting/Formatting Configuration

Not a single `.eslintrc`, `eslint.config.*`, `.prettierrc`, `ruff.toml`, `pyproject.toml`, or `.flake8` configuration file exists anywhere in the ecosystem (outside `node_modules/`).

**Risk:** No consistent code style across 7 active projects. Mixed indentation, quote styles, import ordering, and naming conventions will accumulate. Prevents automated quality gates.

**Action:** Add `eslint.config.mjs` + `.prettierrc` for TypeScript/JavaScript projects. Add `ruff.toml` for Python projects. Install `pre-commit` with basic checks (trailing whitespace, YAML/JSON validation, no secrets).

---

### W8 — No CI/CD Pipeline

No `.github/workflows/`, `Jenkinsfile`, or any CI configuration exists. All 7 projects rely entirely on manual local testing.

**Risk:** Tests exist (~106 test files total) but have no automated execution. Regressions are only caught when a developer manually runs tests — which may not happen.

**Action:** Create `.github/workflows/test.yml` that runs `npm test` / `pytest` per project, plus lint and type-check steps.

---

### W9 — Skeleton Workflow (foreign-jv-china-watch)

**Directory:** `Passenger-Vehicle-Intel/workflows/foreign-jv-china-watch/`

This workflow has a config entry in `agent02-workflow-cards.json` but contains only a `data/` subdirectory with no source code or adapter logic.

**Risk:** The config entry suggests this is an active workflow, but it cannot produce any output. Either a forgotten placeholder or a broken feature that silently fails.

**Action:** Either implement the workflow or change its `"status"` to `"planned"` and document the roadmap.

---

### W10 — Monolithic PDF Build Scripts

**File:** `Medical/build_cardio_metabolic_poster.py` (218 lines) and similar scripts.

Each Medical build script is a single-file monolith mixing config, color handling, text rendering, CJK font wrapping, rectangle calculation, and PDF I/O. Every new poster type copy-pastes the same boilerplate.

**Risk:** Fixes to shared rendering logic require manual propagation across all scripts. The probability of missing one is high.

**Action:** Extract a shared `PosterBuilder` or `PDFLayoutEngine` base class. Each poster script should only specify content and layout parameters.

---

### W11 — 462 MB Duplicated Node Modules

- `web/editor/node_modules/`: 172 MB
- `Webstyle-editor/node_modules/`: 174 MB
- `Stratigic-AGI-System/strategic-artifact-system/node_modules/`: ~116 MB (estimated)

**Risk:** Three separate npm installs with overlapping dependencies waste ~300+ MB of disk.

**Action:** Consider `pnpm` workspaces or a shared monorepo tool (Turborepo, Nx) to deduplicate.

---

### W12 — Root Loose Files Without Ownership

```
.DS_Store
2025 Automotive China.pptx
AGENTS_20260530.md.bak.md
AGENTS.md.bak_20260530171421
GLOBAL_ACCOUNT_EXIT_UPDATE_PROMPT.bak.txt
GLOBAL_ACCOUNT_SWITCH_PROMPT.md
rollback_agent03_deepclean.sh
```

**Risk:** Backup files and stale documents at repo root have no clear ownership. They pollute the root namespace and could be misinterpreted as active configuration.

**Action:** Move backup files into `_archive/`. Move presentation files into `Material/`. Delete or archive obsolete `.bak` files.

---

## Suggestions (优化建议)

### S1 — Rotate and Secure API Keys (Related: B1)

Revoke all three keys in `Medical/.env.local`. Delete the file. Use macOS Keychain (`security` CLI) or `pass` for local secret storage.

### S2 — Git-Initialize All Projects (Related: B2)

```bash
for dir in web Passenger-Vehicle-Intel Medical Local-photo-model Webstyle-editor Stratigic-AGI-System; do
  (cd "$dir" && git init && git add -A && git commit -m "Initial commit: ecosystem audit baseline 2026-06-01")
done
```

### S3 — Archive Stale Backup (Related: B3)

```bash
mv web_backup_before_remove_agent01_20260527_085749 _archive/
```

### S4 — Move .cache Outside Project Tree (Related: B4)

```bash
mkdir -p ~/.cache/local-photo-model
mv Local-photo-model/.cache/* ~/.cache/local-photo-model/
# Update backend to use new path
```

### S5 — Add Linting Across the Board (Related: W7)

- **TypeScript/JS:** `npm install -D eslint @eslint/js prettier eslint-config-prettier` + create `eslint.config.mjs` and `.prettierrc` in each Node project root.
- **Python:** `pip install ruff` + create `ruff.toml` in each Python project root.
- **Pre-commit:** Install `pre-commit` globally and add `.pre-commit-config.yaml` at repo root with hooks for trailing whitespace, end-of-file fixer, YAML/JSON validation, and `detect-private-key`.

### S6 — Extract Shared Configuration from web/server.mjs (Related: W2)

Create `web/.env`:
```
PHOTO_LIBRARY_ROOT=/Users/tristanzh/Pictures/Photos Library.photoslibrary/originals
NODE_BIN_DIR=/Users/tristanzh/.local/node-v24.15.0-darwin-arm64/bin
CODEX_CLI_PATH=/Applications/Codex.app/Contents/Resources/codex
AGENT04_PORT=8004
```
Reference via `process.env.PHOTO_LIBRARY_ROOT`, etc., with fallback defaults.

### S7 — De-duplicate Code (Related: W4)

1. **Editor:** Decide canonical editor (`web/editor/` or `Webstyle-editor/`). Remove the other.
2. **Sales agent:** Keep only top-level `auto_intelligence_agent/`. Remove `workflows/domestic-sales/auto_intelligence_agent/`.
3. **JLR sales:** Keep only top-level `jlr-sales/`. Remove `workflows/jlr-sales/`.
4. **Ops tools:** Keep `Codex-Ops/tools/` as canonical. Symlink `Assistant/tools/` → `Codex-Ops/tools/`.

### S8 — Add CI/CD Pipeline (Related: W8)

Minimal `.github/workflows/test.yml`:
```yaml
jobs:
  test-node:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [web/editor, Webstyle-editor, Stratigic-AGI-System]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci && npm test
        working-directory: ${{ matrix.project }}

  test-python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [Passenger-Vehicle-Intel, Medical, Local-photo-model, PetRelatedServices]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt && pytest
        working-directory: ${{ matrix.project }}
```

### S9 — Implement or Document foreign-jv-china-watch (Related: W9)

Either build the workflow adapter and unset `"sendEnabled": false` in the config, or add a `"status": "planned"` field and document the roadmap in a `README.md` within the workflow directory.

### S10 — Consider Monorepo Tooling (Related: W11)

Evaluate `pnpm workspaces` or Turborepo to unify the three separate `node_modules` trees. This alone saves ~300 MB of disk and eliminates dependency version drift between `web/editor` and `Webstyle-editor`.

### S11 — Clean Up Root Loose Files (Related: W12)

```bash
mv AGENTS_20260530.md.bak.md _archive/
mv AGENTS.md.bak_20260530171421 _archive/
mv GLOBAL_ACCOUNT_EXIT_UPDATE_PROMPT.bak.txt _archive/
mv "2025 Automotive China.pptx" Material/
rm .DS_Store  # add to global .gitignore
```

### S12 — Add Cross-Project Dependency Documentation

The implicit dependency graph in `web/server.mjs` is undocumented. Add a `DEPENDENCIES.md` or a section in `AGENTS.md` that explicitly maps:
- Which agent imports which workflow adapter
- Which ports are reserved per service
- Which projects must be running for `web` to function

---

## Vibe Clean Scores

| Project | Score | Summary |
|---|---|---|
| **Stratigic-AGI-System** | **7/10** | Strict TS, 23 tests (unit/integration/regression), well-organized scripts. Deducted for `any` escapes and no lint config files. |
| **Local-photo-model** | **7/10** | Excellent README, modular backend, 16 tests, clean env config. Deducted for 1.2 GB cache in project dir and no git. |
| **Webstyle-editor** | **6/10** | Strict TS, Vite, Zod validation, 7 tests. Deducted for `console.log` in config, near-duplication with web/editor, no git. |
| **Medical** | **5/10** | 8 comprehensive tests, good `.env.example` pattern. Heavy deductions for LIVE API KEYS and monolithic 200+ line scripts. |
| **web** | **5/10** | 13-test suite covering agents/contracts/themes. Deducted for 7+ hardcoded paths, cross-project import tangle, no git. |
| **PetRelatedServices** | **5/10** | Only project with git, 19 tests, organized workflows. Deducted for triple-symlink confusion and 318 MB venv. |
| **Passenger-Vehicle-Intel** | **4/10** | Solid intelligence functionality. Deducted for hardcoded 2026-05-19, 2× code duplication, skeleton workflow, no git. |
| **Codex-Ops** | **4/10** | Focused tools. Deducted for 100% duplication with Assistant/tools, no tests, no git. |
| **Assistant** | **3/10** | Primarily a symlink hub. Useful as cross-reference but not a standalone project. |

---

## Ecosystem Health Summary

| Metric | Status |
|---|---|
| Total active projects | 7 |
| Projects with git | 1 of 7 |
| Projects with CI/CD | 0 of 7 |
| Projects with lint config | 0 of 7 |
| Total test files | ~106 |
| API keys exposed on disk | 3 (Medical) |
| Hardcoded dates found | 2 locations |
| Hardcoded host paths | 7 in web/server.mjs |
| Symlink aliases | 4 |
| Code duplication instances | 6 |
| Total node_modules disk | ~462 MB (3 separate installs) |
| Stale backups | 206 MB |
| Largest runtime cache | 1.2 GB (.cache/thumbnails) |

---

## Immediate Priority Action Queue

| Priority | Item | Effort | Impact |
|---|---|---|---|
| **P0** | Rotate `Medical/.env.local` API keys (B1) | 5 min | Prevents credential leak |
| **P0** | `git init` all active projects (B2) | 10 min | Enables rollback & history |
| **P0** | Archive 206 MB web backup (B3) | 1 min | Recovers disk space |
| **P1** | Move .cache/ out of project tree (B4) | 15 min | Separates source from runtime |
| **P1** | Fix hardcoded REPORT_DATE (W1) | 5 min | Prevents stale data |
| **P1** | Extract hardcoded paths from server.mjs (W2) | 30 min | Enables portability |
| **P1** | De-duplicate sales agent and jlr-sales (W4) | 20 min | Reduces maintenance burden |
| **P2** | Add eslint/ruff configs (W7) | 30 min | Enforces code quality |
| **P2** | Add CI/CD pipeline (W8) | 1 hr | Automates testing |
| **P2** | Clean root loose files (W12) | 5 min | Declutters workspace |
| **P3** | Define PPTX types (W6) | 1 hr | Closes type safety hole |
| **P3** | Monorepo evaluation (S10) | 2 hr | Saves 300+ MB |
| **P3** | Cross-project dependency doc (S12) | 30 min | Improves onboarding |

---

*This white paper is a living document. Re-audit after each major release cycle or quarterly, whichever comes first.*
