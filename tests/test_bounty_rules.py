#!/usr/bin/env python3
"""Red-green tests for the code-sec ast-grep rule pack against vuln-app.

The pack's central guarantee — fires on every planted vuln, silent on every
safe variant — was until now verified only by a manual `ast-grep scan`. That
made it unpinned: a rule edit, an ast-grep version bump, or a fixture line
shift could break it between runs with nothing to catch it. This is that CI
guard.

Ground truth is the MANIFEST planted-vuln tables (never hardcoded here): the
vuln sink `file:line` cells are the RED targets, the safe-variant files are the
GREEN silence check. Line-exactness matters (a stale ref was a real past bug),
but a rule may match a *span* rather than a point — the CWE-287 authz rule
matches the whole decorated block, starting at the decorator, not the sink line
inside it — so RED asserts the sink line falls WITHIN a match's range, which is
what "the rule flags this vuln" actually means.
"""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

CODE_SEC = (
    Path(__file__).parent.parent
    / "claude" / ".claude" / "skills" / "code-sec"
)
MANIFEST = CODE_SEC / "fixtures" / "vuln-app" / "MANIFEST.md"
SGCONFIG = "rules/sgconfig.yml"
TARGET = "fixtures/vuln-app"

SINK = re.compile(r"([\w./-]+\.(?:py|js|ino)):(\d+)")


def parse_planted_sinks():
    """MANIFEST planted-vuln tables -> {(relpath, line), ...} for vuln files.

    Only rows after the '## Planted vulns' header are read, and only the
    `file:line` token whose path is a vuln variant is kept (the safe-variant
    token in the same row is the GREEN check, asserted globally below).
    """
    sinks = set()
    in_section = False
    for line in MANIFEST.read_text().splitlines():
        if line.startswith("## Planted vulns"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.lstrip().startswith("|"):
            continue
        for path, lineno in SINK.findall(line):
            if "/vuln." in path:
                sinks.add((path, int(lineno)))
    return sinks


def run_scan():
    """Run the rule pack; return matches as (relpath, start_line, end_line).

    Lines are 1-indexed to match MANIFEST; paths are stripped to the
    'vuln-app/'-relative form for direct comparison.
    """
    proc = subprocess.run(
        ["ast-grep", "scan", "-c", SGCONFIG, "--json=compact", TARGET],
        cwd=str(CODE_SEC), capture_output=True, text=True,
    )
    matches = []
    for m in json.loads(proc.stdout):
        relpath = m["file"].split("vuln-app/", 1)[-1]
        rng = m["range"]
        matches.append(
            (relpath, rng["start"]["line"] + 1, rng["end"]["line"] + 1)
        )
    return matches


@unittest.skipUnless(
    shutil.which("ast-grep"),
    "ast-grep not installed — the rule pack is unverifiable; install it to run "
    "this guard (a skip here is a coverage gap, not a pass)",
)
class TestRulePackRedGreen(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.planted = parse_planted_sinks()
        cls.matches = run_scan()

    def test_manifest_has_sixteen_planted_sinks(self):
        # Guards the parser: if MANIFEST reshapes and this drops, every
        # red-green assertion below would weaken silently.
        self.assertEqual(len(self.planted), 16)

    def test_red_every_planted_sink_is_flagged(self):
        for relpath, sinkline in self.planted:
            covered = any(
                m_rel == relpath and start <= sinkline <= end
                for (m_rel, start, end) in self.matches
            )
            with self.subTest(sink=f"{relpath}:{sinkline}"):
                self.assertTrue(
                    covered,
                    f"no rule fired covering planted sink {relpath}:{sinkline}",
                )

    def test_green_no_safe_variant_is_flagged(self):
        safe_hits = [m for m in self.matches if "/safe." in m[0]]
        self.assertEqual(
            safe_hits, [],
            f"rule pack fired on safe variant(s): {safe_hits}",
        )

    def test_no_overfire_match_count_equals_planted_count(self):
        # 16 planted vulns, 16 fires — an extra match means a rule is too broad
        # (the js-sqli cross-fire bug this pack already fixed once).
        self.assertEqual(
            len(self.matches), len(self.planted),
            f"expected {len(self.planted)} matches, got {len(self.matches)}: "
            f"{sorted(self.matches)}",
        )


if __name__ == "__main__":
    unittest.main()
