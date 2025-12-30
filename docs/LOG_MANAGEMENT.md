# Log Management Guide

This guide provides comprehensive information about log management in the System project, including configuration, cleanup procedures, and best practices.

## Table of Contents

- [Log Management Guide](#log-management-guide)
  - [Table of Contents](#table-of-contents)
  - [Log Configuration](#log-configuration)
  - [Log Files Overview](#log-files-overview)
  - [Log Rotation Settings](#log-rotation-settings)
  - [Log Cleanup Utility](#log-cleanup-utility)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Options](#options)
    - [Examples](#examples)
  - [Automatic Log Cleanup with Cron](#automatic-log-cleanup-with-cron)
    - [Setup](#setup)
    - [Verification](#verification)
    - [Customization](#customization)
  - [Manual Log Cleanup](#manual-log-cleanup)
  - [Log Analysis](#log-analysis)
  - [Best Practices](#best-practices)
  - [Troubleshooting](#troubleshooting)

## Log Configuration

The logging system is configured in `core/logging_config.py`. Key features:

- **Rotating log files**: Automatic rotation when files reach maximum size
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR
- **JSON formatting**: Structured logging for AI analysis
- **Multiple handlers**: File, console, and TUI handlers

## Log Files Overview

The system generates several types of log files:

1. **Main Logs** (`~/.system_cli/logs/`):
   - `cli.log`: Main application log
   - `errors.log`: Error-specific log
   - `debug.log`: Detailed debugging information
   - `atlas_analysis.jsonl`: Structured JSON logs for analysis

2. **Screen Logs** (`logs/`):
   - `left_screen.log`: Left screen output
   - `right_screen.log`: Right screen/agent output
   - `trinity_state_*.log`: Daily state logs

3. **Task Logs** (`task_logs/`):
   - `task_*.log`: Individual task execution logs

4. **Archive Logs** (`archive/logs/`):
   - Various archived log files

## Log Rotation Settings

Current rotation settings (after optimization):

| Log Type | Max Size | Backup Count |
|----------|----------|--------------|
| Main CLI Log | 5 MB | 3 |
| Error Log | 2 MB | 2 |
| JSON Analysis Log | 10 MB | 3 |
| Screen Logs | 5 MB | 2 |

## Log Cleanup Utility

The `cleanup_logs.py` utility helps manage log files efficiently.

### Installation

The utility is located at:
```bash
scripts/utils/cleanup_logs.py
```

### Usage

```bash
python3 scripts/utils/cleanup_logs.py [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--days N` | Delete files older than N days | 30 |
| `--size N` | Archive files larger than N MB | 50 |
| `--dry-run` | Show what would be done without actually doing it | False |
| `--stats` | Show log statistics only | False |
| `--clean-old` | Cleanup old files | False |
| `--clean-large` | Cleanup large files | False |

### Examples

1. **Show log statistics**:
```bash
python3 scripts/utils/cleanup_logs.py --stats
```

2. **Clean old logs (older than 30 days)**:
```bash
python3 scripts/utils/cleanup_logs.py --clean-old --days 30
```

3. **Clean large logs (larger than 50 MB)**:
```bash
python3 scripts/utils/cleanup_logs.py --clean-large --size 50
```

4. **Dry run (show what would be deleted)**:
```bash
python3 scripts/utils/cleanup_logs.py --clean-old --days 30 --dry-run
```

5. **Full cleanup (old and large files)**:
```bash
python3 scripts/utils/cleanup_logs.py --clean-old --clean-large
```

## Automatic Log Cleanup with Cron

### Setup

Use the provided setup script:
```bash
./scripts/utils/setup_log_cleanup_cron.sh
```

This will:
1. Add a cron job to run daily at 3:00 AM
2. Clean logs older than 30 days
3. Archive logs larger than 50 MB
4. Log cleanup operations to `logs/log_cleanup.log`

### Verification

Check that the cron job was added:
```bash
crontab -l
```

You should see:
```
0 3 * * * /usr/bin/python3 /path/to/System/scripts/utils/cleanup_logs.py --clean-old --days 30 --clean-large --size 50 >> /path/to/System/logs/log_cleanup.log 2>&1
```

### Customization

To customize the cron schedule or parameters:

1. Edit your crontab:
```bash
crontab -e
```

2. Modify the existing line or add a new one with different parameters

Example (run weekly on Sundays at 2:30 AM):
```
30 2 * * 0 /usr/bin/python3 /path/to/System/scripts/utils/cleanup_logs.py --clean-old --days 60 --clean-large --size 100 >> /path/to/System/logs/log_cleanup.log 2>&1
```

## Manual Log Cleanup

For manual cleanup operations:

1. **Check current log usage**:
```bash
python3 scripts/utils/cleanup_logs.py --stats
```

2. **Clean specific logs**:
```bash
# Clean logs older than 7 days
python3 scripts/utils/cleanup_logs.py --clean-old --days 7

# Clean logs larger than 25 MB
python3 scripts/utils/cleanup_logs.py --clean-large --size 25
```

3. **Comprehensive cleanup**:
```bash
python3 scripts/utils/cleanup_logs.py --clean-old --clean-large
```

## Log Analysis

### Viewing Logs

Use standard Unix tools to view logs:

```bash
# View end of a log file
tail -n 50 ~/.system_cli/logs/cli.log

# Follow a log file in real-time
tail -f ~/.system_cli/logs/cli.log

# Search for errors
grep -i error ~/.system_cli/logs/cli.log

# Search in JSON logs
cat ~/.system_cli/logs/atlas_analysis.jsonl | jq 'select(.level == "ERROR")'
```

### Log Analysis Tools

For more advanced analysis:

```bash
# Count log entries by level
cat ~/.system_cli/logs/cli.log | grep -E "(INFO|WARNING|ERROR)" | sort | uniq -c

# Find most frequent errors
cat ~/.system_cli/logs/errors.log | jq -r '.message' | sort | uniq -c | sort -nr | head -10
```

## Best Practices

1. **Regular Monitoring**: Check log statistics weekly using `--stats` option
2. **Rotation Settings**: Adjust rotation settings based on your usage patterns
3. **Backup Important Logs**: Before major cleanup operations, consider backing up important logs
4. **Log Retention Policy**: Establish a clear log retention policy (e.g., 30 days for most logs, 90 days for critical logs)
5. **Disk Space Monitoring**: Monitor disk space usage in your log directories

## Troubleshooting

### Common Issues

**Issue: Log files growing too quickly**
- Solution: Reduce log level or adjust rotation settings

**Issue: Cleanup script not working**
- Solution: Check permissions and Python environment

**Issue: Cron job not running**
- Solution: Check cron logs and verify the cron service is running

### Debugging Cleanup Operations

Check the cleanup log:
```bash
tail -n 20 logs/log_cleanup.log
```

Run with verbose output:
```bash
python3 -v scripts/utils/cleanup_logs.py --clean-old --days 30
```

### Manual Cleanup in Emergency

If automated tools fail:

```bash
# Find and delete large log files
find ~/.system_cli/logs/ -name "*.log" -size +50M -exec ls -lh {} \;

# Delete specific old files
find ~/.system_cli/logs/ -name "*.log.*" -mtime +30 -delete
```

## Conclusion

Proper log management is essential for maintaining system performance and ensuring you have the right information when troubleshooting. This guide provides the tools and knowledge needed to effectively manage logs in the System project.