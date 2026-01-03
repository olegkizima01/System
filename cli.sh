#!/bin/zsh
set -euo pipefail
IFS=$'\n\t'

# System Vision CLI Entry Point
# Ensures robust execution with correct Python environment and permissions.

# 1. Determine Script Directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Environment Configuration
VENV_DIR="$SCRIPT_DIR/.venv"
ENV_FILE="$SCRIPT_DIR/.env"

load_env_file() {
    local env_path="$1"
    [ -f "$env_path" ] || return 0

    local line
    local key
    local value

    while IFS= read -r line || [ -n "$line" ]; do
        line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        [ -z "$line" ] && continue
        case "$line" in
            \#*) continue ;;
        esac
        case "$line" in
            export\ *) line="${line#export }" ;;
        esac
        case "$line" in
            *=*) ;;
            *) continue ;;
        esac

        key="${line%%=*}"
        value="${line#*=}"

        key="$(printf '%s' "$key" | xargs)"
        [ -z "$key" ] && continue
        case "$key" in
            [A-Za-z_][A-Za-z0-9_]*) ;;
            *) continue ;;
        esac

        value="$(printf '%s' "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        if [ "${#value}" -ge 2 ]; then
            if [ "${value#\"}" != "$value" ] && [ "${value%\"}" != "$value" ]; then
                value="${value#\"}"
                value="${value%\"}"
            elif [ "${value#\'}" != "$value" ] && [ "${value%\'}" != "$value" ]; then
                value="${value#\'}"
                value="${value%\'}"
            fi
        fi

        export "$key=$value"
    done < "$env_path"
}

load_env_file "$ENV_FILE"

# 3. Python Selection
PYTHON_EXE=""

if [ -n "${SYSTEM_CLI_PYTHON-}" ]; then
    PYTHON_EXE="$SYSTEM_CLI_PYTHON"
elif [ -x "$VENV_DIR/bin/python" ]; then
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate" || true
    fi
    PYTHON_EXE="$VENV_DIR/bin/python"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Attempting to use system python (not recommended)..."
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_EXE="python3.11"
    else
        PYTHON_EXE="python3"
    fi
fi

if [ "${PYTHON_EXE#/}" != "$PYTHON_EXE" ]; then
    if [ ! -x "$PYTHON_EXE" ]; then
        echo "❌ Error: Python executable is not executable: $PYTHON_EXE"
        exit 1
    fi
else
    if ! command -v "$PYTHON_EXE" >/dev/null 2>&1; then
        echo "❌ Error: Python executable not found on PATH: $PYTHON_EXE"
        exit 1
    fi
fi

# 4. Version Check (Fast)
# Check if we can trust the python executable name/path or just do a quick check
# Only invoke python if absolutely necessary.
if ! "$PYTHON_EXE" -c 'import sys; assert sys.version_info >= (3, 11)' 2>/dev/null; then
    PY_VER=$("$PYTHON_EXE" --version 2>&1)
    echo "❌ Error: Python 3.11+ is required. Found $PY_VER."
    exit 1
fi

# 5. Permission Handling (SUDO)
# Securely handle sudo password if provided
SUDO_ASKPASS_SCRIPT=""
SUDO_ASKPASS_IS_TEMP=0
if [ -n "${SUDO_PASSWORD-}" ]; then
    export SUDO_PASSWORD
    if [ -f "$SCRIPT_DIR/scripts/cleanup/sudo_helper.sh" ]; then
        SUDO_ASKPASS_SCRIPT="$SCRIPT_DIR/scripts/cleanup/sudo_helper.sh"
    elif [ -f "$SCRIPT_DIR/sudo_helper.sh" ]; then
        SUDO_ASKPASS_SCRIPT="$SCRIPT_DIR/sudo_helper.sh"
    fi

    if [ -n "$SUDO_ASKPASS_SCRIPT" ]; then
        chmod 700 "$SUDO_ASKPASS_SCRIPT" 2>/dev/null || true
        export SUDO_ASKPASS="$SUDO_ASKPASS_SCRIPT"
        if ! command sudo -A -k true 2>/dev/null; then
            echo "⚠️  Warning: SUDO_PASSWORD provided but sudo validation failed."
        fi
    else
        echo "⚠️  Warning: SUDO_PASSWORD provided but sudo helper script not found."
    fi
fi

# 6. Execute Application
export TOKENIZERS_PARALLELISM=false
# Only log launch message if not in quiet mode (could be added later)
echo "🚀 Launching System CLI with $PYTHON_EXE..."

# Trap cleanup to run on exit
cleanup() {
    if [ "${SUDO_ASKPASS_IS_TEMP:-0}" = "1" ] && [ -n "${SUDO_ASKPASS_SCRIPT:-}" ] && [ -f "${SUDO_ASKPASS_SCRIPT:-}" ]; then
        rm -f "${SUDO_ASKPASS_SCRIPT:-}"
    fi
}
trap cleanup EXIT INT TERM

"$PYTHON_EXE" "$SCRIPT_DIR/cli.py" "$@"