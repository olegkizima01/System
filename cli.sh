#!/bin/zsh

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
    export $(grep -v '^#' "$ENV_FILE" | xargs)
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

# 4. Version Check
PY_VER=$("$PYTHON_EXE" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
if [[ "$PY_VER" != "3.11"* ]]; then
    # Allow 3.12/3.13 if absolutely necessary but warn
    if [[ "$PY_VER" == "3.12"* ]] || [[ "$PY_VER" == "3.13"* ]]; then
        echo "⚠️  Warning: Using Python $PY_VER. Python 3.11 is recommended."
    else
        echo "❌ Error: Python 3.11+ is required. Found $PY_VER."
        exit 1
    fi
fi

# 5. Permission Handling (SUDO)
# If sudo password is known, set up askpass for non-interactive sudo usage
if [ -n "$SUDO_PASSWORD" ]; then
    SUDO_ASKPASS_DIR="$HOME/.system_cli"
    mkdir -p "$SUDO_ASKPASS_DIR"
    SUDO_ASKPASS_SCRIPT="$SUDO_ASKPASS_DIR/.sudo_askpass"
    
    # Verify password validity quietly
    echo "$SUDO_PASSWORD" | sudo -S -k true 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "#!/bin/bash" > "$SUDO_ASKPASS_SCRIPT"
        echo "echo \"$SUDO_PASSWORD\"" >> "$SUDO_ASKPASS_SCRIPT"
        chmod 700 "$SUDO_ASKPASS_SCRIPT"
        export SUDO_ASKPASS="$SUDO_ASKPASS_SCRIPT"
    else
        echo "Detailed Warning: SUDO_PASSWORD provided but invalid."
    fi
fi

# 6. Execute Application
export TOKENIZERS_PARALLELISM=false
echo "🚀 Launching System CLI with $PYTHON_EXE..."
"$PYTHON_EXE" "$SCRIPT_DIR/cli.py" "$@"

# 7. Cleanup
if [ -n "$SUDO_ASKPASS_SCRIPT" ] && [ -f "$SUDO_ASKPASS_SCRIPT" ]; then
    rm "$SUDO_ASKPASS_SCRIPT"
fi