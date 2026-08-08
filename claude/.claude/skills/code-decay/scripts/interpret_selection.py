#!/usr/bin/env python3
"""Interpret Pass — deterministic front end only (FR-10/FR-11): decides which
files clear the score floor and make the top-N cut for model interpretation.
Never calls a model itself — sending the selected files to the agent for
interpretation is the CLI entrypoint's job (`SKILL.md`), the one place this
system's deterministic-core guarantee ends.

Floor locked at p75 of the run's own score distribution — validated against
kodex-ide's real 81-file universe: p75 leaves it as a soft gate N usually caps
first (20 of 81 files clear it), while p90 would almost always bind before N
does, making the two controls redundant. See
`.work/findings/code-decay-interpret-score-floor.md`."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_PERCENTILE_MODULE_NAME = "code_decay_percentile"
_percentile_module = sys.modules.get(_PERCENTILE_MODULE_NAME)
if _percentile_module is None:
    _loader = importlib.machinery.SourceFileLoader(
        _PERCENTILE_MODULE_NAME, str(Path(__file__).parent / "percentile.py")
    )
    _spec = importlib.util.spec_from_loader(_loader.name, _loader)
    _percentile_module = importlib.util.module_from_spec(_spec)
    sys.modules[_loader.name] = _percentile_module
    _loader.exec_module(_percentile_module)
percentile = _percentile_module.percentile

DEFAULT_TOP_N = 10
FLOOR_PERCENTILE = 0.75


def select_for_interpretation(
    rows: dict[str, tuple[int, int]], top_n: int = DEFAULT_TOP_N
) -> list[str]:
    """rows: path -> (churn, cx). Returns up to `top_n` paths whose score
    clears the floor, highest score first — never padded with files below the
    floor even when fewer than `top_n` qualify.

    Floor comparison is `>=`, not `>`. A tied cluster of files sitting exactly
    at p75 (e.g. a repo where several files share the same top score) must
    still be eligible — `top_n` already bounds how many of them get sent, so
    there's no zero-variance mass-selection risk here the way there was for
    the Labeler's unbounded `>=` buckets (which had no equivalent cap)."""
    if not rows:
        return []

    scores = {path: churn * cx for path, (churn, cx) in rows.items()}
    floor = percentile(sorted(scores.values()), FLOOR_PERCENTILE)
    candidates = [path for path, score in scores.items() if score >= floor]
    candidates.sort(key=lambda path: (-scores[path], path))
    return candidates[:top_n]
