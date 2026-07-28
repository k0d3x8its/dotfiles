"""Enforce the cross-runtime skill ownership model."""

from __future__ import annotations

import filecmp
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / "claude" / ".claude" / "skills"
CODEX = ROOT / "codex" / ".codex" / "skills"

SHARED = {
    "bounty-hunter",
    "create-gdd",
    "grill-me",
    "mutation-testing",
    "write-a-skill",
    "zoom-out",
}

RUNTIME_SPECIFIC = {
    "ante-mortem",
    "brainstorm",
    "changelog",
    "code-sec",
    "consolidate",
    "dev-brief",
    "dev-setup",
    "diagnose",
    "diagram",
    "encrypt",
    "fable-mode",
    "harness-audit",
    "prototype",
    "recall",
    "release-notes",
    "remember",
    "review-response",
    "session-checkpoint",
    "session-close",
    "session-handoff",
    "session-handoff-return",
    "sync-trello",
    "tdd",
    "trello-agent",
    "trust-but-verify",
    "write-plan",
}

CLAUDE_ONLY = {
    "architecture",
    "code-crit",
    "code-decay",
    "codebase-design",
    "requirements",
    "threat-model",
}


def catalog(path: Path) -> set[str]:
    return {entry.name for entry in path.iterdir() if entry.is_dir()}


def regular_files(path: Path) -> dict[str, Path]:
    return {
        str(entry.relative_to(path)): entry
        for entry in path.rglob("*")
        if entry.is_file()
    }


def trees_are_identical(left: Path, right: Path) -> bool:
    left_files = regular_files(left)
    right_files = regular_files(right)
    if left_files.keys() != right_files.keys():
        return False
    return all(
        filecmp.cmp(left_files[name], right_files[name], shallow=False)
        for name in left_files
    )


class SkillArchitectureTests(unittest.TestCase):
    def test_every_skill_has_an_explicit_ownership_class(self) -> None:
        self.assertEqual(catalog(CLAUDE), SHARED | RUNTIME_SPECIFIC | CLAUDE_ONLY)
        self.assertEqual(catalog(CODEX), SHARED | RUNTIME_SPECIFIC)

    def test_shared_skills_are_codex_links_to_claude_canonical_sources(self) -> None:
        for name in sorted(SHARED):
            with self.subTest(skill=name):
                codex_skill = CODEX / name
                self.assertTrue(codex_skill.is_symlink())
                self.assertEqual(codex_skill.resolve(), (CLAUDE / name).resolve())

    def test_runtime_specific_skills_remain_real_directories(self) -> None:
        for name in sorted(RUNTIME_SPECIFIC):
            with self.subTest(skill=name):
                self.assertFalse((CLAUDE / name).is_symlink())
                self.assertFalse((CODEX / name).is_symlink())

    def test_runtime_specific_skills_are_not_byte_identical_duplicates(self) -> None:
        for name in sorted(RUNTIME_SPECIFIC):
            with self.subTest(skill=name):
                self.assertFalse(
                    trees_are_identical(CLAUDE / name, CODEX / name),
                    f"{name} is byte-identical and should move to SHARED",
                )


if __name__ == "__main__":
    unittest.main()
