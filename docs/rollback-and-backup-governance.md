# Rollback and Backup Governance

Date: 2026-06-01

## Scope

This document records the retained local rollback and backup artifacts found during the DeepSeek R2 remediation pass.

## Policy

- `rollback_*.sh` scripts are local recovery utilities. Keep them only when they point to a clear project boundary or legacy cleanup path.
- `*.bak*` files are temporary local backup artifacts. They must be ignored by project repositories and must not enter baseline commits.
- `_archive_legacy/` is local historical context. It is excluded from project repository baselines unless TZ explicitly asks to preserve a specific file as source.
- `_archive/` at `/Users/tristanzh/agent/_archive` is ecosystem-level historical storage, not a source package.

## Retained Rollback Scripts

| Path | Boundary | Purpose |
|---|---|---|
| `/Users/tristanzh/agent/Codex-Ops/rollback_legacy.sh` | Codex ops | Legacy local rollback helper retained as an ops artifact. |
| `/Users/tristanzh/agent/Local-photo-model/rollback_legacy.sh` | Local photo model | Legacy rollback helper retained for Agent04 local photo workspace recovery. |
| `/Users/tristanzh/agent/Passenger-Vehicle-Intel/rollback_pvi.sh` | Passenger vehicle intel | Project-level rollback helper for passenger vehicle workflow cleanup. |
| `/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales/rollback_jlr.sh` | JLR child workflow | Child-project rollback helper for JLR sales workflow cleanup. |
| `/Users/tristanzh/agent/PetRelatedServices/rollback_agent03.sh` | Pet related services | Agent03 rollback helper retained because this repository already has history and active user changes. |
| `/Users/tristanzh/agent/Stratigic-AGI-System/rollback_stratigic.sh` | Strategic AGI system | Legacy rollback helper retained for strategic artifact system cleanup. |
| `/Users/tristanzh/agent/web/rollback_legacy.sh` | Web publishing surface | Legacy rollback helper retained for shared web publishing recovery. |

## Archived Rollback Scripts

| Path | Reason |
|---|---|
| `/Users/tristanzh/agent/_archive/root_loose_20260601/rollback_agent03_deepclean.sh` | Historical root loose-file cleanup artifact. Not part of a project repository baseline. |

## Baseline Commit Rule

Before an initial baseline commit in any empty project repository:

1. Run `git status --short --ignored`.
2. Run `git add .`.
3. Run `git status --short`.
4. Run `git ls-files`.
5. Abort if any `.env`, `venv/`, `node_modules/`, `.cache/`, `.pytest_cache/`, generated database, log, or `*.bak*` file appears in tracked output.

