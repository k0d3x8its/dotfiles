#!/usr/bin/env python3
"""ast-grep Backend: per-language branch_count + max_nesting_depth via `ast-grep
run --kind`, never a metavariable pattern (kind-based works on bash; patterns
like `$A=$B` don't)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# No `sys.path` mutation, no bare "cx_types" name in sys.modules — this
# skill's scripts/ dir has no package boundary to import through, but the
# module-level side effect a plain `sys.path.insert` + `import` causes is
# still worth avoiding (PYTHON.md AVOID). Keyed by absolute path under a
# repo-unique name instead.
_CX_TYPES_MODULE_NAME = "code_decay_cx_types"
# Reuse an already-registered load: this file, proxy_backend.py, and
# complexity.py can all load cx_types.py in the same process, and each fresh
# exec_module() would mint a distinct Cx class — breaking equality between a
# Cx returned by this backend and one returned by the other.
_cx_types = sys.modules.get(_CX_TYPES_MODULE_NAME)
if _cx_types is None:
    _loader = importlib.machinery.SourceFileLoader(
        _CX_TYPES_MODULE_NAME, str(Path(__file__).parent / "cx_types.py")
    )
    _spec = importlib.util.spec_from_loader(_loader.name, _loader)
    _cx_types = importlib.util.module_from_spec(_spec)
    # dataclass + `from __future__ import annotations` needs the module
    # resolvable via sys.modules[cls.__module__] while its class body runs.
    sys.modules[_loader.name] = _cx_types
    _loader.exec_module(_cx_types)
Cx = _cx_types.Cx

# Kind names come from each language's own tree-sitter grammar, not a shared
# vocabulary — verified empirically per language (fixtures in
# .work/findings/, one `ast-grep run --kind <name>` probe per candidate) since
# grammars disagree on naming (JS has do_statement/switch_statement, Solidity
# has neither). Lua's `for_statement` covers both numeric and generic `for`
# forms — confirmed 2 matches on a fixture with one of each, not two kinds.
BRANCH_KINDS: dict[str, tuple[str, ...]] = {
    "python": ("if_statement", "for_statement", "while_statement"),
    "javascript": (
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
    ),
    "typescript": (
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
    ),
    "tsx": (
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
    ),
    "lua": ("if_statement", "for_statement", "while_statement", "repeat_statement"),
    "bash": ("if_statement", "for_statement", "while_statement", "case_statement"),
    "c": (
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
    ),
    "cpp": (
        "if_statement",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
    ),
    "solidity": ("if_statement", "for_statement", "while_statement"),
}


class AstGrepBackendError(RuntimeError):
    """Raised when `ast-grep` is missing, unreachable, or exits with a real
    error. Fail loud — 2026-07-27 decision: a silent proxy fallback would
    hide a broken install as an accuracy problem instead of a setup
    problem."""


def _match_ranges(lang: str, kind: str, file_path: str) -> list[tuple[int, int]]:
    try:
        result = subprocess.run(
            [
                "ast-grep",
                "run",
                "--lang",
                lang,
                "--kind",
                kind,
                "--json=compact",
                file_path,
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise AstGrepBackendError(
            "ast-grep binary not found on PATH — install it or repair the "
            "environment; this backend never silently degrades to the proxy."
        ) from error
    # ast-grep exits 1 whenever a kind matches nothing in the file — a normal
    # outcome (most files have no `switch_statement`, say), not a failure.
    # Only >1 is a real problem (bad --lang, unreadable file).
    if result.returncode not in (0, 1):
        raise AstGrepBackendError(
            f"ast-grep failed on {file_path} ({lang}/{kind}): {result.stderr.strip()}"
        )
    matches = json.loads(result.stdout)
    return [
        (match["range"]["byteOffset"]["start"], match["range"]["byteOffset"]["end"])
        for match in matches
    ]


def _max_containment_depth(ranges: list[tuple[int, int]]) -> int:
    # Same algorithm as the /prototype pass that locked cx = branch_count +
    # max_nesting_depth: a node's depth is 1 + how many other matched nodes
    # fully contain it, so the deepest branch/loop nest wins regardless of
    # which kind produced which node.
    max_depth = 0
    for start, end in ranges:
        depth = 1 + sum(
            1
            for other_start, other_end in ranges
            if (other_start, other_end) != (start, end)
            and other_start <= start
            and end <= other_end
        )
        max_depth = max(max_depth, depth)
    return max_depth


def compute(file_path: str, lang: str) -> Cx:
    kinds = BRANCH_KINDS.get(lang, ())
    ranges = [
        match_range
        for kind in kinds
        for match_range in _match_ranges(lang, kind, file_path)
    ]
    return Cx(branch_count=len(ranges), nesting_depth=_max_containment_depth(ranges))


if __name__ == "__main__":
    target = Path(sys.argv[1])
    result = compute(str(target), sys.argv[2])
    print(f"branch_count={result.branch_count} nesting_depth={result.nesting_depth}")
