#!/usr/bin/env python3
"""Tests for code-crit/scripts/fingerprint_group.py — pins the exact-match boundary so it never drifts into fuzzy matching (the advisor's job) or silently stops clustering real dupes."""

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).parent.parent
    / "claude"
    / ".claude"
    / "skills"
    / "code-crit"
    / "scripts"
)


def load_module(name):
    """Load a script from a hyphenated skill dir (not import-package-safe)."""
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


fingerprint_group = load_module("fingerprint_group.py")
Finding = fingerprint_group.Finding
group_findings = fingerprint_group.group_findings
normalize_title = fingerprint_group.normalize_title


class NormalizeTitleTests(unittest.TestCase):
    def test_lowercases_and_strips_punctuation(self) -> None:
        self.assertEqual(
            normalize_title("Null deref on `user`!"),
            "null deref on user",
        )

    def test_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_title("null   deref  on user"), "null deref on user")

    def test_folds_accented_letters_instead_of_stripping(self) -> None:
        # Fold, don't strip — a strip-only regex loses the letters entirely.
        self.assertEqual(normalize_title("café déjà"), normalize_title("cafe deja"))


class GroupFindingsTests(unittest.TestCase):
    def test_clusters_same_finding_with_different_formatting(self) -> None:
        # Same bug, two personas, trivially different punctuation/case —
        # this is exactly what the exact-normalized-title fingerprint exists
        # to catch.
        findings = [
            Finding(
                file="app.py",
                line=10,
                title="Null deref on `user`",
                persona="correctness",
            ),
            Finding(
                file="app.py", line=12, title="null deref on user", persona="security"
            ),
        ]
        clusters = group_findings(findings)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]), 2)

    def test_leaves_differently_worded_findings_ungrouped(self) -> None:
        # Same underlying bug, described in different words — this is the
        # advisor's semantic-dedup territory (SKILL.md § Synthesis #2), NOT
        # this fingerprint's. Must NOT cluster.
        findings = [
            Finding(
                file="app.py",
                line=10,
                title="Null deref on user",
                persona="correctness",
            ),
            Finding(
                file="app.py",
                line=11,
                title="user may be null here",
                persona="security",
            ),
        ]
        clusters = group_findings(findings)
        self.assertEqual(len(clusters), 2)

    def test_leaves_findings_outside_line_window_ungrouped(self) -> None:
        # Same file, same normalized title, but far enough apart (>3 lines)
        # to plausibly be two distinct instances of the same smell, not one
        # dupe report.
        findings = [
            Finding(file="app.py", line=10, title="missing null check"),
            Finding(file="app.py", line=50, title="missing null check"),
        ]
        clusters = group_findings(findings)
        self.assertEqual(len(clusters), 2)

    def test_leaves_findings_in_different_files_ungrouped(self) -> None:
        findings = [
            Finding(file="app.py", line=10, title="missing null check"),
            Finding(file="other.py", line=10, title="missing null check"),
        ]
        clusters = group_findings(findings)
        self.assertEqual(len(clusters), 2)

    def test_single_linkage_chains_a_run_but_breaks_on_a_wide_gap(self) -> None:
        findings = [
            Finding(file="app.py", line=10, title="dup"),
            Finding(file="app.py", line=13, title="dup"),
            Finding(file="app.py", line=16, title="dup"),
            Finding(file="app.py", line=30, title="dup"),
        ]
        clusters = group_findings(findings)
        sizes = sorted(len(c) for c in clusters)
        self.assertEqual(sizes, [1, 3])

    def test_all_punctuation_titles_never_cluster(self) -> None:
        # "" == "" is not a real fingerprint match.
        findings = [
            Finding(file="app.py", line=10, title="!!!"),
            Finding(file="app.py", line=11, title="---"),
        ]
        clusters = group_findings(findings)
        self.assertEqual(len(clusters), 2)


class CliTests(unittest.TestCase):
    """Exercises the __main__ subprocess path, not just library calls."""

    def test_stdin_json_produces_clustered_stdout(self) -> None:
        payload = [
            {
                "file": "app.py",
                "line": 10,
                "title": "Null deref on user",
                "persona": "correctness",
            },
            {
                "file": "app.py",
                "line": 12,
                "title": "null deref on user",
                "persona": "security",
            },
            {"file": "app.py", "line": 40, "title": "unrelated smell"},
        ]
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "fingerprint_group.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        clusters = json.loads(result.stdout)
        sizes = sorted(len(c) for c in clusters)
        self.assertEqual(sizes, [1, 2])

    def test_malformed_finding_degrades_with_clean_error(self) -> None:
        payload = [{"file": "app.py", "line": 10}]  # missing required "title"
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "fingerprint_group.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
