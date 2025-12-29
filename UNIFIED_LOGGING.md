# Trinity Runtime - Unified Logging System

## 🎯 Logging System Overview

This document provides comprehensive information about the unified logging system in Trinity Runtime, including log locations, formats, and best practices.

## 📋 Log File Locations

### Primary Log Directory
```
~/.system_cli/logs/
```

All logs are stored in this centralized directory for easy access and management.

### Main Log Files

1. **cli.log** - Main application log
   - Location: `~/.system_cli/logs/cli.log`
   - Format: Detailed with timestamps
   - Rotation: 10 MB, 5 backups

2. **errors.log** - Error-specific log
   - Location: `~/.system_cli/logs/errors.log`
   - Format: Detailed with timestamps
   - Rotation: 5 MB, 3 backups

3. **debug.log** - Debug information log
   - Location: `~/.system_cli/logs/debug.log`
   - Format: Detailed with timestamps
   - Rotation: 50 MB, 5 backups

4. **atlas_analysis.jsonl** - Analysis log for AI
   - Location: `~/.system_cli/logs/atlas_analysis.jsonl`
   - Format: JSON Lines
   - Rotation: 50 MB, 5 backups

5. **trinity_state_{date}.log** - State transition log
   - Location: `~/.system_cli/logs/trinity_state_{date}.log`
   - Format: Detailed with timestamps
   - Rotation: Daily files

### Legacy Log Files (if used)

1. **left_screen.log** - Left screen log
   - Location: `{root_dir}/logs/left_screen.log`
   - Format: Simple with timestamps
   - Rotation: 10 MB, 3 backups

2. **right_screen.log** - Right screen log
   - Location: `{root_dir}/logs/right_screen.log`
   - Format: Simple with timestamps
   - Rotation: 10 MB, 3 backups

## 📊 Log Formats

### Simple Format
```
%(asctime)s | %(levelname)-8s | %(message)s
```

Example:
```
2025-12-25 14:30:45 | INFO     | Task execution started
```

### Detailed Format
```
%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s
```

Example:
```
2025-12-25 14:30:45 | INFO     | trinity.core | run:42 | Task execution started
```

### JSON Format (for AI analysis)
```json
{
  "timestamp": "2025-12-25T14:30:45.123456",
  "level": "INFO",
  "logger": "trinity.core",
  "message": "Task execution started",
  "module": "runtime",
  "func": "run",
  "line": 42,
  "thread": "MainThread"
}
```

## 🔧 Logging Configuration

### Setup Global Logging
```python
from core.logging_config import setup_global_logging

# Basic setup
logger = setup_global_logging(verbose=True)

# With TUI integration
logger = setup_global_logging(
    verbose=True,
    tui_state_callback=lambda: tui_state  # Return TUI state object
)

# With custom root directory
logger = setup_global_logging(
    verbose=True,
    root_dir="/custom/path"
)
```

### Get Logger
```python
from core.logging_config import get_logger

# Get default logger
logger = get_logger()

# Get named logger
logger = get_logger("trinity.core")

# Get agent-specific logger
agent_logger = get_logger("trinity.right")  # Right screen/agent
```

## 📋 Logging Best Practices

### Basic Logging
```python
logger = get_logger(__name__)

# Different log levels
logger.debug("Debug message")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Exception Logging
```python
try:
    # Some operation
    result = risky_operation()
except Exception as e:
    logger.exception("Exception during operation")
    # Or with context
    log_exception(logger, e, "risky_operation")
```

### Command Execution Logging
```python
log_command_execution(
    logger,
    cmd="ls -la",
    cwd="/home/user",
    returncode=0,
    stdout="file1.txt\nfile2.txt",
    stderr=""
)
```

### Trace Events (for AI analysis)
```python
trace(logger, "task_started", {
    "task_id": "123",
    "task_type": "execution",
    "agent": "tetyana"
})
```

## 🔍 Log Management

### Get Log File Information
```python
from core.logging_config import get_log_files_info

log_info = get_log_files_info()
print(f"Log directory: {log_info['logs_dir']}")
for filename, info in log_info['files'].items():
    print(f"{filename}: {info['size_mb']:.2f} MB" if info['exists'] else f"{filename}: Not found")
```

### Log Rotation
- Automatic rotation based on file size
- Configurable backup count
- Prevents log files from growing too large

### Log Retention
- Configured in `core/logging_config.py`
- Default: Keep 3-5 backup files
- Adjustable based on needs

## 🎯 Unified Logging Strategy

### Centralized Logging
All logs are centralized in `~/.system_cli/logs/` for:
- Easy access and management
- Consistent format across components
- Simplified monitoring and analysis

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **CRITICAL**: Critical failures

### Log Suppression
Noisy libraries are automatically suppressed:
- urllib3
- chromadb
- backoff
- posthog
- watchdog

## 📊 Monitoring and Analysis

### Log Analysis Tools
```bash
# View recent logs
tail -f ~/.system_cli/logs/cli.log

# Search for errors
grep "ERROR" ~/.system_cli/logs/cli.log

# Monitor in real-time
tail -f ~/.system_cli/logs/*.log | grep "INFO"
```

### Log Analysis with AI
```python
# Read analysis log for AI processing
with open('~/.system_cli/logs/atlas_analysis.jsonl') as f:
    for line in f:
        analysis_data = json.loads(line)
        # Process analysis data
```

## 🚀 Production Logging Setup

### Recommended Configuration
```python
# Production setup
logger = setup_global_logging(
    verbose=False,  # No console output in production
    tui_state_callback=None  # No TUI in production
)

# Add additional handlers if needed
production_handler = logging.FileHandler('production.log')
production_handler.setLevel(logging.INFO)
logger.addHandler(production_handler)
```

### Log Retention Policy
```python
# Configure in logging_config.py
file_handler = logging.handlers.RotatingFileHandler(
    CLI_LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,  # Keep 5 backup files
    encoding="utf-8"
)
```

## 📋 Troubleshooting

### Common Issues

**Issue: Logs not appearing**
- Check log file permissions
- Verify log directory exists
- Ensure logger is properly configured

**Issue: Logs too verbose**
- Adjust log level: `logger.setLevel(logging.WARNING)`
- Suppress specific libraries

**Issue: Log files too large**
- Adjust rotation size
- Reduce backup count
- Implement log archiving

### Debugging Tips

1. **Check log directory**:
   ```bash
   ls -la ~/.system_cli/logs/
   ```

2. **Verify log configuration**:
   ```python
   import logging
   print(logging.getLogger().handlers)
   ```

3. **Test logging**:
   ```python
   logger = get_logger()
   logger.info("Test message")
   ```

## 🎉 Conclusion

The unified logging system provides:
- ✅ **Centralized logging** in `~/.system_cli/logs/`
- ✅ **Consistent formats** across all components
- ✅ **Automatic rotation** to prevent large files
- ✅ **Multiple log levels** for different needs
- ✅ **JSON logging** for AI analysis
- ✅ **Easy access** for monitoring and debugging

All logging now points to the correct, unified locations with no outdated references.

---

*Unified Logging Documentation: December 2025*
*Trinity Runtime Version: 2.5*
*Status: Complete and Unified*