#!/usr/bin/env python3
"""Unit tests for code-decay/scripts/report_renderer.py — writes a dated,
plaintext hotspot report inside the TARGET repo (FR-14), never touches
git-crypt config (NFR-03)."""

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = (
    Path(__file__).parent.parent
    / "claude"
    / ".claude"
    / "skills"
    / "code-decay"
    / "scripts"
)


def load_module(name):
    mod_name = name.replace(".", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


report_renderer = load_module("report_renderer.py")
render_report = report_renderer.render_report


class RenderReportTests(unittest.TestCase):
    def test_writes_report_under_docs_code_decay_in_the_target_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo), {"a.py": (10, 5)}, {"a.py": None}, report_date="2026-07-27"
            )

            self.assertEqual(
                output_path, repo / "docs" / "code-decay" / "some-repo-2026-07-27.md"
            )
            self.assertTrue(output_path.exists())

    def test_two_different_dates_produce_two_distinct_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()
            rows = {"a.py": (10, 5)}
            labels = {"a.py": None}

            first = render_report(str(repo), rows, labels, report_date="2026-07-27")
            second = render_report(str(repo), rows, labels, report_date="2026-07-28")

            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())

    def test_report_ranks_files_by_score_descending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()
            rows = {"low.py": (1, 1), "high.py": (10, 10)}
            labels = {"low.py": None, "high.py": "God Class"}

            output_path = render_report(
                str(repo), rows, labels, report_date="2026-07-27"
            )
            content = output_path.read_text()

            self.assertLess(content.index("high.py"), content.index("low.py"))

    def test_label_none_renders_as_empty_not_the_string_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo), {"a.py": (1, 1)}, {"a.py": None}, report_date="2026-07-27"
            )
            content = output_path.read_text()

            self.assertNotIn("None", content)

    def test_skill_source_has_no_git_crypt_step_for_code_decay_reports(self) -> None:
        # NFR-03's actual clause: the skill's own code/docs contain no step
        # that writes or checks for a `docs/code-decay` git-crypt pattern —
        # not "did this test's own temp dir happen to grow a .gitattributes
        # file nothing here would create."
        skill_dir = (
            Path(__file__).parent.parent
            / "claude"
            / ".claude"
            / "skills"
            / "code-decay"
        )
        offending = [
            path
            for path in skill_dir.rglob("*")
            if path.is_file()
            and "gitattributes" in path.read_text(errors="ignore").lower()
        ]

        self.assertEqual(offending, [])

    def test_empty_rows_still_writes_a_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(str(repo), {}, {}, report_date="2026-07-27")

            self.assertTrue(output_path.exists())

    def test_states_actual_interpret_count_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo),
                {"a.py": (10, 5), "b.py": (1, 1)},
                {"a.py": None, "b.py": None},
                report_date="2026-07-27",
                interpreted_paths=["a.py"],
            )
            content = output_path.read_text()

            self.assertIn("1 file", content)

    def test_states_undershoot_count_not_padded_to_n(self) -> None:
        # Only 3 files cleared the floor even though top_n was 10 — the
        # report must say 3, never imply 10 were sent (FR-10, architecture's
        # "floor undershoot: reported, not silently short").
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo),
                {"a.py": (1, 1)},
                {"a.py": None},
                report_date="2026-07-27",
                interpreted_paths=["hot_1.py", "hot_2.py", "hot_3.py"],
            )
            content = output_path.read_text()

            self.assertIn("3 files", content)
            self.assertNotIn("10 files", content)

    def test_score_column_comes_from_the_real_scorer_not_a_second_formula(
        self,
    ) -> None:
        # FR-08 traces to one Scorer implementation. If report_renderer ever
        # grows its own inline `churn * cx`, this test still passes on
        # ordinary input (both formulas agree) but fails the moment
        # scorer.score_files is patched to something else — proving the
        # report actually calls it rather than merely agreeing with it by
        # coincidence.
        original = report_renderer.scorer.score_files
        report_renderer.scorer.score_files = lambda rows: {path: 999 for path in rows}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "some-repo"
                repo.mkdir()

                output_path = render_report(
                    str(repo),
                    {"a.py": (10, 5)},
                    {"a.py": None},
                    report_date="2026-07-27",
                )
                content = output_path.read_text()

                self.assertIn("999", content)
        finally:
            report_renderer.scorer.score_files = original

    def test_shallow_warning_visible_in_report_when_true(self) -> None:
        # FR-05: a shallow-clone warning must be visible in the report
        # output, not just printed to stdout during the run.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo),
                {"a.py": (1, 1)},
                {"a.py": None},
                report_date="2026-07-27",
                shallow_warning=True,
            )
            content = output_path.read_text()

            self.assertIn("shallow", content.lower())

    def test_no_shallow_warning_line_when_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo),
                {"a.py": (1, 1)},
                {"a.py": None},
                report_date="2026-07-27",
                shallow_warning=False,
            )
            content = output_path.read_text()

            self.assertNotIn("shallow", content.lower())

    def test_no_interpret_line_when_interpret_pass_was_not_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "some-repo"
            repo.mkdir()

            output_path = render_report(
                str(repo), {"a.py": (1, 1)}, {"a.py": None}, report_date="2026-07-27"
            )
            content = output_path.read_text()

            self.assertNotIn("Interpret pass", content)


if __name__ == "__main__":
    unittest.main()
