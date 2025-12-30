#!/bin/bash

# Log Cleanup Cron Setup Script
# This script sets up automatic log cleanup using cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Path to the cleanup script
CLEANUP_SCRIPT="$PROJECT_ROOT/scripts/utils/cleanup_logs.py"

# Check if the cleanup script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "Error: Cleanup script not found at $CLEANUP_SCRIPT"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# Create cron job entry
CRON_JOB="0 3 * * * /usr/bin/python3 $CLEANUP_SCRIPT --clean-old --days 30 --clean-large --size 50 >> $PROJECT_ROOT/logs/log_cleanup.log 2>&1"

# Add to crontab
echo "Setting up cron job for log cleanup..."

# Backup existing crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added successfully!"
echo "Log cleanup will run daily at 3:00 AM"
echo "Logs will be written to: $PROJECT_ROOT/logs/log_cleanup.log"

# Show current crontab
echo -e "\nCurrent crontab:"
crontab -l