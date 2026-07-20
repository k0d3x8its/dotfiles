#!/usr/bin/env python3
"""Drift-guard: SKILL.md's Dispatch section names personas by path in prose only — nothing else pins that the files exist or still carry a trigger: line."""

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent / "claude" / ".claude" / "skills" / "code-crit"
SKILL_MD = SKILL_DIR / "SKILL.md"
PERSONAS_DIR = SKILL_DIR / "personas"

ALWAYS_ON = [
    "CORRECTNESS.md",
    "MAINTAINABILITY.md",
    "TESTING.md",
    "PROJECT-STANDARDS.md",
    "SPEC-COMPLIANCE.md",
]

CONDITIONAL = [
    "SECURITY.md",
    "PERFORMANCE.md",
    "RELIABILITY.md",
    "API-CONTRACT.md",
    "DATA-MIGRATION.md",
    "ADVERSARIAL.md",
    "AGENT-NATIVE.md",
]


class DispatchDriftGuardTests(unittest.TestCase):
    def test_skill_md_names_exactly_the_expected_personas(self) -> None:
        text = SKILL_MD.read_text()
        named = set(re.findall(r"personas/([A-Z-]+\.md)", text))
        self.assertEqual(named, set(ALWAYS_ON) | set(CONDITIONAL))

    def test_always_on_persona_files_exist(self) -> None:
        for name in ALWAYS_ON:
            self.assertTrue(
                (PERSONAS_DIR / name).is_file(), f"missing always-on persona: {name}"
            )

    def test_conditional_persona_files_exist_and_carry_trigger_line(self) -> None:
        for name in CONDITIONAL:
            path = PERSONAS_DIR / name
            self.assertTrue(path.is_file(), f"missing conditional persona: {name}")
            text = path.read_text()
            self.assertRegex(
                text,
                r"\*\*trigger:\*\*",
                f"{name} has no trigger: line — can never be selected",
            )


if __name__ == "__main__":
    unittest.main()
