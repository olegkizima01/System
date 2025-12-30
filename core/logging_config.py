"""
Unified Logging System for Trinity/Kinotavr.

This module replaces `tui/logger.py` and provides a centralized way to configure
logging for both the CLI/TUI and the backend agents.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# --- Constants ---

LOGS_DIR = Path.home() / ".system_cli" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Main log files
CLI_LOG_FILE = LOGS_DIR / "cli.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug.log"
ANALYSIS_LOG_FILE = LOGS_DIR / "atlas_analysis.jsonl"
TRINITY_STATE_LOG_FILE_PATTERN = LOGS_DIR / "trinity_state_{date}.log"

# Log Formats
# Simplified format for general readability
LOG_FORMAT_SIMPLE = "%(asctime)s | %(levelname)-8s | %(message)s"
# Detailed format for debugging (includes file/line)
LOG_FORMAT_DETAILED = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# --- Formatters ---

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for AI analysis or machine ingestion."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }
        if hasattr(record, "tui_category"):
            log_obj["tui_category"] = getattr(record, "tui_category")
        if hasattr(record, "agent_type"):
            log_obj["agent_type"] = str(getattr(record, "agent_type"))
            
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj, ensure_ascii=False)


# --- Handlers ---

class SafeTuiHandler(logging.Handler):
    """
    Log directly to TUI state safely.
    Uses a deferred import or callback to avoid circular dependencies with `tui.state`.
    """
    def __init__(self, state_module_callback=None):
        super().__init__()
        self.state_callback = state_module_callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Skip if it is an agent message (handled separately usually)
            if record.name.endswith(".right") or record.name == "trinity.right":
                return

            if not self.state_callback:
                return

            # Execute callback to get state object (lazy load)
            state = self.state_callback()
            if not state:
                return

            msg = self.format(record)
            category = getattr(record, "tui_category", "info")
            
            # Map levels to TUI categories if not explicitly set
            if category == "info":
                if record.levelno >= logging.ERROR:
                    category = "error"
                elif record.levelno >= logging.WARNING:
                    category = "warning"
                elif record.levelno == logging.DEBUG:
                    category = "debug"
            
            # We assume state has the necessary attributes (logs, logs_lock)
            # This logic mimics the original TUI handler but is safer
            try:
                from tui.constants import LOG_STYLE_MAP
                style = LOG_STYLE_MAP.get(category, LOG_STYLE_MAP.get("info"))
            except ImportError:
                 style = "white"

            if hasattr(state, "logs_lock") and hasattr(state, "logs"):
                # Ensure we don't crash if logs_lock is not a Lock (though it should be)
                if state.logs_lock:
                    with state.logs_lock:
                        state.logs.append((style, f"{msg}\n"))
                        # Auto-trim
                        if len(state.logs) > 2500:
                             # Defer trim if agent is processing to avoid jumpiness
                             if not getattr(state, "agent_processing", False):
                                 del state.logs[:-2000]

        except Exception:
            self.handleError(record)


# --- Setup ---

_tui_handler = None

def setup_global_logging(
    verbose: bool = False, 
    tui_state_callback=None,
    root_dir: Optional[str] = None
) -> logging.Logger:
    """
    Initialize the global logging configuration.
    
    Args:
        verbose: If True, log INFO+ to stderr (useful for CLI without TUI).
        tui_state_callback: Function returning the `tui.state.state` object. 
                            Used to hook logs into the TUI.
        root_dir: Optional root directory to set up additional logs (e.g. left/right screen).
                  Used for backward compatibility with `setup_root_file_logging`.
    """
    global _tui_handler
    
    root_logger = logging.getLogger()
    # Ensure capture of DEBUG logs so we can route them
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    # 1. Main File Handler (Rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        CLI_LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB (reduced from 10MB)
        backupCount=3,  # Reduced from 5 to 3
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT_DETAILED, datefmt=DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # 2. Error File Handler
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=2 * 1024 * 1024,  # 2 MB (reduced from 5MB)
        backupCount=2,  # Reduced from 3 to 2
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT_DETAILED, datefmt=DATE_FORMAT))
    root_logger.addHandler(error_handler)
    
    # 3. Analysis/JSON Handler
    json_handler = logging.handlers.RotatingFileHandler(
        ANALYSIS_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB (reduced from 50MB)
        backupCount=3,  # Reduced from 5 to 3
        encoding="utf-8"
    )
    json_handler.setLevel(logging.DEBUG)
    json_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(json_handler)

    # 4. TUI Handler
    if tui_state_callback:
        _tui_handler = SafeTuiHandler(tui_state_callback)
        _tui_handler.setLevel(logging.INFO) # TUI usually shows INFO+
        _tui_handler.setFormatter(logging.Formatter(LOG_FORMAT_SIMPLE, datefmt=DATE_FORMAT))
        root_logger.addHandler(_tui_handler)

    # 5. Console (Verbose)
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT_SIMPLE, datefmt=DATE_FORMAT))
        root_logger.addHandler(console_handler)

    # Suppress noise
    _suppress_libs()
    
    if root_dir:
        _setup_legacy_root_logging(root_dir, root_logger)

    return root_logger


def _suppress_libs():
    """Silence noisy libraries."""
    for lib in ["urllib3", "chromadb", "backoff", "posthog", "watchdog"]:
        logging.getLogger(lib).setLevel(logging.WARNING)


def _setup_legacy_root_logging(root_dir: str, root_logger: logging.Logger):
    """Setup additional log handlers for legacy 'Left/Right' screen logging."""
    logs_dir = Path(root_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Simply attach a new handler to root if needed, or specific loggers.
    # Legacy code used 'trinity.left' and 'trinity.right'.
    # We can configure those loggers specifically.
    
    # Left Screen (Main) -> redirects to 'trinity.left'
    left_logger = logging.getLogger("trinity.left")
    left_logger.propagate = False # Isolated
    
    try:
        left_h = logging.handlers.RotatingFileHandler(
            logs_dir / "left_screen.log",
            maxBytes=5*1024*1024, backupCount=2, encoding="utf-8"  # Reduced from 10MB to 5MB, backupCount from 3 to 2
        )
        left_h.setFormatter(logging.Formatter(LOG_FORMAT_SIMPLE, datefmt=DATE_FORMAT))
        left_logger.addHandler(left_h)
        # Also log to TUI if available
        if _tui_handler:
            left_logger.addHandler(_tui_handler)
    except Exception:
        pass

    # Right Screen (Agents) -> 'trinity.right'
    right_logger = logging.getLogger("trinity.right")
    right_logger.propagate = False
    
    try:
        right_h = logging.handlers.RotatingFileHandler(
            logs_dir / "right_screen.log",
            maxBytes=5*1024*1024, backupCount=2, encoding="utf-8"  # Reduced from 10MB to 5MB, backupCount from 3 to 2
        )
        right_h.setFormatter(logging.Formatter("%(asctime)s | %(message)s", datefmt=DATE_FORMAT))
        right_logger.addHandler(right_h)
    except Exception:
        pass


def get_logger(name: str = "trinity") -> logging.Logger:
    """Convenience accessor."""
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> None:
    """Helper to log tracebacks."""
    if not logger:
        logger = get_logger()
    msg = f"Exception in {context}: {exc}" if context else f"Exception: {exc}"
    logger.exception(msg)


def log_command_execution(logger: logging.Logger, cmd: str, cwd: Optional[str] = None, 
                          returncode: Optional[int] = None, stdout: str = "", 
                          stderr: str = "") -> None:
    """Log command execution details."""
    if not logger:
        logger = get_logger()
    
    logger.debug(f"Command: {cmd}")
    if cwd:
        logger.debug(f"Working directory: {cwd}")
    if returncode is not None:
        logger.debug(f"Return code: {returncode}")
    if stdout:
        preview = stdout[:1000] + "..." if len(stdout) > 1000 else stdout
        logger.debug(f"STDOUT:\n{preview}")
    if stderr:
        preview = stderr[:1000] + "..." if len(stderr) > 1000 else stderr
        logger.warning(f"STDERR:\n{preview}")


def trace(logger: logging.Logger, event: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Log structured trace event for AI analysis."""
    if not logger:
        logger = get_logger()
    try:
        payload = {"event": event}
        if data:
            payload.update(data)
        serialized = json.dumps(payload, ensure_ascii=False)
        logger.info(f"[TRACE] {serialized}")
    except Exception:
        logger.debug(f"[TRACE] {event} (serialization failed)")


def get_log_files_info() -> Dict[str, Any]:
    """Get information about log files."""
    info = {
        "logs_dir": str(LOGS_DIR),
        "files": {}
    }
    for log_file in [CLI_LOG_FILE, ERROR_LOG_FILE, DEBUG_LOG_FILE]:
        if log_file.exists():
            size_mb = log_file.stat().st_size / (1024 * 1024)
            info["files"][log_file.name] = {
                "path": str(log_file),
                "size_mb": round(size_mb, 2),
                "exists": True
            }
        else:
            info["files"][log_file.name] = {
                "path": str(log_file),
                "exists": False
            }
    return info


# --- Legacy/Shim Functions ---

def setup_root_file_logging(root_dir: str) -> None:
    """Compatible shim that delegates to setup_global_logging."""
    setup_global_logging(root_dir=root_dir)


def setup_logging(verbose: bool = False, name: str = "trinity") -> logging.Logger:
    """Compatible shim that delegates to setup_global_logging."""
    return setup_global_logging(verbose=verbose)

