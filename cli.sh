#!/bin/zsh
set -e

# System Vision CLI Entry Point
# Ensures robust execution with correct Python environment and permissions.

# 1. Determine Script Directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 2. Environment Configuration
VENV_DIR="$SCRIPT_DIR/.venv"
ENV_FILE="$SCRIPT_DIR/.env"

# Load .env if it exists
if [ -f "$ENV_FILE" ]; then
    # Safely export vars, ignoring comments and empty lines
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^\s*$' | xargs) 2>/dev/null || true
fi

# 3. Python Selection
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    PYTHON_EXE="$VENV_DIR/bin/python"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Attempting to use system python (not recommended)..."
    PYTHON_EXE="python3"
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
if [ -n "$SUDO_PASSWORD" ]; then
    SUDO_ASKPASS_DIR="$HOME/.system_cli"
    mkdir -p "$SUDO_ASKPASS_DIR"
    SUDO_ASKPASS_SCRIPT="$SUDO_ASKPASS_DIR/.sudo_askpass"
    
    # Verify password validity quietly
    if echo "$SUDO_PASSWORD" | sudo -S -k true 2>/dev/null; then
        # Create askpass script with restrictive permissions
        cat <<EOF > "$SUDO_ASKPASS_SCRIPT"
#!/bin/bash
echo "\$SUDO_PASSWORD"
EOF
        chmod 700 "$SUDO_ASKPASS_SCRIPT"
        export SUDO_ASKPASS="$SUDO_ASKPASS_SCRIPT"
    else
        echo "⚠️  Warning: SUDO_PASSWORD provided but invalid."
    fi
fi

# 6. Execute Application
export TOKENIZERS_PARALLELISM=false
# Only log launch message if not in quiet mode (could be added later)
echo "🚀 Launching System CLI with $PYTHON_EXE..."

# Trap cleanup to run on exit
cleanup() {
    if [ -n "$SUDO_ASKPASS_SCRIPT" ] && [ -f "$SUDO_ASKPASS_SCRIPT" ]; then
        rm -f "$SUDO_ASKPASS_SCRIPT"
    fi
}
trap cleanup EXIT INT TERM

"$PYTHON_EXE" "$SCRIPT_DIR/cli.py" "$@"