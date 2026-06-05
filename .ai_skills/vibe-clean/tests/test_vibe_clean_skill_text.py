#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class VibeCleanSkillTextTests(unittest.TestCase):
    def test_dry_run_trigger_is_exact_unique_command(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("唯一 dry-run 触发命令：`执行vibe clean`", text)
        self.assertIn("任何其他近似表达都不得触发 Vibe Clean 文件 GC dry-run", text)

        forbidden_trigger_lines = [
            "触发词：vibe clean",
            "执行清理",
            "环境清理",
            "上下文太脏",
            "收工前清理",
            "清理工作区",
            "执行vibe gc dry-run",
        ]
        for forbidden in forbidden_trigger_lines:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
