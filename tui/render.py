"""Rendering and log management for TUI.

Provides functions for:
- Log snapshot rendering with caching
- Agent messages snapshot rendering
- Log manipulation (reserve, replace, trim)
- Header, context, and status bar rendering
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from prompt_toolkit.data_structures import Point

from system_cli.state import state
from tui.messages import MessageBuffer, AgentType


# Locks and buffers
_logs_lock = threading.RLock()
_logs_need_trim: bool = False
_thread_log_override = threading.local()

_agent_messages_buffer = MessageBuffer(max_messages=200)
_agent_messages_lock = threading.RLock()

# Render caches
_render_log_cache: Dict[str, Any] = {"ts": 0.0, "logs": [], "cursor": Point(x=0, y=0)}
_render_log_cache_ttl_s: float = 0.2

_render_agents_cache: Dict[str, Any] = {"ts": 0.0, "messages": [], "cursor": Point(x=0, y=0)}
_render_agents_cache_ttl_s: float = 0.2

# Style mapping
STYLE_MAP = {
    "info": "class:log.info",
    "user": "class:log.user",
    "action": "class:log.action",
    "error": "class:log.error",
}


def get_render_log_snapshot() -> Tuple[List[Tuple[str, str]], Point]:
    """Get cached log snapshot with cursor position."""
    global _logs_need_trim
    
    with _logs_lock:
        now = time.monotonic()
        try:
            ts = float(_render_log_cache.get("ts", 0.0))
            if (now - ts) < _render_log_cache_ttl_s:
                cached = _render_log_cache.get("logs") or []
                cached_cursor = _render_log_cache.get("cursor") or Point(x=0, y=0)
                try:
                    combined = "".join(str(text or "") for _, text in cached)
                    if combined:
                        parts = combined.split("\n")
                        actual_line_count = max(1, len(parts))
                        if combined.endswith("\n"):
                            actual_line_count = max(1, actual_line_count - 1)
                        valid_cursor_y = max(0, min(cached_cursor.y, actual_line_count - 1))
                        return (
                            list(cached),
                            Point(x=0, y=valid_cursor_y),
                        )
                    else:
                        return (list(cached), Point(x=0, y=0))
                except Exception:
                    pass
        except Exception:
            pass

        try:
            logs_snapshot: List[Tuple[str, str]] = list(state.logs)
        except Exception:
            logs_snapshot = []

    try:
        combined = "".join(str(text or "") for _, text in logs_snapshot)
    except Exception:
        combined = ""

    if not combined:
        line_count = 1
        last_line_y = 0
    else:
        parts = combined.split("\n")
        line_count = max(1, len(parts))
        last_line_y = max(0, line_count - 1)
        if combined.endswith("\n"):
            last_line_y = max(0, last_line_y - 1)

    try:
        state.ui_log_line_count = int(line_count)
    except Exception:
        state.ui_log_line_count = 1

    try:
        if getattr(state, "ui_log_follow", True):
            state.ui_log_cursor_y = int(last_line_y)
        else:
            state.ui_log_cursor_y = max(
                0,
                min(
                    int(getattr(state, "ui_log_cursor_y", 0)),
                    max(0, int(getattr(state, "ui_log_line_count", 1)) - 1),
                ),
            )
            if state.ui_log_cursor_y >= max(0, int(getattr(state, "ui_log_line_count", 1)) - 1):
                state.ui_log_follow = True
    except Exception:
        state.ui_log_follow = True
        state.ui_log_cursor_y = int(last_line_y)

    cursor = Point(x=0, y=max(0, min(int(getattr(state, "ui_log_cursor_y", 0)), max(0, int(getattr(state, "ui_log_line_count", 1)) - 1))))

    with _logs_lock:
        _render_log_cache["ts"] = now
        _render_log_cache["logs"] = logs_snapshot
        _render_log_cache["cursor"] = cursor
        return logs_snapshot, cursor


def get_render_agents_snapshot() -> Tuple[List[Tuple[str, str]], Point]:
    """Get cached agent messages snapshot with cursor position."""
    with _agent_messages_lock:
        now = time.monotonic()
        try:
            ts = float(_render_agents_cache.get("ts", 0.0))
            if (now - ts) < _render_agents_cache_ttl_s:
                cached = _render_agents_cache.get("messages") or []
                cached_cursor = _render_agents_cache.get("cursor") or Point(x=0, y=0)
                try:
                    combined = "".join(str(text or "") for _, text in cached)
                    if combined:
                        parts = combined.split("\n")
                        actual_line_count = max(1, len(parts))
                        if combined.endswith("\n"):
                            actual_line_count = max(1, actual_line_count - 1)
                        valid_cursor_y = max(0, min(cached_cursor.y, actual_line_count - 1))
                        return (
                            list(cached),
                            Point(x=0, y=valid_cursor_y),
                        )
                    else:
                        return (list(cached), Point(x=0, y=0))
                except Exception:
                    pass
        except Exception:
            pass

        try:
            formatted: List[Tuple[str, str]] = list(_agent_messages_buffer.get_formatted() or [])
        except Exception:
            formatted = []

        try:
            combined = "".join(str(text or "") for _, text in formatted)
        except Exception:
            combined = ""

        if not combined:
            line_count = 1
            last_line_y = 0
        else:
            parts = combined.split("\n")
            line_count = max(1, len(parts))
            last_line_y = max(0, line_count - 1)
            if combined.endswith("\n"):
                last_line_y = max(0, last_line_y - 1)

        try:
            state.ui_agents_line_count = int(line_count)
        except Exception:
            state.ui_agents_line_count = 1

        try:
            if getattr(state, "ui_agents_follow", True):
                state.ui_agents_cursor_y = int(last_line_y)
            else:
                state.ui_agents_cursor_y = max(
                    0,
                    min(
                        int(getattr(state, "ui_agents_cursor_y", 0)),
                        max(0, int(getattr(state, "ui_agents_line_count", 1)) - 1),
                    ),
                )
                if state.ui_agents_cursor_y >= max(0, int(getattr(state, "ui_agents_line_count", 1)) - 1):
                    state.ui_agents_follow = True
        except Exception:
            state.ui_agents_follow = True
            state.ui_agents_cursor_y = int(last_line_y)

        cursor = Point(
            x=0,
            y=max(0, min(int(getattr(state, "ui_agents_cursor_y", 0)), max(0, int(getattr(state, "ui_agents_line_count", 1)) - 1))),
        )

        _render_agents_cache["ts"] = now
        _render_agents_cache["messages"] = formatted
        _render_agents_cache["cursor"] = cursor
        return formatted, cursor


def trim_logs_if_needed() -> None:
    """Trim logs if buffer exceeds limit and agent is not processing."""
    global _logs_need_trim
    with _logs_lock:
        if not _logs_need_trim:
            return
        if getattr(state, "agent_processing", False):
            return
        if len(state.logs) > 500:
            state.logs = state.logs[-400:]
        _logs_need_trim = False


def log_replace_last(text: str, category: str = "info") -> None:
    """Replace last log entry."""
    with _logs_lock:
        if not state.logs:
            state.logs.append((STYLE_MAP.get(category, "class:log.info"), f"{text}\n"))
            return
        state.logs[-1] = (STYLE_MAP.get(category, "class:log.info"), f"{text}\n")


def log_reserve_line(category: str = "info") -> int:
    """Reserve a new log line and return its index."""
    global _logs_need_trim
    with _logs_lock:
        state.logs.append((STYLE_MAP.get(category, "class:log.info"), "\n"))
        if len(state.logs) > 500:
            if getattr(state, "agent_processing", False):
                _logs_need_trim = True
            else:
                state.logs = state.logs[-400:]
        return max(0, len(state.logs) - 1)


def log_replace_at(index: int, text: str, category: str = "info") -> None:
    """Replace log entry at specific index."""
    with _logs_lock:
        if index < 0 or index >= len(state.logs):
            state.logs.append((STYLE_MAP.get(category, "class:log.info"), f"{text}\n"))
        else:
            state.logs[index] = (STYLE_MAP.get(category, "class:log.info"), f"{text}\n")


def log(text: str, category: str = "info") -> None:
    """Main log function - appends to log buffer."""
    global _logs_need_trim
    override = getattr(_thread_log_override, "handler", None)
    if callable(override):
        try:
            override(text, category)
        except Exception:
            pass
        return
    with _logs_lock:
        state.logs.append((STYLE_MAP.get(category, "class:log.info"), f"{text}\n"))
        if len(state.logs) > 500:
            if getattr(state, "agent_processing", False):
                _logs_need_trim = True
            else:
                state.logs = state.logs[-400:]


def log_agent_message(agent: AgentType, text: str) -> None:
    """Log agent message to clean display panel."""
    with _agent_messages_lock:
        try:
            _agent_messages_buffer.upsert_stream(agent, text, is_technical=False)
        except Exception:
            _agent_messages_buffer.add(agent, text, is_technical=False)
    
    # Update UI
    try:
        from tui.layout import force_ui_update
        force_ui_update()
    except Exception:
        pass


def get_logs() -> List[Tuple[str, str]]:
    """Get formatted logs for display."""
    try:
        logs_snapshot, _ = get_render_log_snapshot()
        return logs_snapshot if logs_snapshot else []
    except Exception:
        return []


def get_agent_messages() -> List[Tuple[str, str]]:
    """Get formatted agent messages for clean display panel."""
    try:
        formatted, _ = get_render_agents_snapshot()
        return formatted if formatted else []
    except Exception:
        return []


def get_agent_cursor_position() -> Point:
    """Get cursor position for agent messages panel."""
    try:
        _, cursor = get_render_agents_snapshot()
        return cursor
    except Exception:
        return Point(x=0, y=0)


def get_log_cursor_position() -> Point:
    """Get cursor position for log panel."""
    try:
        _, cursor = get_render_log_snapshot()
        return cursor
    except Exception:
        return Point(x=0, y=0)


def set_thread_log_override(handler: Optional[Callable[[str, str], None]]) -> None:
    """Set thread-local log override handler."""
    _thread_log_override.handler = handler


def clear_thread_log_override() -> None:
    """Clear thread-local log override handler."""
    _thread_log_override.handler = None


def get_agent_messages_buffer() -> MessageBuffer:
    """Get agent messages buffer (for external access)."""
    return _agent_messages_buffer


def get_agent_messages_lock() -> threading.RLock:
    """Get agent messages lock (for external access)."""
    return _agent_messages_lock


def get_logs_lock() -> threading.RLock:
    """Get logs lock (for external access)."""
    return _logs_lock


# Backward compatibility aliases
_get_render_log_snapshot = get_render_log_snapshot
_get_render_agents_snapshot = get_render_agents_snapshot
_trim_logs_if_needed = trim_logs_if_needed
_log_replace_last = log_replace_last
_log_reserve_line = log_reserve_line
_log_replace_at = log_replace_at
