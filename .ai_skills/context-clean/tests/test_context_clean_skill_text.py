#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
PROTOCOL = Path("/Users/tristanzh/agent/web/docs/vibe-clean-protocol.md")


class ContextCleanSkillTextTests(unittest.TestCase):
    def test_context_clean_has_exact_trigger_and_protocol_boundary(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("name: context-clean", text)
        self.assertIn("执行context clean", text)
        self.assertIn(str(PROTOCOL), text)
        self.assertIn("不删除", text)
        self.assertIn("不移动", text)
        self.assertIn("不归档", text)
        self.assertIn("pure_context.md", text)
        self.assertNotIn("确认执行清除指令", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
