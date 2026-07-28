#!/usr/bin/env python3
"""Shared percentile helper — Labeler and the Interpret Pass selector both
need a repo-relative percentile of the current call's own distribution, never
a hardcoded constant (R8/R9)."""

from __future__ import annotations


def percentile(sorted_values: list[int], target: float) -> float:
    if not sorted_values:
        return 0.0
    rank = (len(sorted_values) - 1) * target
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return sorted_values[lower]
    fraction = rank - lower
    return (
        sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction
    )
