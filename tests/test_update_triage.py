#!/usr/bin/env python3
"""
Tests for scripts/update-triage and scripts/update-cache.
Run: python3 tests/test_update_triage.py
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).parent.parent / "scripts"


def load_script(name):
    import importlib.machinery
    mod_name = name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


triage = load_script("update-triage")
cache = load_script("update-cache")


class TestParseTags(unittest.TestCase):
    def test_single_tag(self):
        self.assertEqual(triage.parse_tags("- [ ] [BUG] broken thing"), ["BUG"])

    def test_multiple_tags(self):
        self.assertEqual(
            triage.parse_tags("- [ ] [TEST][PERFORMANCE] verify cache"),
            ["TEST", "PERFORMANCE"],
        )

    def test_no_tags(self):
        self.assertEqual(triage.parse_tags("- [ ] plain todo"), [])

    def test_priority_tags_included(self):
        tags = triage.parse_tags("- [ ] [LOW][CHORE] some chore")
        self.assertIn("LOW", tags)
        self.assertIn("CHORE", tags)


class TestIsUrgent(unittest.TestCase):
    def test_keyword_failing(self):
        self.assertTrue(triage.is_urgent("CI is failing"))

    def test_keyword_broken(self):
        self.assertTrue(triage.is_urgent("[BROKEN] thing broken"))

    def test_keyword_missing(self):
        self.assertTrue(triage.is_urgent("missing config file"))

    def test_not_urgent(self):
        self.assertFalse(triage.is_urgent("clean up old branch"))

    def test_backtick_code_excluded(self):
        # "failing" inside backtick span should NOT trigger urgent
        self.assertFalse(triage.is_urgent("run `test_failing_helper()` to verify"))


class TestGetTier(unittest.TestCase):
    def test_broken_is_critical(self):
        self.assertEqual(triage.get_tier(["BROKEN"], "broken thing"), "CRITICAL")

    def test_blocker_is_high(self):
        self.assertEqual(triage.get_tier(["BLOCKER"], "must fix first"), "HIGH")

    def test_low_tag_is_low(self):
        self.assertEqual(triage.get_tier(["LOW"], "optional cleanup"), "LOW")

    def test_backlog_tag_is_backlog(self):
        self.assertEqual(triage.get_tier(["BACKLOG"], "someday task"), "BACKLOG")

    def test_urgent_keyword_is_high(self):
        self.assertEqual(triage.get_tier([], "CI is failing right now"), "HIGH")

    def test_default_is_medium(self):
        self.assertEqual(triage.get_tier([], "normal todo item"), "MEDIUM")

    def test_priority_tag_beats_keyword(self):
        self.assertEqual(triage.get_tier(["BACKLOG"], "CI is failing"), "BACKLOG")

    def test_test_tag_is_critical(self):
        self.assertEqual(triage.get_tier(["TEST"], "verify something"), "CRITICAL")

    def test_test_tag_beats_other_priority_tags(self):
        self.assertEqual(triage.get_tier(["TEST", "LOW"], "verify something"), "CRITICAL")
        self.assertEqual(triage.get_tier(["LOW", "TEST"], "verify something"), "CRITICAL")


class TestItemKey(unittest.TestCase):
    def test_strips_prefix(self):
        self.assertEqual(triage.item_key("- [ ] [BUG] fix thing"), "[BUG] fix thing")

    def test_strips_priority_tags(self):
        self.assertEqual(triage.item_key("- [ ] [LOW][BUG] fix thing"), "[BUG] fix thing")
        self.assertEqual(triage.item_key("- [ ] [BROKEN][FEAT] new thing"), "[FEAT] new thing")
        self.assertEqual(triage.item_key("- [ ] [BLOCKER] must do"), "must do")
        self.assertEqual(triage.item_key("- [ ] [BACKLOG] someday"), "someday")

    def test_normalizes_whitespace(self):
        self.assertEqual(triage.item_key("- [ ] [LOW]  lots   of   space"), "lots of space")

    def test_annotation_tags_preserved(self):
        key = triage.item_key("- [ ] [LOW][BUG] fix thing")
        self.assertIn("[BUG]", key)
        self.assertNotIn("[LOW]", key)

    def test_stable_across_priority_tag_change(self):
        # adding [LOW] to an item should not change its key
        without = triage.item_key("- [ ] [BUG] fix thing")
        with_low = triage.item_key("- [ ] [LOW][BUG] fix thing")
        self.assertEqual(without, with_low)

    def test_strips_since_tag(self):
        self.assertEqual(triage.item_key("- [ ] [LOW] Do thing [since: 2026-05-01]"), "Do thing")

    def test_stable_across_since_tag_change(self):
        without = triage.item_key("- [ ] [BUG] fix thing")
        with_since = triage.item_key("- [ ] [BUG] fix thing [since: 2026-05-01]")
        self.assertEqual(without, with_since)

    def test_malformed_since_tag_stripped_from_key(self):
        self.assertEqual(triage.item_key("- [ ] [BUG] bad tag [since: not-a-date]"), "[BUG] bad tag")


class TestUpdateItemDates(unittest.TestCase):
    def _projects(self, *lines, mtime_str=None):
        return {"proj": [(line, mtime_str) for line in lines]}

    def test_new_item_seeds_from_file_mtime(self):
        """First-seen date uses file mtime, not today — stale items visible immediately."""
        old_mtime = "2020-01-01"
        projects = self._projects("- [ ] [BUG] fix thing", mtime_str=old_mtime)
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        self.assertEqual(result[triage.item_key("- [ ] [BUG] fix thing")], old_mtime)

    def test_legacy_item_with_none_mtime_uses_today(self):
        """Legacy inline items (no file mtime) fall back to today."""
        projects = self._projects("- [ ] [BUG] fix thing", mtime_str=None)
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(result[triage.item_key("- [ ] [BUG] fix thing")], today)

    def test_existing_dates_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            key = triage.item_key("- [ ] [BUG] fix thing")
            dates_file.write_text(json.dumps({key: "2020-01-01"}))
            projects = self._projects("- [ ] [BUG] fix thing", mtime_str="2026-01-01")
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        self.assertEqual(result[key], "2020-01-01")

    def test_gone_items_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            old_key = triage.item_key("- [ ] [BUG] old item")
            dates_file.write_text(json.dumps({old_key: "2020-01-01"}))
            projects = self._projects("- [ ] [FEAT] new item", mtime_str="2026-01-01")
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        self.assertNotIn(old_key, result)

    def test_dates_file_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            projects = self._projects("- [ ] [BUG] fix thing", mtime_str="2026-01-01")
            with patch.object(triage, "DATES_FILE", dates_file):
                triage.update_item_dates(projects)
            self.assertTrue(dates_file.exists())

    def test_since_tag_used_as_seed(self):
        """[since: DATE] tag uses that date as seed, not file mtime."""
        projects = self._projects("- [ ] [BACKLOG] Old thing [since: 2026-05-01]", mtime_str="2026-06-04")
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        key = triage.item_key("- [ ] [BACKLOG] Old thing [since: 2026-05-01]")
        self.assertEqual(result[key], "2026-05-01")

    def test_since_tag_overrides_existing_cached_date(self):
        """[since:] tag always wins — enables retroactive correction of wrong seed dates."""
        key = triage.item_key("- [ ] [BACKLOG] Old thing [since: 2026-05-01]")
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            dates_file.write_text(json.dumps({key: "2026-06-04"}))
            projects = self._projects("- [ ] [BACKLOG] Old thing [since: 2026-05-01]", mtime_str="2026-06-04")
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        self.assertEqual(result[key], "2026-05-01")

    def test_since_tag_removed_cached_date_survives(self):
        """Removing [since:] tag does not reset the cached date."""
        key = triage.item_key("- [ ] [BACKLOG] Old thing")
        with tempfile.TemporaryDirectory() as tmp:
            dates_file = Path(tmp) / ".triage-dates"
            dates_file.write_text(json.dumps({key: "2026-05-01"}))
            projects = self._projects("- [ ] [BACKLOG] Old thing", mtime_str="2026-06-04")
            with patch.object(triage, "DATES_FILE", dates_file):
                result = triage.update_item_dates(projects)
        self.assertEqual(result[key], "2026-05-01")


class TestParseCache(unittest.TestCase):
    def test_pointer_format_reads_todos_file(self):
        """parse_cache follows 'path:' pointer and reads TODOS.md lines."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text(
                "# header\n"
                "- [ ] [TEST] first open item\n"
                "- [x] done item\n"
                "- [ ] [BUG] second open item\n"
            )
            cache_file = tmp / ".triage-cache"
            cache_file.write_text(f"## [machine]\nmtime: 1234\npath: {todos}\n")
            projects = triage.parse_cache(cache_file)

        self.assertIn("[machine]", projects)
        items = projects["[machine]"]
        self.assertEqual(len(items), 2)
        line_texts = [line for line, _ in items]
        self.assertIn("- [ ] [TEST] first open item", line_texts)
        self.assertIn("- [ ] [BUG] second open item", line_texts)
        self.assertNotIn("- [x] done item", line_texts)

    def test_pointer_format_items_carry_mtime(self):
        """parse_cache returns (line, mtime_str) tuples for pointer-format items."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] [BUG] some item\n")
            cache_file = tmp / ".triage-cache"
            cache_file.write_text(f"## [proj]\nmtime: 1234\npath: {todos}\n")
            projects = triage.parse_cache(cache_file)

        line, mtime_str = projects["[proj]"][0]
        self.assertTrue(line.startswith("- [ ]"))
        self.assertRegex(mtime_str, r"^\d{4}-\d{2}-\d{2}$")

    def test_legacy_format_reads_inline_todos(self):
        """parse_cache reads verbatim '- [ ]' lines for legacy blocks."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cache_file = tmp / ".triage-cache"
            cache_file.write_text(
                "## batctrl\nmtime: 9999\n- [ ] [BUG] legacy todo\n- [ ] [CHORE] cleanup\n"
            )
            projects = triage.parse_cache(cache_file)

        self.assertIn("batctrl", projects)
        self.assertEqual(len(projects["batctrl"]), 2)

    def test_missing_todos_path_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cache_file = tmp / ".triage-cache"
            cache_file.write_text(
                f"## ghostproject\nmtime: 1234\npath: {tmp}/nonexistent.md\n"
            )
            projects = triage.parse_cache(cache_file)

        self.assertIn("ghostproject", projects)
        self.assertEqual(projects["ghostproject"], [])


