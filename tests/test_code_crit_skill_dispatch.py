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


class ModeDispatchDriftGuardTests(unittest.TestCase):
    """Goal 28: dual-mode dispatch (fast default / thorough opt-in) — pin the shape so a
    future SKILL.md edit can't silently collapse back to single-mode or invert the default.
    """

    def setUp(self) -> None:
        self.text = SKILL_MD.read_text()

    def test_mode_detection_order_is_arg_then_keyword_then_default_fast(self) -> None:
        arg_pos = self.text.find("Explicit arg")
        keyword_pos = self.text.find("Natural-language keyword")
        default_pos = self.text.find("**Default**: **fast**")
        self.assertGreater(arg_pos, -1, "no explicit-arg detection step documented")
        self.assertGreater(keyword_pos, -1, "no NL-keyword detection step documented")
        self.assertGreater(default_pos, -1, "no explicit fast default documented")
        self.assertLess(
            arg_pos, keyword_pos, "arg detection must be checked before keyword"
        )
        self.assertLess(
            keyword_pos, default_pos, "keyword detection must be checked before default"
        )

    def test_fast_mode_sonnet_tier_is_one_mega_spawn(self) -> None:
        self.assertRegex(
            self.text,
            r"fast mode — one Agent mega-spawn call",
            "fast mode's Sonnet-tier dispatch is no longer documented as one mega-spawn",
        )

    def test_thorough_mode_sonnet_tier_is_isolated_per_persona(self) -> None:
        self.assertRegex(
            self.text,
            r"thorough mode — one isolated Agent spawn per matched persona",
            "thorough mode's Sonnet-tier dispatch is no longer documented as isolated-per-persona",
        )

    def test_opus_frontline_isolated_in_both_modes(self) -> None:
        self.assertRegex(
            self.text,
            r"Opus frontline \(4 separate isolated spawns, both modes, identical\)",
            "Opus frontline must stay isolated in both modes — this is the "
            "miss-is-unrecoverable tier and must never be batched",
        )

    def test_canonical_record_normalization_documented(self) -> None:
        self.assertIn(
            "(file, line, title, persona, severity, confidence, fix)",
            self.text,
            "canonical-record normalization (Opus issue-field + Sonnet mega JSON "
            "reconciled before grouping) must be spelled out, not left implicit",
        )

    def test_fast_mode_failure_marker_is_not_hardcoded_to_eight(self) -> None:
        self.assertNotIn(
            "8 personas not represented",
            self.text,
            "failure marker must use the matched count, not a hardcoded 8 — "
            "a thin diff can match as few as 3 of the 8 Sonnet-tier personas",
        )


if __name__ == "__main__":
    unittest.main()
