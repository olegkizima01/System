#!/usr/bin/env bash
# Lightweight launcher that executes the project `cli.py` using either the project's
# virtualenv (`.venv`) or the pyenv/global Python.
#
# Installs read config from: $HOME/.config/system/system.conf
# CONFIG file format (simple KEY=VALUE lines):
#   PROJECT_ROOT=/path/to/System

set -euo pipefail

CONFIG_DIR="$HOME/.config/system"
CONFIG_FILE="$CONFIG_DIR/system.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration not found: $CONFIG_FILE"
    echo "Run: scripts/install_global_launcher.sh /path/to/System"
    exit 1
fi

# Load config (simple KEY=VALUE parsing)
PROJECT_ROOT=""
while IFS='=' read -r key value; do
    case "$key" in
        PROJECT_ROOT) PROJECT_ROOT="$value" ;;
    esac
done < "$CONFIG_FILE"

if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ PROJECT_ROOT not set in $CONFIG_FILE"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ PROJECT_ROOT does not exist: $PROJECT_ROOT"
    exit 1
fi

# Prefer project's virtualenv
if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    PY_EXE="$PROJECT_ROOT/.venv/bin/python"
else
    # Fall back to pyenv-shim or system python
    if command -v pyenv &>/dev/null; then
        PY_EXE="$(pyenv which python 2>/dev/null || which python3)"
    else
        PY_EXE="$(which python3 || which python)"
    fi
fi

if [ -z "$PY_EXE" ]; then
    echo "❌ No Python executable found. Install Python or set up .venv in project root."
    exit 1
fi

exec "$PY_EXE" "$PROJECT_ROOT/cli.py" "$@"