class TestBuildTriage(unittest.TestCase):
    def _p(self, *lines):
        return {"proj": [(line, None) for line in lines]}

    def test_tiers_populated_correctly(self):
        tiers = triage.build_triage(self._p(
            "- [ ] [BROKEN] critical thing",
            "- [ ] [BLOCKER] high priority",
            "- [ ] normal medium todo",
            "- [ ] [LOW] low priority",
            "- [ ] [BACKLOG] someday",
        ), {})
        self.assertEqual(len(tiers["CRITICAL"]), 1)
        self.assertEqual(len(tiers["HIGH"]), 1)
        self.assertEqual(len(tiers["MEDIUM"]), 1)
        self.assertEqual(len(tiers["LOW"]), 1)
        self.assertEqual(len(tiers["BACKLOG"]), 1)

    def test_urgent_item_goes_to_high_not_medium(self):
        tiers = triage.build_triage(self._p("- [ ] CI is failing badly"), {})
        self.assertEqual(len(tiers["HIGH"]), 1)
        self.assertEqual(len(tiers["MEDIUM"]), 0)

    def test_urgent_items_sorted_first_within_tier(self):
        projects = {
            "aaa": [("- [ ] normal medium todo", None)],
            "bbb": [("- [ ] build is broken", None)],
        }
        tiers = triage.build_triage(projects, {})
        self.assertTrue(tiers["HIGH"][0][2])  # urgent flag True

    def test_tier_items_are_four_tuples(self):
        tiers = triage.build_triage(self._p("- [ ] [BUG] something"), {})
        self.assertEqual(len(tiers["HIGH"][0]), 4)

    def test_first_seen_date_threaded_through(self):
        line = "- [ ] [BUG] something"
        key = triage.item_key(line)
        item_dates = {key: "2020-01-01"}
        tiers = triage.build_triage({"proj": [(line, None)]}, item_dates)
        _, _, _, first_seen = tiers["HIGH"][0]
        self.assertEqual(first_seen, datetime.fromisoformat("2020-01-01"))

    def test_none_date_when_key_missing(self):
        tiers = triage.build_triage(self._p("- [ ] [BUG] something"), {})
        _, _, _, first_seen = tiers["HIGH"][0]
        self.assertIsNone(first_seen)


