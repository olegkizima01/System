"""Monitoring Services for System CLI.

Provides services for tracking file system events via fs_usage, opensnoop, etc.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from tui.cli_paths import MONITOR_EVENTS_DB_PATH
from tui.monitoring import monitor_db_insert


@dataclass
class DummyProcService:
    running: bool = False

    def start(self, *args: Any, **kwargs: Any) -> Tuple[bool, str]:
        self.running = True
        return True, "Monitoring started."

    def stop(self) -> Tuple[bool, str]:
        self.running = False
        return True, "Monitoring stopped."


class ProcTraceService:
    """Simple process-trace service wrapper around fs_usage/opensnoop.

    It spawns the tool, reads stdout lines and tries to parse pid/process/path
    and writes events into the monitor DB using `monitor_db_insert`.
    This is intentionally minimal and fails gracefully when tool is absent or
    blocked by SIP.
    """

    def __init__(self, cmd_name: str, cmd_base: list):
        self.cmd_name = str(cmd_name)
        self.cmd_base = list(cmd_base)
        self.proc = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.running = False

    def _parse_and_insert(self, line: str) -> None:
        try:
            # naive parsing: look for pid and path
            pid = 0
            process = ""
            path = ""
            # PID: first integer token after timestamp (fallback)
            m = re.search(r"\b(\d{2,7})\b", line)
            if m:
                try:
                    pid = int(m.group(1))
                except Exception:
                    pid = 0
            # path: first token starting with /
            m2 = re.search(r"(/[^\s]+)", line)
            if m2:
                path = m2.group(1)
            # process: try last token (often contains execname), prefer token with dot+digits
            m_proc = re.search(r"([A-Za-z0-9_\-\.]+(?:\.[0-9]+)?)\s*$", line)
            if m_proc:
                process = m_proc.group(1)

            # If pid wasn't found, try to resolve by process name using pgrep
            if not pid and process:
                try:
                    out = subprocess.check_output(["pgrep", "-f", process], text=True).strip().splitlines()
                    if out:
                        pid = int(out[0])
                except Exception:
                    pass

            # Insert into DB using existing utility
            try:
                monitor_db_insert(
                    MONITOR_EVENTS_DB_PATH,
                    source=self.cmd_name,
                    event_type="access",
                    src_path=path or "",
                    dest_path="",
                    is_directory=False,
                    target_key="",
                    pid=int(pid or 0),
                    process=str(process or ""),
                    raw_line=str(line or ""),
                )
            except Exception:
                return
        except Exception:
            return

    def _reader(self, stream: Any) -> None:
        try:
            for ln in iter(stream.readline, ""):
                if self.stop_event.is_set():
                    break
                if not ln:
                    continue
                line = str(ln or "").strip()
                if not line:
                    continue
                self._parse_and_insert(line)
        except Exception:
            return

    def start(self, pid: Optional[int] = None) -> Tuple[bool, str]:
        if self.running:
            return True, f"{self.cmd_name} already running"
        # check availability
        if shutil.which(self.cmd_base[0]) is None:
            return False, f"{self.cmd_base[0]} not found on PATH"

        cmd = list(self.cmd_base)
        if pid:
            # pass pid as positional argument for tools like fs_usage
            cmd += [str(int(pid))]

        # Optionally run under sudo if environment / state indicates it
        use_sudo = False
        try:
            from tui.state import state as _st
            use_sudo = bool(getattr(_st, "monitor_use_sudo", False))
        except Exception:
            use_sudo = False
        if not use_sudo:
            # also allow explicit env override
            use_sudo = bool(str(os.environ.get("FORCE_MONITOR_SUDO") or "").strip())

        if use_sudo:
            sudo_pwd = str(os.environ.get("SUDO_PASSWORD") or "").strip()
            cmd = ["sudo", "-S"] + cmd

        try:
            self.stop_event.clear()
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE if use_sudo and sudo_pwd else None, text=True)
            if use_sudo and sudo_pwd and self.proc.stdin:
                try:
                    # supply password
                    self.proc.stdin.write(sudo_pwd + "\n")
                    self.proc.stdin.flush()
                except Exception:
                    pass
            if self.proc.stdout:
                self.thread = threading.Thread(target=self._reader, args=(self.proc.stdout,), daemon=True)
                self.thread.start()
            self.running = True
            return True, f"{self.cmd_name} started"
        except Exception as e:
            return False, f"Failed to start {self.cmd_name}: {e}"

    def stop(self) -> Tuple[bool, str]:
        try:
            self.stop_event.set()
            if self.proc:
                try:
                    self.proc.terminate()
                except Exception:
                    pass
            if self.thread:
                try:
                    self.thread.join(timeout=2)
                except Exception:
                    pass
        finally:
            self.proc = None
            self.thread = None
            self.running = False
        return True, f"{self.cmd_name} stopped"
