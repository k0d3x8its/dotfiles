#!/usr/bin/env python3
"""Tests for scripts/rotate-log."""

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "scripts"


def load_script(name):
    mod_name = name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(mod_name, str(SCRIPTS / name))
    spec = importlib.util.spec_from_loader(mod_name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    loader.exec_module(mod)
    return mod


rl = load_script("rotate-log")

BLOCK_A = "## Session Handoff — 2026-01-01 10:00 AM\noldest content\n"
BLOCK_B = "## Session Handoff — 2026-01-02 10:00 AM\nmiddle content\n"
BLOCK_C = "## Session Handoff — 2026-01-03 10:00 AM\nnewest content\n"
BLOCK_D = "## Session Handoff — 2026-01-04 10:00 AM\nextra content\n"
# Checkpoint blocks use a different heading than handoff blocks. rotate-log
# must treat them as first-class block boundaries (regression fixture).
BLOCK_CHECK = "## Session Checkpoint — 2026-01-05 10:00 AM\ncheckpoint content\n"


class TestParseBlocks(unittest.TestCase):
    def test_no_blocks_returns_empty(self):
        lines = "# header\n> desc\n".splitlines(keepends=True)
        header, blocks = rl.parse_blocks(lines)
        self.assertEqual(blocks, [])

    def test_header_lines_captured_before_first_block(self):
        text = "# My Log\n> desc\n---\n" + BLOCK_A
        header, _ = rl.parse_blocks(text.splitlines(keepends=True))
        self.assertEqual(len(header), 3)

    def test_single_block_parsed(self):
        _, blocks = rl.parse_blocks(BLOCK_A.splitlines(keepends=True))
        self.assertEqual(len(blocks), 1)

    def test_multiple_blocks_parsed(self):
        text = BLOCK_A + BLOCK_B + BLOCK_C
        _, blocks = rl.parse_blocks(text.splitlines(keepends=True))
        self.assertEqual(len(blocks), 3)

    def test_epoch_parsed_from_date(self):
        _, blocks = rl.parse_blocks(BLOCK_A.splitlines(keepends=True))
        epoch, _, _ = blocks[0]
        self.assertGreater(epoch, 0)

    def test_block_without_date_gets_epoch_zero(self):
        text = "## Session Handoff — no date here\ncontent\n"
        _, blocks = rl.parse_blocks(text.splitlines(keepends=True))
        epoch, _, _ = blocks[0]
        self.assertEqual(epoch, 0)

    def test_block_boundaries_contiguous(self):
        lines = (BLOCK_A + BLOCK_B).splitlines(keepends=True)
        _, blocks = rl.parse_blocks(lines)
        _, s0, e0 = blocks[0]
        _, s1, e1 = blocks[1]
        self.assertEqual(e0, s1)
        self.assertEqual(e1, len(lines))


class TestCheckpointBlocks(unittest.TestCase):
    """Regression: BLOCK_RE must match Checkpoint headings too.

    With the old regex (^## Session Handoff) a checkpoint block was not a
    boundary, so its content got swallowed into the preceding handoff block
    and the block count was undercounted.
    """

    def test_checkpoint_block_parsed(self):
        _, blocks = rl.parse_blocks(BLOCK_CHECK.splitlines(keepends=True))
        self.assertEqual(len(blocks), 1)

    def test_handoff_then_checkpoint_are_separate_blocks(self):
        text = BLOCK_A + BLOCK_CHECK
        _, blocks = rl.parse_blocks(text.splitlines(keepends=True))
        self.assertEqual(len(blocks), 2)

    def test_checkpoint_not_swallowed_into_handoff(self):
        text = BLOCK_A + BLOCK_CHECK
        _, blocks = rl.parse_blocks(text.splitlines(keepends=True))
        _, s0, e0 = blocks[0]
        # handoff block ends before the checkpoint heading begins
        self.assertEqual(e0, s0 + len(BLOCK_A.splitlines()))

    def test_checkpoint_date_parsed_to_epoch(self):
        _, blocks = rl.parse_blocks(BLOCK_CHECK.splitlines(keepends=True))
        epoch, _, _ = blocks[0]
        self.assertGreater(epoch, 0)


class TestRotateReturnValue(unittest.TestCase):
    def test_returns_false_when_at_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C)
            self.assertFalse(rl.rotate(log, 3))

    def test_returns_false_when_below_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B)
            self.assertFalse(rl.rotate(log, 5))

    def test_returns_true_when_above_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C + BLOCK_D)
            self.assertTrue(rl.rotate(log, 3))


