#!/usr/bin/env python3
"""Tests for code-sec/bin/enumerate-entrypoints.sh against the vuln-app fixture.

The enumerator is the shared deterministic core both code-sec and bounty-hunter
consume; a silent miss reads as "no attack surface" and is the dangerous failure
mode. These tests pin its per-file output against the fixture's MANIFEST — the
single source of truth — so a fixture edit updates the assertions automatically
and a regressed enumerator fails `unittest discover` instead of a manual run.

Ground truth parsed from MANIFEST's "Entry points" table:
  | File | Routes | Bind | Exposure guess |
Routes = the http-route count for that file; Exposure = the file-level bind guess.
"""

import re
import subprocess
import unittest
from pathlib import Path

CODE_SEC = (
    Path(__file__).parent.parent
    / "claude" / ".claude" / "skills" / "code-sec"
)
ENUMERATOR = CODE_SEC / "bin" / "enumerate-entrypoints.sh"
MANIFEST = CODE_SEC / "fixtures" / "vuln-app" / "MANIFEST.md"


def parse_entry_points():
    """MANIFEST 'Entry points' table -> {relpath: (routes:int, exposure:str)}.

    Reads only the pipe rows whose first cell is a backticked fixture path, so
    the header and separator rows are skipped without positional assumptions.
    """
    expected = {}
    row = re.compile(
        r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|[^|]*\|\s*(\w+)\s*\|"
    )
    for line in MANIFEST.read_text().splitlines():
        m = row.match(line.strip())
        if m:
            expected[m.group(1)] = (int(m.group(2)), m.group(3))
    return expected


def run_enumerator(*targets):
    """Run the enumerator from the code-sec dir; return (rows, returncode).

    rows are (relpath, kind, detail, exposure) with the 'fixtures/vuln-app/'
    prefix stripped so they compare directly against MANIFEST paths.
    """
    proc = subprocess.run(
        [str(ENUMERATOR), *targets],
        cwd=str(CODE_SEC),
        capture_output=True,
        text=True,
    )
    rows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        loc, kind, detail, exposure = (p.strip() for p in line.split("|"))
        relpath = loc.rsplit(":", 1)[0].split("vuln-app/", 1)[-1]
        rows.append((relpath, kind, detail, exposure))
    return rows, proc.returncode


class TestManifestFixture(unittest.TestCase):
    """The parse itself must find the fixture — a silent empty table would make
    every per-file test vacuously pass."""

    def test_manifest_lists_all_six_fixture_files(self):
        expected = parse_entry_points()
        self.assertEqual(
            set(expected),
            {
                "python/vuln.py", "python/safe.py",
                "node/vuln.js", "node/safe.js",
                "arduino/vuln.ino", "arduino/safe.ino",
            },
        )


class TestPerFileRouteCounts(unittest.TestCase):
    """Every fixture file's http-route count + exposure guess matches MANIFEST."""

    def test_route_count_and_exposure_per_file(self):
        for relpath, (routes, exposure) in parse_entry_points().items():
            with self.subTest(file=relpath):
                rows, code = run_enumerator(f"fixtures/vuln-app/{relpath}")
                self.assertEqual(
                    code, 0, f"{relpath}: enumerator found no entry points"
                )
                http_routes = [r for r in rows if r[1] == "http-route"]
                self.assertEqual(
                    len(http_routes), routes,
                    f"{relpath}: expected {routes} http-routes, "
                    f"enumerator emitted {len(http_routes)}",
                )
                exposures = {r[3] for r in rows}
                self.assertEqual(
                    exposures, {exposure},
                    f"{relpath}: expected exposure {exposure!r}, got {exposures}",
                )


class TestExitCodes(unittest.TestCase):
    """The exit-code contract callers branch on: 0 = surface found, 1 = none,
    2 = usage / bad path. A missed distinction here silently mis-triages."""

    def test_zero_when_surface_found(self):
        _, code = run_enumerator("fixtures/vuln-app")
        self.assertEqual(code, 0)

    def test_one_when_no_entry_points(self):
        import tempfile
        with tempfile.TemporaryDirectory() as empty:
            proc = subprocess.run(
                [str(ENUMERATOR), empty],
                cwd=str(CODE_SEC), capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(proc.stdout.strip(), "")

    def test_two_on_missing_path(self):
        proc = subprocess.run(
            [str(ENUMERATOR), "/no/such/path/here"],
            cwd=str(CODE_SEC), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_two_on_no_args(self):
        proc = subprocess.run(
            [str(ENUMERATOR)],
            cwd=str(CODE_SEC), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
