#!/usr/bin/env python3
"""
Contract tests for the future Vibe Clean garbage-collection helper.

These tests intentionally target a script that does not exist yet:
../scripts/vibe_clean_gc.py

Expected future interface:
  python3 scripts/vibe_clean_gc.py --root <dir> --today YYYYMMDD --mode dry-run --format json
  python3 scripts/vibe_clean_gc.py --root <dir> --today YYYYMMDD --mode dry-run --format markdown
  python3 scripts/vibe_clean_gc.py --root <dir> --today YYYYMMDD --mode execute --confirm 确认执行清除指令

No skill body is tested here. This file only defines filesystem behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TODAY = "20260531"
CONFIRMATION = "确认执行清除指令"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "vibe_clean_gc.py"


class VibeCleanContractTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-clean-contract-")
        self.root = Path(self.tmp.name)
        self._seed_workspace(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_candidate(self, *args: str, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(SCRIPT), "--root", str(self.root), "--today", TODAY, *args]
        result = subprocess.run(cmd, text=True, capture_output=True)
        if expect_success and result.returncode != 0:
            self.fail(
                "candidate command failed\n"
                f"cmd: {' '.join(cmd)}\n"
                f"returncode: {result.returncode}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return result

    def test_dry_run_reports_recursive_delete_and_archive_targets_without_mutating_files(self) -> None:
        before = self._snapshot(self.root)

        result = self.run_candidate("--mode", "dry-run", "--format", "json")
        report = json.loads(result.stdout)

        self.assertEqual(
            sorted(report["delete"]),
            sorted(
                [
                    ".DS_Store",
                    ".pytest_cache",
                    ".vitest",
                    "debug_trace.log",
                    "deepseek_audit_feedback_r1.md",
                    "deepseek_audit_feedback_r2.md",
                    "module/__pycache__",
                    "module/cache.pyc",
                    "nested/conflict.bak",
                    "nested/node_modules/.cache",
                    "nested/scratch.swp",
                    "nested/temp_probe.py",
                    "nested/test_draft_case.md",
                    "nested/tilde_backup~",
                    "tracked_conflict.bak",
                ]
            ),
        )
        self.assertEqual(
            sorted(report["archive"]),
            sorted(
                [
                    "HANDOVER_web_20260530.md",
                    "nested/HANDOVER_agent_20260529.md",
                ]
            ),
        )
        self.assertEqual(self._snapshot(self.root), before, "dry-run must not mutate the workspace")

    def test_markdown_dry_run_uses_required_review_format_and_confirmation_phrase(self) -> None:
        result = self.run_candidate("--mode", "dry-run", "--format", "markdown")

        self.assertIn("Vibe Clean 预演扫描报告", result.stdout)
        self.assertIn("拟物理删除 (Delete)", result.stdout)
        self.assertIn("拟移入归档 (Move to _archive_legacy/)", result.stdout)
        self.assertIn(CONFIRMATION, result.stdout)
        self.assertIn(".pytest_cache", result.stdout)
        self.assertIn("deepseek_audit_feedback_r2.md", result.stdout)
        self.assertIn("nested/conflict.bak", result.stdout)
        self.assertNotIn("nested/pure_context.md", result.stdout)
        self.assertNotIn("pure_context.md", result.stdout)

    def test_execute_rejects_all_confirmation_phrases_except_exact_required_phrase(self) -> None:
        before = self._snapshot(self.root)

        for phrase in ["确认执行", "执行清理", "确认执行清除", "ok", ""]:
            result = self.run_candidate(
                "--mode",
                "execute",
                "--confirm",
                phrase,
                expect_success=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self._snapshot(self.root), before, f"phrase should not execute: {phrase!r}")

    def test_execute_deletes_blacklisted_files_and_archives_state_snapshots_after_exact_confirmation(self) -> None:
        self.run_candidate("--mode", "execute", "--confirm", CONFIRMATION)

        for relative_path in [
            ".DS_Store",
            ".pytest_cache",
            ".vitest",
            "debug_trace.log",
            "deepseek_audit_feedback_r1.md",
            "deepseek_audit_feedback_r2.md",
            "module/__pycache__",
            "module/cache.pyc",
            "nested/conflict.bak",
            "nested/node_modules/.cache",
            "nested/scratch.swp",
            "nested/temp_probe.py",
            "nested/test_draft_case.md",
            "nested/tilde_backup~",
            "tracked_conflict.bak",
        ]:
            self.assertFalse((self.root / relative_path).exists(), relative_path)

        for relative_path in [
            "HANDOVER_web_20260530.md",
            "nested/HANDOVER_agent_20260529.md",
        ]:
            self.assertFalse((self.root / relative_path).exists(), relative_path)
            self.assertTrue((self.root / "_archive_legacy" / relative_path).exists(), relative_path)

        for relative_path in [
            "nested/pure_context.md",
            "pure_context.md",
        ]:
            self.assertTrue((self.root / relative_path).exists(), relative_path)
            self.assertFalse((self.root / "_archive_legacy" / relative_path).exists(), relative_path)

    def test_execute_preserves_immune_paths_and_non_blacklisted_business_files(self) -> None:
        self.run_candidate("--mode", "execute", "--confirm", CONFIRMATION)

        for relative_path in [
            ".git/config",
            "_archive_legacy/HANDOVER_old_already_archived_20260501.md",
            ".ai_skills/handover_skill.md",
            ".ai_skills/vibe_clean_skill.md",
            ".env",
            ".env.local",
            ".venv/lib/python3.11/site-packages/package/__pycache__/module.pyc",
            "HANDOVER_current_20260531.md",
            "audit_artifact_cleanup_catalog.md",
            "deepseek_audit_feedback_r3.md",
            "node_modules/left-pad/index.js",
            "node_modules/left-pad/.DS_Store",
            "src/core_business.py",
            "venv/lib/python3.11/site-packages/package/__pycache__/module.pyc",
            "nested/notes.md",
        ]:
            self.assertTrue((self.root / relative_path).exists(), relative_path)

    def test_single_deepseek_audit_round_is_preserved_as_current_output(self) -> None:
        solo_root = self.root / "solo_audit"
        solo_root.mkdir()
        (solo_root / "deepseek_audit_feedback_r3.md").write_text("only round\n", encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(solo_root),
                "--today",
                TODAY,
                "--mode",
                "dry-run",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["delete"], [])
        self.assertTrue((solo_root / "deepseek_audit_feedback_r3.md").exists())

    def test_execute_unlinks_delete_target_symlink_without_deleting_link_target(self) -> None:
        symlink_root = self.root / "symlink_case"
        cache_parent = symlink_root / "node_modules"
        cache_parent.mkdir(parents=True)
        target_dir = symlink_root / "protected_cache_target"
        target_dir.mkdir()
        (target_dir / "keep.txt").write_text("do not delete target\n", encoding="utf-8")
        (cache_parent / ".cache").symlink_to(target_dir, target_is_directory=True)

        dry_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(symlink_root),
                "--today",
                TODAY,
                "--mode",
                "dry-run",
                "--format",
                "json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertEqual(json.loads(dry_run.stdout)["delete"], ["node_modules/.cache"])

        execute = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(symlink_root),
                "--today",
                TODAY,
                "--mode",
                "execute",
                "--confirm",
                CONFIRMATION,
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(execute.returncode, 0, execute.stderr)
        self.assertFalse((cache_parent / ".cache").exists())
        self.assertTrue((target_dir / "keep.txt").exists())

    def _seed_workspace(self, root: Path) -> None:
        files = {
            ".DS_Store": "finder metadata\n",
            ".env": "SECRET=keep\n",
            ".env.local": "SECRET=keep\n",
            ".pytest_cache/CACHEDIR.TAG": "pytest cache\n",
            ".venv/lib/python3.11/site-packages/package/__pycache__/module.pyc": "venv bytecode\n",
            ".vitest/results.json": "{}\n",
            "audit_artifact_cleanup_catalog.md": "protected catalog\n",
            "deepseek_audit_feedback_r1.md": "old audit round\n",
            "deepseek_audit_feedback_r2.md": "old audit round\n",
            "deepseek_audit_feedback_r3.md": "current audit round\n",
            "node_modules/left-pad/index.js": "module code\n",
            "node_modules/left-pad/.DS_Store": "must stay under immune node_modules\n",
            "tracked_conflict.bak": "tracked bak should still be deleted after confirmation\n",
            "debug_trace.log": "temporary debug log\n",
            "pure_context.md": "legacy global context\n",
            "HANDOVER_web_20260530.md": "old state snapshot\n",
            "HANDOVER_current_20260531.md": "today state snapshot\n",
            "src/core_business.py": "print('business logic')\n",
            "module/__pycache__/core.cpython-311.pyc": "bytecode\n",
            "module/cache.pyc": "bytecode\n",
            "nested/conflict.bak": "nested bak\n",
            "nested/node_modules/.cache/tool/cache.json": "{}\n",
            "nested/scratch.swp": "swap\n",
            "nested/temp_probe.py": "temporary scaffold\n",
            "nested/test_draft_case.md": "draft test junk\n",
            "nested/tilde_backup~": "editor backup\n",
            "nested/pure_context.md": "nested legacy context\n",
            "nested/HANDOVER_agent_20260529.md": "nested old handover\n",
            "nested/notes.md": "normal project note\n",
            "venv/lib/python3.11/site-packages/package/__pycache__/module.pyc": "venv bytecode\n",
            ".ai_skills/handover_skill.md": "protected handover skill\n",
            ".ai_skills/vibe_clean_skill.md": "protected vibe clean skill\n",
            "_archive_legacy/HANDOVER_old_already_archived_20260501.md": "already archived\n",
            "_archive_legacy/stale.bak": "already archived bak should not be touched\n",
        }
        for relative_path, content in files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        git_dir = root / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
        (git_dir / "internal.bak").write_text("must not be scanned\n", encoding="utf-8")

    def _snapshot(self, root: Path) -> list[str]:
        paths: list[str] = []
        for current_root, dirnames, filenames in os.walk(root):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                path = Path(current_root) / filename
                paths.append(path.relative_to(root).as_posix())
        return sorted(paths)


if __name__ == "__main__":
    unittest.main(verbosity=2)
