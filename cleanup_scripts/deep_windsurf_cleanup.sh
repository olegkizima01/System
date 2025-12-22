#!/bin/bash

# deep_windsurf_cleanup.sh - Specific cleanup for Windsurf editor traces
echo "🌊 Starting deep Windsurf cleanup..."

WINDSURF_LOGS="$HOME/Library/Application Support/Windsurf/logs"
if [ -d "$WINDSURF_LOGS" ]; then
    rm -rf "$WINDSURF_LOGS"/*
    echo "✅ Cleared Windsurf logs."
fi

# Clear global storage if exists (potential traces)
WINDSURF_STORAGE="$HOME/Library/Application Support/Windsurf/User/globalStorage"
if [ -d "$WINDSURF_STORAGE" ]; then
    find "$WINDSURF_STORAGE" -name "*.log" -delete
    echo "✅ Sanitized Windsurf global storage."
fi

echo "✨ Windsurf cleanup completed."
