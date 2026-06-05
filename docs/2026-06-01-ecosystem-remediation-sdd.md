# Ecosystem Remediation SDD

Date: 2026-06-01

## Scope

This pass addresses the verified audit findings that can be fixed locally without deleting source history or requiring external provider access.

## Interfaces

### Passenger-Vehicle-Intel report date

- `auto_intelligence_agent.main.get_report_date(argv=None, today=None) -> str`
- CLI flag: `--report-date YYYY-MM-DD`
- Environment fallback: `REPORT_DATE=YYYY-MM-DD`
- Default: current local date when neither CLI nor environment is supplied
- Invalid date format raises `ValueError`

### Local-photo-model runtime cache

- `backend.config.LIMB_THUMBNAIL_DIR` exposes the default thumbnail path.
- Default thumbnail path moves from project `.cache/thumbnails` to `~/.cache/local-photo-model/thumbnails`.
- `LIMB_THUMBNAIL_DIR` environment variable remains the override for local deployments.

### Web publishing server host config

- Host-specific paths are read from environment variables:
  - `LIMB_PHOTO_ROOT`
  - `LIMB_PHOTO_ROOT_ALIASES`
  - `CODEX_NODE_BIN_DIR`
  - `CODEX_CLI_PATH`
- Existing absolute values are retained only as local fallback defaults.

### Strategic artifact PPT renderer types

- `slide_renderer.ts` replaces broad `any` slide method parameters with minimal structural types used by the renderer.

## Non-code Operations

- Secret file: remove `Medical/.env.local` after recording that external rotation is still required.
- Audit document: redact literal key values and preserve variable names.
- Stale backup: move the web backup directory under `_archive/`.
- Root loose files: move stale backups and presentation into `_archive/` or `Material/` without deleting.

## Tests

- Passenger-Vehicle-Intel: date source precedence and validation tests.
- Local-photo-model: runtime config test asserts the default thumbnail dir is outside the project tree.
- Web: service test asserts server code reads host-specific path settings from environment variables.
- Strategic artifact system: TypeScript compile verifies PPT renderer structural types.

## Round 2 Hardening Interfaces

### Repository hygiene

- Each project repository owns a `.gitignore` that excludes runtime and generated state:
  - local env files and secrets;
  - virtual environments and package installs;
  - cache, test cache, build, coverage, logs, generated databases;
  - local backup files (`*.bak*`) and `_archive_legacy/`.
- Initial commits must be created only after `git status --short` and `git ls-files` show no sensitive or heavyweight runtime artifacts.

### Web default user identity

- `web/server.mjs` reads the default Lark user open_id from `LARK_DEFAULT_USER_ID`.
- The server must not embed TZ's concrete open_id in source.
- If the variable is unset, the default is an empty string and downstream behavior must handle the absence explicitly.

### Local-photo-model frontend tests

- Tests validate current product behavior rather than brittle selector ordering across unrelated theme overrides.
- Existing assertions may be updated only after confirming the target behavior is still represented in the implementation.

### Rollback and backup governance

- Rollback scripts are retained as local recovery utilities.
- `.bak*` files are excluded from baseline commits.
- `_archive_legacy/` is treated as local historical context, not project source.

## Phase 2 Quality Gate Interfaces

### Project check scripts

- Node projects expose `npm run check` where practical.
- `check` must run at least syntax/type validation plus the project test suite.
- Placeholder lint scripts such as `echo "lint not implemented yet"` are invalid.

### Python quality config

- Python projects expose `pyproject.toml`.
- `pyproject.toml` includes:
  - `[tool.pytest.ini_options]`
  - `[tool.ruff]`
  - `[tool.ruff.lint]` with `E`, `F`, and `W` selected.

### Ecosystem gate

- `Codex-Ops/tools/ecosystem_quality_gate.py` is the machine-readable ecosystem gate.
- `--mode audit` checks repository hygiene and forbidden tracked runtime artifacts.
- `--mode verify` additionally runs project-specific verification commands.
- `--project <name>` scopes the gate to one repository; single-repo CI must use this mode because sibling repositories are not present after checkout.
- Passenger-Vehicle-Intel root and `workflows/domestic-sales` pytest files are run in separate processes because they intentionally share a basename.

### CI

- Each active repository should have a project-local `.github/workflows/quality.yml` when feasible.
- CI must run the same local project check/test command that developers can run manually.

## Phase 3 Canonical Map Interfaces

### Canonical map

- `Codex-Ops/config/ecosystem_canonical_map.json` is the machine-readable duplicate-boundary registry.
- Each entry declares:
  - `canonical`: the source-of-truth path for business ownership.
  - `copies`: mirrored, embedded, or publishing-adapter paths that currently remain active.
  - `policy`: how future edits flow between canonical and copied paths.
  - `removal_allowed`: `false` unless a concrete migration plan exists.
- Phase 3 does not delete duplicate directories. Deletion is allowed only after the map and tests identify a migration plan that preserves active routes, adapters, and user worktree changes.

### Audit rule

- Full local ecosystem audit validates canonical map structure and path existence.
- Project-scoped CI must not require sibling repositories to exist, so it does not enforce full canonical path existence.