class TestFmtLine(unittest.TestCase):
    def test_project_without_brackets_gets_brackets(self):
        result = triage.fmt_line("machine", "- [ ] [BUG] fix thing", False, None)
        self.assertIn("[machine]", result)

    def test_project_with_brackets_unchanged(self):
        result = triage.fmt_line("[machine]", "- [ ] [BUG] fix thing", False, None)
        self.assertIn("[machine]", result)
        self.assertNotIn("[[machine]]", result)

    def test_urgent_prefix_applied(self):
        result = triage.fmt_line("proj", "- [ ] broken thing", True, None)
        self.assertIn("⚠", result)

    def test_no_prefix_when_not_urgent(self):
        result = triage.fmt_line("proj", "- [ ] normal thing", False, None)
        self.assertNotIn("⚠", result)

    def test_priority_tags_stripped_from_text(self):
        result = triage.fmt_line("proj", "- [ ] [LOW] optional chore", False, None)
        self.assertNotIn("[LOW]", result)

    def test_raw_prefix_stripped(self):
        result = triage.fmt_line("proj", "- [ ] do the thing", False, None)
        self.assertNotIn("- [ ]", result)

    def test_stale_label_appended_when_old(self):
        old_date = datetime.now() - timedelta(days=triage.STALE_DAYS + 1)
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, old_date)
        self.assertIn(triage.STALE_LABEL, result)

    def test_stale_label_absent_when_fresh(self):
        fresh_date = datetime.now() - timedelta(days=triage.STALE_DAYS - 1)
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, fresh_date)
        self.assertNotIn(triage.STALE_LABEL, result)

    def test_stale_label_absent_when_date_none(self):
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, None)
        self.assertNotIn(triage.STALE_LABEL, result)

    def test_stale_label_contains_date_string(self):
        old_date = datetime(2025, 3, 10)
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, old_date)
        self.assertIn("2025-03-10", result)

    def test_stale_label_contains_color(self):
        old_date = datetime.now() - timedelta(days=triage.STALE_DAYS + 1)
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, old_date)
        self.assertIn(triage.STALE_COLOR, result)

    def test_since_tag_stripped_from_display(self):
        result = triage.fmt_line("proj", "- [ ] [LOW] Do thing [since: 2026-05-01]", False, None)
        self.assertNotIn("[since:", result)
        self.assertIn("Do thing", result)

    def test_exactly_at_threshold_is_not_stale(self):
        boundary_date = datetime.now() - timedelta(days=triage.STALE_DAYS)
        result = triage.fmt_line("proj", "- [ ] [BUG] fix thing", False, boundary_date)
        self.assertNotIn(triage.STALE_LABEL, result)


