"""
Legacy shim for tui/logger.py.
Redirects to core/logging_config.py.
"""

from core.logging_config import (
    setup_global_logging as setup_logging,
    setup_root_file_logging,
    get_logger,
    log_exception,
    log_command_execution,
    trace,
    get_log_files_info,
    CLI_LOG_FILE,
    ERROR_LOG_FILE,
    DEBUG_LOG_FILE,
    ANALYSIS_LOG_FILE
)

# Stub for MemoryHandler since it was removed/replaced by TUI direct logging
class MemoryHandler:
    def get_records(self): return []
    def clear(self): pass

# Constants
LOG_STYLE_MAP = {} # Should be imported from constants if needed, but logger shouldn't export it ideally.

