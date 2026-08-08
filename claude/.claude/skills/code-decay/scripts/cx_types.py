#!/usr/bin/env python3
"""Shared `Cx` shape both complexity backends return — one definition so the
Dispatcher never has to check which backend answered."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cx:
    branch_count: int
    nesting_depth: int

    @property
    def value(self) -> int:
        return self.branch_count + self.nesting_depth
