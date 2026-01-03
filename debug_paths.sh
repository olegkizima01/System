#!/bin/zsh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/scripts/cleanup/common_functions.sh"

echo "WINDSURF_PATH: |${EDITOR_PATHS[windsurf]}|"
echo "VSCODE_PATH: |${EDITOR_PATHS[vscode]}|"
echo "ZSH_VERSION: $ZSH_VERSION"
echo "BASH_VERSION: $BASH_VERSION"

ls -l "$HOME/Library/Application Support/Windsurf/User/globalStorage/state.vscdb"
