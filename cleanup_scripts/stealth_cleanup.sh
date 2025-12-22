#!/bin/bash

# stealth_cleanup.sh - Removes traces of activity
echo "🧹 Starting stealth cleanup..."

# 1. Clear Trinity logs
find ./logs -name "trinity_state_*.log" -type f -mtime +1 -delete
echo "✅ Trimmed old state logs."

# 2. Clear task screenshots and logs
rm -rf ./task_screenshots/*
rm -rf ./task_logs/*
echo "✅ Cleared screenshots and task logs."

# 3. Clear system caches (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    rm -rf ~/Library/Caches/com.apple.Safari/ReadingListArchives/* 2>/dev/null
    echo "✅ Cleared Safari archives."
fi

echo "✨ Stealth cleanup completed."