class TestUpdateCacheMtime(unittest.TestCase):
    def test_written_mtime_equals_live_stat(self):
        """update-cache writes mtime: that exactly equals stat -c %Y of TODOS.md."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] some item\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("[machine]", todos)

            live_mtime = int(todos.stat().st_mtime)
            import re
            m = re.search(r"mtime: (\d+)", cache_file.read_text())
            self.assertIsNotNone(m, "mtime: line not found in cache")
            self.assertEqual(int(m.group(1)), live_mtime)

    def test_cache_contains_path_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] foo\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("myproject", todos)

            text = cache_file.read_text()
            self.assertIn(f"path: {todos}", text)
            self.assertIn("## [MYPROJECT]", text)

    def test_update_replaces_existing_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] foo\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("proj", todos)
                cache.update_cache("proj", todos)

            self.assertEqual(cache_file.read_text().count("## [PROJ]"), 1)


class TestIsUrgentFullCoverage(unittest.TestCase):
    def test_not_yet(self):
        self.assertTrue(triage.is_urgent("not yet implemented"))

    def test_do_not(self):
        self.assertTrue(triage.is_urgent("do not deploy this"))

    def test_hasnt(self):
        self.assertTrue(triage.is_urgent("hasn't been fixed"))

    def test_has_not(self):
        self.assertTrue(triage.is_urgent("has not been merged"))

    def test_warning(self):
        self.assertTrue(triage.is_urgent("warning in CI output"))

    def test_stale(self):
        self.assertTrue(triage.is_urgent("stale branch needs cleanup"))

    def test_never(self):
        self.assertTrue(triage.is_urgent("never lands on main"))

    def test_error(self):
        self.assertTrue(triage.is_urgent("error in deploy step"))

    def test_backtick_excludes_keyword(self):
        self.assertFalse(triage.is_urgent("call `never_retry()` here"))

    def test_case_insensitive(self):
        self.assertTrue(triage.is_urgent("STALE branch"))


class TestGetTierConflictingTags(unittest.TestCase):
    def test_broken_beats_low(self):
        self.assertEqual(triage.get_tier(["BROKEN", "LOW"], "thing"), "CRITICAL")

    def test_test_beats_backlog(self):
        self.assertEqual(triage.get_tier(["TEST", "BACKLOG"], "verify"), "CRITICAL")

    def test_test_beats_low(self):
        self.assertEqual(triage.get_tier(["TEST", "LOW"], "verify"), "CRITICAL")

    def test_first_priority_tag_wins(self):
        self.assertEqual(triage.get_tier(["BLOCKER", "LOW"], "thing"), "HIGH")


class TestStripPriorityTags(unittest.TestCase):
    def test_strips_broken(self):
        self.assertNotIn("[BROKEN]", triage.strip_priority_tags("[BROKEN] fix this"))

    def test_strips_blocker(self):
        self.assertNotIn("[BLOCKER]", triage.strip_priority_tags("[BLOCKER] must do first"))

    def test_strips_low(self):
        self.assertNotIn("[LOW]", triage.strip_priority_tags("[LOW] optional"))

    def test_strips_backlog(self):
        self.assertNotIn("[BACKLOG]", triage.strip_priority_tags("[BACKLOG] someday"))

    def test_whitespace_normalized(self):
        self.assertNotIn("  ", triage.strip_priority_tags("[BROKEN]   lots   of   space"))

    def test_annotation_tags_preserved(self):
        self.assertIn("[BUG]", triage.strip_priority_tags("[LOW][BUG] broken thing"))


class TestColorizeTags(unittest.TestCase):
    def test_known_tag_gets_color_span(self):
        result = triage.colorize_tags("[BUG] broken thing")
        self.assertIn('<span style="color:', result)
        self.assertIn("[BUG]", result)

    def test_unknown_tag_passes_through(self):
        result = triage.colorize_tags("[MYUNKNOWNTAG] thing")
        self.assertIn("[MYUNKNOWNTAG]", result)
        self.assertNotIn("<span", result)

    def test_tag_in_backtick_not_colorized(self):
        result = triage.colorize_tags("run `[BUG]` inline")
        self.assertNotIn("<span", result)
        self.assertIn("`[BUG]`", result)

    def test_multiple_known_tags_all_colorized(self):
        self.assertEqual(triage.colorize_tags("[BUG][FEAT] something").count("<span"), 2)

    def test_correct_color_applied(self):
        self.assertIn("#74c0fc", triage.colorize_tags("[TEST] verify"))

    def test_waiting_color_distinct_from_chore(self):
        chore = triage.colorize_tags("[CHORE] cleanup")
        waiting = triage.colorize_tags("[WAITING] blocked")
        chore_color = triage.ANNOTATION_COLORS["CHORE"]
        waiting_color = triage.ANNOTATION_COLORS["WAITING"]
        self.assertIn(chore_color, chore)
        self.assertIn(waiting_color, waiting)
        self.assertNotEqual(chore_color, waiting_color)

    def test_ux_correct_color_applied(self):
        self.assertIn("#f783ac", triage.colorize_tags("[UX] check the flow"))


class TestRemoveProjectBlock(unittest.TestCase):
    def test_target_block_removed(self):
        lines = [
            "## proj-a\n", "mtime: 1\n", "- [ ] task\n",
            "## proj-b\n", "mtime: 2\n", "- [ ] other\n",
        ]
        result = cache.remove_project_block(lines, "proj-a")
        self.assertNotIn("## proj-a\n", result)

    def test_adjacent_blocks_preserved(self):
        lines = [
            "## proj-a\n", "mtime: 1\n",
            "## proj-b\n", "mtime: 2\n", "- [ ] keep\n",
        ]
        result = cache.remove_project_block(lines, "proj-a")
        self.assertIn("## proj-b\n", result)
        self.assertIn("- [ ] keep\n", result)

    def test_nonexistent_project_leaves_lines_unchanged(self):
        lines = ["## proj-a\n", "mtime: 1\n"]
        self.assertEqual(cache.remove_project_block(lines, "ghost"), lines)

    def test_partial_name_match_not_removed(self):
        lines = ["## proj\n", "mtime: 1\n", "## proj-extended\n", "mtime: 2\n"]
        result = cache.remove_project_block(lines, "proj")
        self.assertNotIn("## proj\n", result)
        self.assertIn("## proj-extended\n", result)

    def test_bracketed_block_removed_by_bare_name(self):
        lines = ["## [MACHINE]\n", "mtime: 1\n", "path: /dev/TODOS.md\n"]
        self.assertNotIn("## [MACHINE]\n", cache.remove_project_block(lines, "machine"))

    def test_bare_block_removed_by_bracketed_name(self):
        lines = ["## machine\n", "mtime: 1\n", "path: /dev/TODOS.md\n"]
        self.assertNotIn("## machine\n", cache.remove_project_block(lines, "[machine]"))

    def test_both_forms_removed_when_duplicate_exists(self):
        lines = [
            "## [machine]\n", "mtime: 1\n", "path: /dev/TODOS.md\n",
            "## machine\n", "mtime: 2\n", "path: /dev/TODOS.md\n",
        ]
        result = cache.remove_project_block(lines, "machine")
        self.assertNotIn("## [machine]\n", result)
        self.assertNotIn("## machine\n", result)


class TestCanonical(unittest.TestCase):
    def test_bare_name_gets_brackets_and_uppercased(self):
        self.assertEqual(cache._canonical("machine"), "[MACHINE]")

    def test_bracketed_name_stays_bracketed_uppercased(self):
        self.assertEqual(cache._canonical("[machine]"), "[MACHINE]")

    def test_already_upper_unchanged(self):
        self.assertEqual(cache._canonical("[MACHINE]"), "[MACHINE]")

    def test_hyphenated_name(self):
        self.assertEqual(cache._canonical("kos-capture"), "[KOS-CAPTURE]")

    def test_update_cache_writes_canonical_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] item\n")
            cache_file = tmp / ".triage-cache"
            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("[machine]", todos)
            self.assertIn("## [MACHINE]", cache_file.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
