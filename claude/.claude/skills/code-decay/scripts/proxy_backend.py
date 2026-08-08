#!/usr/bin/env python3
"""Agnostic Proxy Backend: regex/indent-based branch_count + max_nesting_depth
for any language outside the ast-grep v1 set — never errors, always returns a
value, deliberately rougher than an AST-backed measurement."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path

_CX_TYPES_MODULE_NAME = "code_decay_cx_types"
# Reuse an already-registered load: ast_grep_backend.py, this file, and
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

# Deliberately broad and language-agnostic (covers C-family, Ruby, Lua-ish,
# etc. keywords at once) — precision isn't the goal here, "never errors,
# always returns a value" is. A miscount on an unsupported language is an
# accepted rougher estimate, not a bug.
BRANCH_KEYWORDS = re.compile(
    r"\b(if|elif|elseif|for|foreach|while|switch|case|catch|unless)\b"
)

# Fallback indent unit when a file uses space-only indentation but no
# consistent step can be inferred (e.g. every line is at column 0).
DEFAULT_INDENT_UNIT = 2


def _detect_indent_unit(lines: list[str]) -> int:
    # Mode of the deepening steps (indent increases vs. the prior non-blank
    # line), not the global min space-run — a single stray 1-space-indented
    # comment/continuation line anywhere in the file would otherwise collapse
    # the whole file's unit to 1 and inflate every real indent's depth.
    deltas = []
    previous_indent = 0
    for line in lines:
        if not line.strip() or line.startswith("\t"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent > previous_indent:
            deltas.append(indent - previous_indent)
        previous_indent = indent
    if not deltas:
        return DEFAULT_INDENT_UNIT
    return Counter(deltas).most_common(1)[0][0]


def _indent_level(line: str, indent_unit: int) -> int:
    stripped = line.rstrip("\n")
    leading = len(stripped) - len(stripped.lstrip(" \t"))
    prefix = stripped[:leading]
    # Each tab is one level on its own — the guarantee that nesting depth is
    # non-zero on tab-indented files rests on this, not on space division.
    tab_levels = prefix.count("\t")
    space_levels = prefix.count(" ") // indent_unit
    return tab_levels + space_levels


def compute(file_path: str) -> Cx:
    try:
        content = Path(file_path).read_text(errors="replace")
    except OSError:
        return Cx(branch_count=0, nesting_depth=0)

    lines = content.splitlines()
    indent_unit = _detect_indent_unit(lines)
    nesting_depth = max((_indent_level(line, indent_unit) for line in lines), default=0)
    branch_count = len(BRANCH_KEYWORDS.findall(content))
    return Cx(branch_count=branch_count, nesting_depth=nesting_depth)


if __name__ == "__main__":
    result = compute(sys.argv[1])
    print(f"branch_count={result.branch_count} nesting_depth={result.nesting_depth}")
