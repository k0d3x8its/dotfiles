#!/usr/bin/env python3
"""
Tests for scripts/update-triage and scripts/update-cache.
Run: python3 tests/test_update_triage.py
"""
import importlib.util
import sys
import unittest
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
        # BACKLOG tag overrides urgent keyword
        self.assertEqual(triage.get_tier(["BACKLOG"], "CI is failing"), "BACKLOG")

    def test_test_tag_is_critical(self):
        self.assertEqual(triage.get_tier(["TEST"], "verify something"), "CRITICAL")

    def test_test_tag_beats_other_priority_tags(self):
        # [TEST] present → always CRITICAL regardless of other priority tags
        self.assertEqual(triage.get_tier(["TEST", "LOW"], "verify something"), "CRITICAL")
        self.assertEqual(triage.get_tier(["LOW", "TEST"], "verify something"), "CRITICAL")


class TestParseCache(unittest.TestCase):
    def test_pointer_format_reads_todos_file(self, tmp_path=None):
        """parse_cache follows 'path:' pointer and reads TODOS.md lines."""
        import tempfile, os
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
            cache_file.write_text(
                f"## [machine]\nmtime: 1234\npath: {todos}\n"
            )
            with patch.object(triage, "CACHE", cache_file):
                projects = triage.parse_cache(cache_file)

        self.assertIn("[machine]", projects)
        lines = projects["[machine]"]
        self.assertEqual(len(lines), 2)
        self.assertIn("- [ ] [TEST] first open item", lines)
        self.assertIn("- [ ] [BUG] second open item", lines)
        self.assertNotIn("- [x] done item", "\n".join(lines))

    def test_legacy_format_reads_inline_todos(self):
        """parse_cache reads verbatim '- [ ]' lines for legacy blocks."""
        import tempfile
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
        """If pointer points to nonexistent file, project list is empty."""
        import tempfile
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
    def test_tiers_populated_correctly(self):
        projects = {
            "proj": [
                "- [ ] [BROKEN] critical thing",
                "- [ ] [BLOCKER] high priority",
                "- [ ] normal medium todo",
                "- [ ] [LOW] low priority",
                "- [ ] [BACKLOG] someday",
            ]
        }
        tiers = triage.build_triage(projects)
        self.assertEqual(len(tiers["CRITICAL"]), 1)
        self.assertEqual(len(tiers["HIGH"]), 1)
        self.assertEqual(len(tiers["MEDIUM"]), 1)
        self.assertEqual(len(tiers["LOW"]), 1)
        self.assertEqual(len(tiers["BACKLOG"]), 1)

    def test_urgent_item_goes_to_high_not_medium(self):
        projects = {"proj": ["- [ ] CI is failing badly"]}
        tiers = triage.build_triage(projects)
        self.assertEqual(len(tiers["HIGH"]), 1)
        self.assertEqual(len(tiers["MEDIUM"]), 0)

    def test_urgent_items_sorted_first_within_tier(self):
        projects = {
            "aaa": ["- [ ] normal medium todo"],
            "bbb": ["- [ ] build is broken"],  # urgent keyword
        }
        tiers = triage.build_triage(projects)
        # urgent item should sort before non-urgent within HIGH
        high = tiers["HIGH"]
        self.assertEqual(len(high), 1)
        self.assertTrue(high[0][2])  # urgent flag is True


class TestUpdateCacheMtime(unittest.TestCase):
    def test_written_mtime_equals_live_stat(self):
        """update-cache writes mtime: that exactly equals stat -c %Y of TODOS.md."""
        import tempfile, time
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] some item\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("[machine]", todos)

            live_mtime = int(todos.stat().st_mtime)
            cache_text = cache_file.read_text()
            import re
            m = re.search(r"mtime: (\d+)", cache_text)
            self.assertIsNotNone(m, "mtime: line not found in cache")
            cached_mtime = int(m.group(1))
            self.assertEqual(cached_mtime, live_mtime,
                msg=f"cached mtime {cached_mtime} != live {live_mtime}")

    def test_cache_contains_path_pointer(self):
        """update-cache writes a 'path:' line pointing to the TODOS.md."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] foo\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("myproject", todos)

            cache_text = cache_file.read_text()
            self.assertIn(f"path: {todos}", cache_text)
            self.assertIn("## myproject", cache_text)

    def test_update_replaces_existing_block(self):
        """Running update-cache twice replaces the block, not appends."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            todos = tmp / "TODOS.md"
            todos.write_text("- [ ] foo\n")
            cache_file = tmp / ".triage-cache"

            with patch.object(cache, "CACHE", cache_file):
                cache.update_cache("proj", todos)
                cache.update_cache("proj", todos)

            # Should have exactly one ## proj block
            text = cache_file.read_text()
            count = text.count("## proj")
            self.assertEqual(count, 1, f"Expected 1 block, found {count}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
