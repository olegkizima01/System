#!/usr/bin/env python3
"""cli.py - Entry point for the System CLI.

The main implementation is located in `tui/cli.py`.
This file serves as a minimal wrapper to ensure proper path configuration and encoding.
"""

from __future__ import annotations

import os
import sys

from core.logging_config import setup_global_logging, get_logger, log_exception

# Silence ChromaDB/PostHog telemetry globally
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# Ensure project root is in path
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Ensure stdin is utf-8 to prevent encoding errors
try:
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
except Exception:
    pass


def main() -> None:
    try:
        setup_global_logging(verbose=False)

        # Transform args if necessary (Natural Language Support)
        # Lazy import to keep startup fast
        from tui.cli_helpers import parse_natural_language_args
        sys.argv = parse_natural_language_args(sys.argv)

        from tui.cli import main as tui_main
        tui_main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        logger = get_logger("system_cli.cli")
        log_exception(logger, e, "cli.py main()")
        sys.exit(1)


if __name__ == "__main__":
    main()