class TestRotateContent(unittest.TestCase):
    def test_oldest_block_moved_to_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C)
            rl.rotate(log, 2)
            arch = Path(tmp) / "ARCHIVE-LOG.md"
            self.assertIn("oldest content", arch.read_text())

    def test_newest_blocks_stay_in_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C)
            rl.rotate(log, 2)
            text = log.read_text()
            self.assertIn("middle content", text)
            self.assertIn("newest content", text)
            self.assertNotIn("oldest content", text)

    def test_oldest_block_not_in_log_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C + BLOCK_D)
            rl.rotate(log, 2)
            text = log.read_text()
            self.assertNotIn("oldest content", text)
            self.assertNotIn("middle content", text)

    def test_correct_block_count_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C + BLOCK_D)
            rl.rotate(log, 2)
            headers = [l for l in log.read_text().splitlines()
                       if l.startswith("## Session Handoff")]
            self.assertEqual(len(headers), 2)

    def test_file_header_preserved_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text("# Session Log\n> desc\n---\n" + BLOCK_A + BLOCK_B)
            rl.rotate(log, 1)
            self.assertTrue(log.read_text().startswith("# Session Log\n"))

    def test_kept_blocks_preserve_file_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            # out-of-order dates — newest N by date kept, written in file order
            text = (
                "## Session Handoff — 2026-01-03 10:00 AM\nblock3\n"
                "## Session Handoff — 2026-01-01 10:00 AM\nblock1\n"
                "## Session Handoff — 2026-01-04 10:00 AM\nblock4\n"
                "## Session Handoff — 2026-01-02 10:00 AM\nblock2\n"
            )
            log.write_text(text)
            rl.rotate(log, 2)
            out = log.read_text()
            # block3 and block4 are newest — block3 appeared first in file
            pos3 = out.find("block3")
            pos4 = out.find("block4")
            self.assertGreater(pos3, -1)
            self.assertGreater(pos4, -1)
            self.assertLess(pos3, pos4)


class TestArchiveFile(unittest.TestCase):
    def test_archive_created_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B)
            arch = Path(tmp) / "ARCHIVE-LOG.md"
            self.assertFalse(arch.exists())
            rl.rotate(log, 1)
            self.assertTrue(arch.exists())

    def test_archive_contains_header_when_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B)
            rl.rotate(log, 1)
            self.assertIn("Session Log — Archive", (Path(tmp) / "ARCHIVE-LOG.md").read_text())

    def test_archive_appended_when_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            arch = Path(tmp) / "ARCHIVE-LOG.md"
            arch.write_text("# Session Log — Archive\npre-existing\n")
            log.write_text(BLOCK_A + BLOCK_B)
            rl.rotate(log, 1)
            text = arch.read_text()
            self.assertIn("pre-existing", text)
            self.assertIn("oldest content", text)

    def test_multiple_rotations_accumulate_in_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "SESSION-LOG.md"
            arch = Path(tmp) / "ARCHIVE-LOG.md"
            log.write_text(BLOCK_A + BLOCK_B + BLOCK_C)
            rl.rotate(log, 2)  # archives block_a
            log.write_text(log.read_text() + BLOCK_D)
            rl.rotate(log, 2)  # archives block_b
            arch_text = arch.read_text()
            self.assertIn("oldest content", arch_text)
            self.assertIn("middle content", arch_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
