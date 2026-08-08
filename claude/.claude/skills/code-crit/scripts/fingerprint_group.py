#!/usr/bin/env python3
"""Groups findings into candidate-dupe clusters as a HINT for the Stage-2 Opus advisor (SKILL.md § Synthesis), which has final dedup say."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    # Frozen: this module only ever reorders/buckets findings, never edits one.
    file: str
    line: int
    title: str
    persona: str = ""


def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    # NFKD-fold first so accented letters survive as their base letter (café -> cafe, not caf).
    folded = unicodedata.normalize("NFKD", title.lower())
    ascii_only = folded.encode("ascii", "ignore").decode("ascii")
    stripped = re.sub(r"[^a-z0-9\s]", "", ascii_only)
    return re.sub(r"\s+", " ", stripped).strip()


def group_findings(
    findings: list[Finding], line_window: int = 3
) -> list[list[Finding]]:
    """Group findings sharing (file, normalized title) whose lines chain within `line_window` of a neighbor (single-linkage)."""
    buckets: dict[tuple[str, str], list[Finding]] = {}
    singletons: list[Finding] = []
    for finding in findings:
        normalized = normalize_title(finding.title)
        if not normalized:
            # Empty normalized title ("" == "") is not a real fingerprint match.
            singletons.append(finding)
            continue
        key = (finding.file, normalized)
        buckets.setdefault(key, []).append(finding)

    clusters: list[list[Finding]] = [[finding] for finding in singletons]
    for bucket in buckets.values():
        ordered = sorted(bucket, key=lambda item: item.line)
        current: list[Finding] = []
        for finding in ordered:
            # Chain off the previous item, not the cluster's first, so one wide gap in a long run splits it instead of merging everything.
            if current and finding.line - current[-1].line > line_window:
                clusters.append(current)
                current = []
            current.append(finding)
        if current:
            clusters.append(current)

    return clusters


if __name__ == "__main__":
    # SKILL.md's dispatch invokes this as a subprocess via stdin/stdout JSON, not an import.
    import json
    import sys

    raw = json.load(sys.stdin)
    try:
        findings = [Finding(**item) for item in raw]
    except TypeError as exc:
        print(
            f"fingerprint_group: malformed finding in stdin JSON: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    clustered = group_findings(findings)
    out = [[item.__dict__ for item in cluster] for cluster in clustered]
    json.dump(out, sys.stdout, indent=2)
