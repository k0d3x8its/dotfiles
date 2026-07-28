#!/usr/bin/env python3
"""Complexity Dispatcher: routes a file to the ast-grep backend (v1 languages)
or the agnostic proxy backend (everything else) by extension. No downstream
code branches on which backend answered — both return the same `Cx` shape."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parent


def _load_sibling(module_name: str, file_name: str):
    loader = importlib.machinery.SourceFileLoader(
        f"code_decay_{module_name}", str(_SCRIPTS_DIR / file_name)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    # dataclass + `from __future__ import annotations` needs the module
    # resolvable via sys.modules[cls.__module__] while its class body runs —
    # matters for cx_types.py; harmless for the others.
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


ast_grep_backend = _load_sibling("ast_grep_backend", "ast_grep_backend.py")
proxy_backend = _load_sibling("proxy_backend", "proxy_backend.py")
# Reuse the Cx class ast_grep_backend already loaded rather than loading
# cx_types.py a third time under this module's own sys.modules key.
Cx = ast_grep_backend.Cx

# `.ino` maps straight to "cpp" here — this IS the "no language-mapping
# config" guarantee: one dict entry in code, not a config file a user has to
# maintain or discover.
EXTENSION_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".lua": "lua",
    ".sh": "bash",
    ".bash": "bash",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".ino": "cpp",
    ".sol": "solidity",
}


def complexity(file_path: str) -> Cx:
    lang = EXTENSION_TO_LANG.get(Path(file_path).suffix)
    if lang is not None:
        return ast_grep_backend.compute(file_path, lang)
    return proxy_backend.compute(file_path)


if __name__ == "__main__":
    result = complexity(sys.argv[1])
    print(
        f"cx={result.value} branch_count={result.branch_count} "
        f"nesting_depth={result.nesting_depth}"
    )
