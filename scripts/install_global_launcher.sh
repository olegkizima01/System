#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: $0 [PATH_TO_PROJECT]"
    echo "Installs launcher to: $HOME/.local/bin/system-vision"
    echo "Creates config in: $HOME/.config/system/system.conf"
}

PROJECT_ROOT="${1:-$(pwd)}"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Project root does not exist: $PROJECT_ROOT"
    usage
    exit 1
fi

BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/system"
LAUNCHER_SRC="$(pwd)/scripts/system-vision-launcher.sh"
LAUNCHER_DEST="$BIN_DIR/system-vision"

mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"

echo "📋 Installing launcher to: $LAUNCHER_DEST"
cp "$LAUNCHER_SRC" "$LAUNCHER_DEST"
chmod +x "$LAUNCHER_DEST"

CONFIG_FILE="$CONFIG_DIR/system.conf"
echo "PROJECT_ROOT=$PROJECT_ROOT" > "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

echo "✅ Installed launcher."
echo "  - Launcher: $LAUNCHER_DEST"
echo "  - Config: $CONFIG_FILE"

echo "💡 Make sure $HOME/.local/bin is in your PATH. Add to your shell profile if needed:
  export PATH=\"$HOME/.local/bin:$PATH\""

echo "🔧 You can now run: system-vision"
