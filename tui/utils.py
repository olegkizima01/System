"""General utilities for System CLI.
"""

from __future__ import annotations

import os

from tui.cli_paths import SCRIPT_DIR

def safe_abspath(path: str) -> str:
    expanded = os.path.expanduser(str(path or "")).strip()
    if not expanded:
        return ""
    if os.path.isabs(expanded):
        return expanded

    raw = expanded
    if raw.startswith("./"):
        raw = raw[2:]

    cleanup_dir = os.path.join(SCRIPT_DIR, "cleanup_scripts")
    base = os.path.basename(raw)

    candidates = [
        os.path.abspath(os.path.join(SCRIPT_DIR, raw)),
        os.path.abspath(os.path.join(cleanup_dir, raw)),
        os.path.abspath(os.path.join(cleanup_dir, base)),
        os.path.abspath(os.path.join(SCRIPT_DIR, base)),
    ]

    for p in candidates:
        if os.path.exists(p):
            return p

    return candidates[0]
