#!/usr/bin/env python3
"""Labeler: heuristic labels (God Class, Shotgun Surgery, Dormant Complexity)
from percentiles of THIS call's own distribution, display-only — never fed
back into score (FR-09). Cutoffs measured against kodex-ide's real churn/cx
distribution, not picked by convention — see
`.work/findings/code-decay-label-percentile-cutoffs.md`. Checked in priority
order so labels are mutually exclusive: Dormant Complexity first (a subset of
"high cx"), then God Class (everything else high-cx), then Shotgun Surgery."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

# No `sys.path` mutation — this skill's scripts/ dir has no package boundary
# to import through (same convention as ast_grep_backend.py's cx_types load).
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

HIGH_PERCENTILE = 0.90
LOW_CX_PERCENTILE = 0.50
LOW_CHURN_PERCENTILE = 0.75


def label_files(rows: dict[str, tuple[int, int]]) -> dict[str, str | None]:
    """rows: path -> (churn, cx). Thresholds are percentiles of THIS call's
    own rows — never a hardcoded constant — so a different file set shifts
    where the boundaries fall without touching any file's score.

    A metric floor of 0 is a legitimate "no signal" value (a file with zero
    branches, or zero touches), not a real complexity/churn measurement — in a
    low-variance universe (e.g. mostly docs/config, cx==0 for >10% of files)
    `p90` can land AT that floor, which would make `value >= high_threshold`
    trivially true for the whole set. The `high_cx > 0` / `high_churn > 0`
    guards below stop that: a "high" bucket only fires when its percentile
    threshold is itself above the floor, i.e. there's real spread to rank on.
    """
    if not rows:
        return {}

    churns = sorted(churn for churn, _ in rows.values())
    cxs = sorted(cx for _, cx in rows.values())
    high_cx = percentile(cxs, HIGH_PERCENTILE)
    high_churn = percentile(churns, HIGH_PERCENTILE)
    low_cx = percentile(cxs, LOW_CX_PERCENTILE)
    low_churn = percentile(churns, LOW_CHURN_PERCENTILE)

    labels: dict[str, str | None] = {}
    for path, (churn, cx) in rows.items():
        is_high_cx = high_cx > 0 and cx >= high_cx
        is_high_churn = high_churn > 0 and churn >= high_churn
        if is_high_cx and churn <= low_churn:
            labels[path] = "Dormant Complexity"
        elif is_high_cx:
            labels[path] = "God Class"
        elif is_high_churn and cx <= low_cx:
            labels[path] = "Shotgun Surgery"
        else:
            labels[path] = None
    return labels
