#!/usr/bin/env python3
"""Report Renderer: writes docs/code-decay/<repo>-YYYY-MM-DD.md INSIDE the
target repo being analyzed (not dotfiles) — plaintext, one new dated file per
run rather than an overwrite, so hotspot reports diff across dates (FR-14).
Never adds or checks a git-crypt pattern — a hotspot report isn't sensitive
(NFR-03)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parent


def _load_sibling(module_name: str, file_name: str):
    loader = importlib.machinery.SourceFileLoader(
        f"code_decay_{module_name}", str(_SCRIPTS_DIR / file_name)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


# Score comes from the Scorer, not a second copy of `churn * cx` — FR-08
# traces to one implementation, and the report must show what that
# implementation actually produces.
scorer = _load_sibling("scorer", "scorer.py")

TABLE_HEADER = ("File", "Churn", "Cx", "Score", "Label")


def render_report(
    repo_path: str,
    rows: dict[str, tuple[int, int]],
    labels: dict[str, str | None],
    report_date: str | None = None,
    interpreted_paths: list[str] | None = None,
    shallow_warning: bool = False,
) -> Path:
    """rows: path -> (churn, cx). labels: path -> label or None.
    `interpreted_paths`: the paths `select_for_interpretation` chose for the
    `--interpret` model pass, or None when `--interpret` wasn't used. States
    the actual count sent — never implies N were sent when fewer cleared the
    floor (FR-10). `shallow_warning`: True when `shallow_guard.is_shallow`
    detected a truncated clone — surfaced IN the report, not only at the
    terminal, since a report read later has no access to that run's stdout
    (FR-05). Returns the path written."""
    resolved_date = report_date or datetime.now().strftime("%Y-%m-%d")
    repo_name = Path(repo_path).name
    output_dir = Path(repo_path) / "docs" / "code-decay"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{repo_name}-{resolved_date}.md"

    scores = scorer.score_files(rows)
    ranked_paths = sorted(rows, key=lambda path: (-scores[path], path))

    lines = [
        f"# code-decay report: {repo_name} ({resolved_date})",
        "",
    ]
    if shallow_warning:
        lines.append(
            "**Warning: shallow clone detected.** Churn numbers reflect only "
            "the truncated history available in this clone and may "
            "understate real hotspots."
        )
        lines.append("")
    lines += [
        f"| {' | '.join(TABLE_HEADER)} |",
        f"|{'---|' * len(TABLE_HEADER)}",
    ]
    for path in ranked_paths:
        churn, cx = rows[path]
        label = labels.get(path) or ""
        lines.append(f"| {path} | {churn} | {cx} | {scores[path]} | {label} |")

    if interpreted_paths is not None:
        lines.append("")
        count = len(interpreted_paths)
        file_word = "file" if count == 1 else "files"
        lines.append(
            f"**Interpret pass:** {count} {file_word} above interpretation "
            "threshold sent for review."
        )

    output_path.write_text("\n".join(lines) + "\n")
    return output_path
