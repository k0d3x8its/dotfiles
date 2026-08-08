#!/usr/bin/env python3
"""Scorer: score = churn x cx, both absolute units, no repo-relative rescale —
so an unchanged file's score stays stable across dates (FR-08)."""

from __future__ import annotations


def score_files(rows: dict[str, tuple[int, int]]) -> dict[str, int]:
    """rows: path -> (churn, cx). Each score is a pure function of that one
    file's own pair — never reads any other file's churn/cx (FR-07)."""
    return {path: churn * cx for path, (churn, cx) in rows.items()}
