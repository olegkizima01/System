#!/usr/bin/env python3
"""cli.py

Єдиний і основний інтерфейс керування системою.

Можливості:
- Управління очисткою по редакторах: Windsurf / VS Code / Antigravity / Cursor
- Керування модулями очистки (enable/disable)
- Режим "нова установка" (відкриття DMG/ZIP/URL)
- LLM-режим: smart-plan (побудова патернів/модулів) і /ask (одноразовий запит)
- Менеджер локалізацій (список/primary) – збереження в ~/.localization_cli.json

Запуск:
  python3 cli.py            # TUI
  python3 cli.py run --editor windsurf --dry-run

Примітка: скрипт навмисно не прив'язується до версій редакторів.
"""

import argparse
import atexit
from collections import Counter, defaultdict
import glob
import json
import os
import plistlib
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from i18n import TOP_LANGS, lang_name, normalize_lang, tr
from system_cli.state import AppState, MenuLevel, state

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.styles import DynamicStyle, Style

from tui.layout import build_app
from tui.menu import build_menu
from tui.keybindings import build_keybindings
from tui.app import TuiRuntime, run_tui as tui_run_tui
from tui.constants import MAIN_MENU_ITEMS
from tui.cli_defaults import DEFAULT_CLEANUP_CONFIG
from tui.cli_localization import AVAILABLE_LOCALES, LocalizationConfig
from tui.themes import THEME_NAMES, THEMES
from tui.cli_paths import (
    CLEANUP_CONFIG_PATH,
    LLM_SETTINGS_PATH,
    LOCALIZATION_CONFIG_PATH,
    MONITOR_EVENTS_DB_PATH,
    MONITOR_SETTINGS_PATH,
    MONITOR_TARGETS_PATH,
    SCRIPT_DIR,
    SYSTEM_CLI_DIR,
    UI_SETTINGS_PATH,
)

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except Exception:  # pragma: no cover
    FileSystemEventHandler = object  # type: ignore
    Observer = None  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

# LLM provider (optional)
try:
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

    from providers.copilot import CopilotLLM  # type: ignore
except Exception:
    CopilotLLM = None  # type: ignore
    HumanMessage = SystemMessage = None  # type: ignore


@dataclass
class AgentTool:
    name: str
    description: str
    handler: Any


@dataclass
class AgentSession:
    enabled: bool = True
    messages: List[Any] = field(default_factory=list)
    tools: List[AgentTool] = field(default_factory=list)
    llm: Any = None
    llm_signature: str = ""

    def reset(self) -> None:
        self.messages = []


agent_session = AgentSession()


agent_chat_mode: bool = True


def _env_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return None


@dataclass
class ModuleRef:
    editor: str
    module_id: str


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
    os.environ["SYSTEM_RAG_ENABLED"] = "1"


def _monitor_get_sudo_password() -> str:
    _load_env()
    return str(os.getenv("SUDO_PASSWORD") or "").strip()


def _load_monitor_settings() -> None:
    try:
        _load_env()
        if not os.path.exists(MONITOR_SETTINGS_PATH):
            if str(os.getenv("SUDO_PASSWORD") or "").strip():
                state.monitor_use_sudo = True
            return

        with open(MONITOR_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        src = str(data.get("source") or "").strip().lower()
        if src in {"watchdog", "fs_usage", "opensnoop"}:
            state.monitor_source = src
        use_sudo = data.get("use_sudo")
        if isinstance(use_sudo, bool):
            state.monitor_use_sudo = use_sudo
    except Exception:
        return


def _maybe_log_monitor_ingest(message: str) -> None:
    try:
        fn = globals().get("log")
        if callable(fn):
            fn(message, "info")
    except Exception:
        return


def _monitor_db_read_since_id(db_path: str, last_id: int, limit: int = 5000) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute(
                "SELECT id, ts, source, event_type, src_path, dest_path, is_directory, target_key, pid, process, raw_line "
                "FROM events WHERE id > ? ORDER BY id ASC LIMIT ?",
                (int(last_id or 0), int(limit)),
            )
            for r in cur.fetchall():
                rows.append(
                    {
                        "id": int(r[0] or 0),
                        "ts": int(r[1] or 0),
                        "source": str(r[2] or ""),
                        "event_type": str(r[3] or ""),
                        "src_path": str(r[4] or ""),
                        "dest_path": str(r[5] or ""),
                        "is_directory": bool(int(r[6] or 0)),
                        "target_key": str(r[7] or ""),
                        "pid": int(r[8] or 0),
                        "process": str(r[9] or ""),
                        "raw_line": str(r[10] or ""),
                    }
                )
        finally:
            conn.close()
    except Exception:
        return []
    return rows


def _monitor_db_get_max_id(db_path: str) -> int:
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute("SELECT MAX(id) FROM events")
            row = cur.fetchone()
            if not row:
                return 0
            return int(row[0] or 0)
        finally:
            conn.close()
    except Exception:
        return 0


def _format_monitor_summary(
    *,
    title: str,
    source: str,
    targets: List[str],
    ts_from: int,
    ts_to: int,
    total_events: int,
    by_target: Dict[str, int],
    by_type: Dict[str, int],
    top_paths: Dict[str, List[Tuple[str, int]]],
    include_processes: bool,
    top_processes: List[Tuple[str, int]],
) -> str:
    lines: List[str] = []
    lines.append(title)
    lines.append(f"source={source} targets={len(targets)} events={total_events}")
    lines.append(f"ts_range={ts_from}..{ts_to}")
    if targets:
        lines.append("targets: " + ", ".join(targets[:20]) + ("" if len(targets) <= 20 else " ..."))
    if by_target:
        top_t = sorted(by_target.items(), key=lambda x: x[1], reverse=True)[:10]
        lines.append("top_targets: " + ", ".join([f"{k}={v}" for k, v in top_t]))
    if by_type:
        top_e = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]
        lines.append("top_event_types: " + ", ".join([f"{k}={v}" for k, v in top_e]))
    if include_processes and top_processes:
        lines.append("top_processes: " + ", ".join([f"{k}={v}" for k, v in top_processes[:10]]))
    if top_paths:
        for tk, paths in list(top_paths.items())[:10]:
            if not paths:
                continue
            p = ", ".join([f"{path}({cnt})" for path, cnt in paths[:5]])
            lines.append(f"paths[{tk}]: {p}")
    return "\n".join(lines)


@dataclass
class _MonitorSummaryService:
    db_path: str
    interval_sec: int = 30
    flush_threshold: int = 250
    thread: Optional[threading.Thread] = None
    running: bool = False
    stop_event: threading.Event = field(default_factory=threading.Event)
    last_id: int = 0
    session_start_ts: int = 0
    session_end_ts: int = 0
    total_events: int = 0
    totals_by_target: Counter = field(default_factory=Counter)
    totals_by_type: Counter = field(default_factory=Counter)
    totals_by_process: Counter = field(default_factory=Counter)
    totals_paths_by_target: Dict[str, Counter] = field(default_factory=lambda: defaultdict(Counter))
    last_flush_ts: int = 0

    def _ingest(self, text: str, metadata: Dict[str, Any]) -> bool:
        try:
            _load_env()
            from system_ai.rag.rag_pipeline import RagPipeline

            rp = RagPipeline(persist_dir="~/.system_cli/chroma")
            return bool(rp.ingest_text(text, metadata=metadata))
        except Exception:
            return False

    def _flush(self, *, kind: str, targets: List[str], source: str) -> None:
        batch = _monitor_db_read_since_id(self.db_path, self.last_id, limit=5000)
        if not batch:
            return

        self.last_id = max(self.last_id, max(int(x.get("id") or 0) for x in batch))
        ts_values = [int(x.get("ts") or 0) for x in batch if int(x.get("ts") or 0) > 0]
        ts_from = min(ts_values) if ts_values else int(time.time())
        ts_to = max(ts_values) if ts_values else int(time.time())

        by_target = Counter()
        by_type = Counter()
        by_process = Counter()
        paths_by_target: Dict[str, Counter] = defaultdict(Counter)

        for e in batch:
            tk = str(e.get("target_key") or "")
            et = str(e.get("event_type") or "")
            by_target[tk] += 1
            by_type[et] += 1
            src = str(e.get("src_path") or "")
            if src:
                paths_by_target[tk][src] += 1
            proc = str(e.get("process") or "").strip()
            if proc:
                by_process[proc] += 1

        self.total_events += len(batch)
        self.totals_by_target.update(by_target)
        self.totals_by_type.update(by_type)
        self.totals_by_process.update(by_process)
        for tk, c in paths_by_target.items():
            self.totals_paths_by_target[tk].update(c)
        self.session_end_ts = max(self.session_end_ts, ts_to)

        top_paths: Dict[str, List[Tuple[str, int]]] = {}
        for tk, c in paths_by_target.items():
            top_paths[tk] = c.most_common(10)

        include_processes = bool(by_process)
        summary_text = _format_monitor_summary(
            title=f"MONITOR SUMMARY ({kind})",
            source=str(source or ""),
            targets=targets,
            ts_from=ts_from,
            ts_to=ts_to,
            total_events=len(batch),
            by_target=dict(by_target),
            by_type=dict(by_type),
            top_paths=top_paths,
            include_processes=include_processes,
            top_processes=by_process.most_common(10),
        )

        meta = {
            "type": "monitor_summary",
            "kind": kind,
            "source": str(source or ""),
            "targets": targets,
            "events": int(len(batch)),
            "ts_from": int(ts_from),
            "ts_to": int(ts_to),
        }
        ok = self._ingest(summary_text, meta)
        if ok:
            self.last_flush_ts = int(time.time())
            _maybe_log_monitor_ingest(
                f"Monitor summary ingested: kind={kind} source={source} events={len(batch)} targets={len(targets)}"
            )

    def _run(self) -> None:
        while not self.stop_event.wait(timeout=max(5, int(self.interval_sec))):
            if not self.running:
                break
            try:
                targets = sorted(getattr(state, "monitor_targets", set()) or set())
                source = str(getattr(state, "monitor_source", "") or "")
                self._flush(kind="periodic", targets=targets, source=source)
            except Exception:
                continue

        try:
            targets = sorted(getattr(state, "monitor_targets", set()) or set())
            source = str(getattr(state, "monitor_source", "") or "")
            self._flush(kind="final", targets=targets, source=source)
        except Exception:
            pass

        if self.total_events > 0:
            try:
                targets = sorted(getattr(state, "monitor_targets", set()) or set())
                source = str(getattr(state, "monitor_source", "") or "")

                top_paths_total: Dict[str, List[Tuple[str, int]]] = {}
                for tk, c in self.totals_paths_by_target.items():
                    top_paths_total[tk] = c.most_common(10)

                session_text = _format_monitor_summary(
                    title="MONITOR SESSION SUMMARY",
                    source=str(source or ""),
                    targets=targets,
                    ts_from=int(self.session_start_ts or 0),
                    ts_to=int(self.session_end_ts or 0),
                    total_events=int(self.total_events),
                    by_target=dict(self.totals_by_target),
                    by_type=dict(self.totals_by_type),
                    top_paths=top_paths_total,
                    include_processes=bool(self.totals_by_process),
                    top_processes=self.totals_by_process.most_common(10),
                )

                meta = {
                    "type": "monitor_summary",
                    "kind": "session",
                    "source": str(source or ""),
                    "targets": targets,
                    "events": int(self.total_events),
                    "ts_from": int(self.session_start_ts or 0),
                    "ts_to": int(self.session_end_ts or 0),
                }
                if self._ingest(session_text, meta):
                    _maybe_log_monitor_ingest(
                        f"Monitor summary ingested: kind=session source={source} events={int(self.total_events)} targets={len(targets)}"
                    )
            except Exception:
                pass

        self.running = False

    def start(self) -> None:
        if self.running:
            return
        self.stop_event.clear()
        self.running = True
        self.session_start_ts = int(time.time())
        self.session_end_ts = int(self.session_start_ts)
        self.last_flush_ts = 0
        self.total_events = 0
        self.totals_by_target = Counter()
        self.totals_by_type = Counter()
        self.totals_by_process = Counter()
        self.totals_paths_by_target = defaultdict(Counter)
        self.last_id = _monitor_db_get_max_id(self.db_path)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if not self.running:
            return
        self.stop_event.set()
        try:
            if self.thread:
                self.thread.join(timeout=8)
        except Exception:
            pass
        self.thread = None
        self.running = False


monitor_summary_service = _MonitorSummaryService(db_path=MONITOR_EVENTS_DB_PATH)


def _save_monitor_settings() -> bool:
    try:
        os.makedirs(SYSTEM_CLI_DIR, exist_ok=True)
        payload = {
            "source": state.monitor_source,
            "use_sudo": bool(state.monitor_use_sudo),
        }
        with open(MONITOR_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _load_ui_settings() -> None:
    try:
        _load_env()
        if not os.path.exists(UI_SETTINGS_PATH):
            env_unsafe = _env_bool(os.getenv("SYSTEM_CLI_UNSAFE_MODE"))
            if env_unsafe is None:
                env_unsafe = _env_bool(os.getenv("SYSTEM_CLI_AUTO_CONFIRM"))
            if env_unsafe is not None:
                state.ui_unsafe_mode = bool(env_unsafe)
            return
        with open(UI_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        theme = str(data.get("theme") or "").strip().lower()
        if theme:
            state.ui_theme = theme
        ui_lang = str(data.get("ui_lang") or "").strip().lower()
        if ui_lang:
            state.ui_lang = normalize_lang(ui_lang)
        chat_lang = str(data.get("chat_lang") or "").strip().lower()
        if chat_lang:
            state.chat_lang = normalize_lang(chat_lang)
        unsafe_mode = data.get("unsafe_mode")
        if isinstance(unsafe_mode, bool):
            state.ui_unsafe_mode = unsafe_mode

        env_unsafe = _env_bool(os.getenv("SYSTEM_CLI_UNSAFE_MODE"))
        if env_unsafe is None:
            env_unsafe = _env_bool(os.getenv("SYSTEM_CLI_AUTO_CONFIRM"))
        if env_unsafe is not None:
            state.ui_unsafe_mode = bool(env_unsafe)
    except Exception:
        return


def _save_ui_settings() -> bool:
    try:
        os.makedirs(SYSTEM_CLI_DIR, exist_ok=True)
        payload = {
            "theme": str(state.ui_theme or "monaco").strip().lower() or "monaco",
            "ui_lang": normalize_lang(state.ui_lang),
            "chat_lang": normalize_lang(state.chat_lang),
            "unsafe_mode": bool(state.ui_unsafe_mode),
        }
        with open(UI_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _get_reply_language_label() -> str:
    # Keep internal prompts English; this only sets desired assistant output language.
    return lang_name(state.chat_lang)


def _load_llm_settings() -> None:
    try:
        provider = str(os.getenv("LLM_PROVIDER") or "copilot").strip().lower() or "copilot"
        main_model = str(os.getenv("COPILOT_MODEL") or "gpt-4o").strip() or "gpt-4o"
        vision_model = str(os.getenv("COPILOT_VISION_MODEL") or "").strip()
        if not vision_model:
            vision_model = "gpt-4.1"
        if vision_model == "gpt-4o":
            vision_model = "gpt-4.1"

        if os.path.exists(LLM_SETTINGS_PATH):
            with open(LLM_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            p = str(data.get("provider") or "").strip().lower()
            if p:
                provider = p
            mm = str(data.get("main_model") or "").strip()
            if mm:
                main_model = mm
            vm = str(data.get("vision_model") or "").strip()
            if vm:
                vision_model = "gpt-4.1" if vm == "gpt-4o" else vm

        os.environ["LLM_PROVIDER"] = provider
        os.environ["COPILOT_MODEL"] = main_model
        os.environ["COPILOT_VISION_MODEL"] = vision_model
    except Exception:
        return


def _save_llm_settings(provider: str, main_model: str, vision_model: str) -> bool:
    try:
        os.makedirs(SYSTEM_CLI_DIR, exist_ok=True)
        payload = {
            "provider": str(provider or "copilot").strip().lower() or "copilot",
            "main_model": str(main_model or "").strip() or "gpt-4o",
            "vision_model": "gpt-4.1" if str(vision_model or "").strip() == "gpt-4o" else str(vision_model or "").strip() or "gpt-4.1",
        }
        with open(LLM_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.environ["LLM_PROVIDER"] = payload["provider"]
        os.environ["COPILOT_MODEL"] = payload["main_model"]
        os.environ["COPILOT_VISION_MODEL"] = payload["vision_model"]
        return True
    except Exception:
        return False


def _get_llm_signature() -> str:
    return "|".join(
        [
            str(os.getenv("LLM_PROVIDER") or ""),
            str(os.getenv("COPILOT_MODEL") or ""),
            str(os.getenv("COPILOT_VISION_MODEL") or ""),
        ]
    )


def _reset_agent_llm() -> None:
    agent_session.llm = None
    agent_session.llm_signature = ""
    agent_session.reset()


def _monitor_db_insert(
    db_path: str,
    *,
    source: str,
    event_type: str,
    src_path: str,
    dest_path: str,
    is_directory: bool,
    target_key: str,
    pid: int = 0,
    process: str = "",
    raw_line: str = "",
) -> None:
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO events(ts, source, event_type, src_path, dest_path, is_directory, target_key, pid, process, raw_line) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    int(time.time()),
                    str(source),
                    str(event_type),
                    str(src_path),
                    str(dest_path),
                    1 if is_directory else 0,
                    str(target_key),
                    int(pid or 0),
                    str(process or ""),
                    str(raw_line or ""),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        return


def _ensure_agent_ready() -> Tuple[bool, str]:
    if CopilotLLM is None or SystemMessage is None or HumanMessage is None:
        return False, "LLM недоступний (нема langchain_core або providers/copilot.py)"

    _load_env()
    _load_llm_settings()
    sig = _get_llm_signature()

    provider = str(os.getenv("LLM_PROVIDER") or "copilot").strip().lower() or "copilot"
    if provider != "copilot":
        return False, f"Unsupported LLM provider: {provider}"

    if agent_session.llm is None or agent_session.llm_signature != sig:
        agent_session.llm = CopilotLLM(model_name=os.getenv("COPILOT_MODEL"), vision_model_name=os.getenv("COPILOT_VISION_MODEL"))
        agent_session.llm_signature = sig
    return True, "OK"


def _is_confirmed_run(text: str) -> bool:
    return "confirm_run" in text.lower()


def _is_confirmed_autopilot(text: str) -> bool:
    return "confirm_autopilot" in text.lower()


def _is_confirmed_shell(text: str) -> bool:
    return "confirm_shell" in text.lower()


def _is_confirmed_applescript(text: str) -> bool:
    return "confirm_applescript" in text.lower()


@dataclass
class CommandPermissions:
    allow_run: bool = False
    allow_autopilot: bool = False
    allow_shell: bool = False
    allow_applescript: bool = False


def _permissions_from_text(text: str) -> CommandPermissions:
    return CommandPermissions(
        allow_run=_is_confirmed_run(text),
        allow_autopilot=_is_confirmed_autopilot(text),
        allow_shell=_is_confirmed_shell(text),
        allow_applescript=_is_confirmed_applescript(text),
    )


_agent_last_permissions = CommandPermissions()


def _safe_abspath(path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        return expanded
    if expanded.startswith("./"):
        expanded = expanded[2:]
    return os.path.abspath(os.path.join(SCRIPT_DIR, expanded))


def _resolve_script_path(script: str) -> str:
    expanded = os.path.expanduser(str(script or "").strip())
    if not expanded:
        return ""
    if os.path.isabs(expanded):
        return expanded

    raw = expanded
    if raw.startswith("./"):
        raw = raw[2:]

    cleanup_dir = os.path.join(SCRIPT_DIR, "cleanup_scripts")
    base = os.path.basename(raw)

    candidates = [
        os.path.abspath(os.path.join(SCRIPT_DIR, raw)),
        os.path.abspath(os.path.join(cleanup_dir, raw)),
        os.path.abspath(os.path.join(cleanup_dir, base)),
        os.path.abspath(os.path.join(SCRIPT_DIR, base)),
    ]

    for p in candidates:
        if os.path.exists(p):
            return p

    return candidates[0]


def _scan_traces(editor: str) -> Dict[str, Any]:
    editor_key = editor.strip().lower()

    patterns_map: Dict[str, List[str]] = {
        "windsurf": ["*Windsurf*", "*windsurf*"],
        "vscode": ["*Code*", "*VSCodium*", "*vscode*", "*VSCode*"],
        "antigravity": ["*Antigravity*", "*antigravity*", "*Google/Antigravity*"],
        "cursor": ["*Cursor*", "*cursor*"],
    }

    base_dirs = [
        "~/Library/Application Support",
        "~/Library/Caches",
        "~/Library/Preferences",
        "~/Library/Logs",
        "~/Library/Saved Application State",
    ]

    patterns = patterns_map.get(editor_key) or [f"*{editor_key}*"]
    found: List[Dict[str, Any]] = []

    for b in base_dirs:
        base = os.path.expanduser(b)
        for pat in patterns:
            for p in sorted(glob.glob(os.path.join(base, pat))):
                entry: Dict[str, Any] = {"path": p, "type": "file" if os.path.isfile(p) else "dir"}
                if os.path.isdir(p):
                    try:
                        items = os.listdir(p)
                        entry["items"] = len(items)
                        entry["sample"] = items[:20]
                    except Exception as e:
                        entry["error"] = str(e)
                found.append(entry)

    # Applications bundles
    for pat in patterns:
        for p in sorted(glob.glob(os.path.join("/Applications", pat))):
            found.append({"path": p, "type": "app" if p.endswith(".app") else "file"})

    # Dot-directories
    dot_candidates = [
        os.path.expanduser("~/.vscode"),
        os.path.expanduser("~/.vscode-oss"),
        os.path.expanduser("~/.cursor"),
        os.path.expanduser("~/.windsurf"),
    ]
    for p in dot_candidates:
        if os.path.exists(p) and editor_key in os.path.basename(p).lower():
            found.append({"path": p, "type": "dir" if os.path.isdir(p) else "file"})

    return {
        "editor": editor_key,
        "count": len(found),
        "found": found[:120],
        "note": "Це швидкий скан типових директорій. Якщо потрібно глибше — скажи, які саме шляхи/патерни шукати.",
    }


def _tool_list_dir(args: Dict[str, Any]) -> Dict[str, Any]:
    path = _safe_abspath(str(args.get("path", "")))
    if not path or not os.path.exists(path):
        return {"ok": False, "error": f"Path not found: {path}"}
    if not os.path.isdir(path):
        return {"ok": False, "error": f"Not a directory: {path}"}
    try:
        items = sorted(os.listdir(path))
        return {"ok": True, "path": path, "count": len(items), "items": items[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_open_app(args: Dict[str, Any]) -> Dict[str, Any]:
    name = str(args.get("name", "")).strip()
    if not name:
        return {"ok": False, "error": "Missing name"}
    try:
        from system_ai.tools.executor import open_app

        out = open_app(name)
        ok = out.get("status") == "success"
        return {"ok": ok, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_take_screenshot(args: Dict[str, Any]) -> Dict[str, Any]:
    app_name = args.get("app_name")
    app_str = str(app_name).strip() if app_name is not None else ""
    try:
        from system_ai.tools.screenshot import take_screenshot

        out = take_screenshot(app_str if app_str else None)
        ok = out.get("status") == "success"
        return {"ok": ok, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_run_shell(args: Dict[str, Any], allow_shell: bool) -> Dict[str, Any]:
    command = str(args.get("command", "")).strip()
    if not command:
        return {"ok": False, "error": "Missing command"}
    try:
        from system_ai.tools.executor import run_shell

        out = run_shell(command, allow=allow_shell, cwd=SCRIPT_DIR)
        ok = out.get("status") == "success"
        return {"ok": ok, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_run_applescript(args: Dict[str, Any], allow_applescript: bool) -> Dict[str, Any]:
    script = str(args.get("script", "")).strip()
    if not script:
        return {"ok": False, "error": "Missing script"}
    try:
        from system_ai.tools.executor import run_applescript

        out = run_applescript(script, allow=allow_applescript)
        ok = out.get("status") == "success"
        return {"ok": ok, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    path = _safe_abspath(str(args.get("path", "")))
    limit = int(args.get("limit", 200))
    if not path or not os.path.exists(path):
        return {"ok": False, "error": f"File not found: {path}"}
    if os.path.isdir(path):
        return {"ok": False, "error": f"Is a directory: {path}"}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return {"ok": True, "path": path, "lines": lines[:limit], "total_lines": len(lines)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _tool_grep(args: Dict[str, Any]) -> Dict[str, Any]:
    root = _safe_abspath(str(args.get("root", SCRIPT_DIR)))
    query = str(args.get("query", ""))
    if not query:
        return {"ok": False, "error": "Missing query"}
    try:
        rx = re.compile(query, re.IGNORECASE)
    except Exception as e:
        return {"ok": False, "error": f"Bad regex: {e}"}

    max_files = int(args.get("max_files", 600))
    max_hits = int(args.get("max_hits", 200))
    hits: List[Dict[str, Any]] = []
    scanned = 0

    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if scanned >= max_files or len(hits) >= max_hits:
                break
            p = os.path.join(dirpath, fn)
            scanned += 1
            try:
                if os.path.getsize(p) > 2_000_000:
                    continue
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, start=1):
                        if rx.search(line):
                            hits.append({"path": p, "line": i, "text": line.strip()[:300]})
                            if len(hits) >= max_hits:
                                break
            except Exception:
                continue
        if scanned >= max_files or len(hits) >= max_hits:
            break

    return {"ok": True, "root": root, "query": query, "scanned_files": scanned, "hits": hits}


def _tool_scan_traces(args: Dict[str, Any]) -> Dict[str, Any]:
    editor = str(args.get("editor", "")).strip()
    if not editor:
        return {"ok": False, "error": "Missing editor"}
    return {"ok": True, "result": _scan_traces(editor)}


def _tool_create_module(args: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _load_cleanup_config()

    editor = str(args.get("editor", "")).strip().lower()
    module_id = str(args.get("id", "")).strip()
    name = str(args.get("name", "")).strip() or module_id
    description = str(args.get("description", "")).strip()
    enabled = bool(args.get("enabled", True))
    script = str(args.get("script", "")).strip() or f"./cleanup_scripts/{module_id}.sh"
    content = str(args.get("script_content", "")).strip()
    overwrite = bool(args.get("overwrite", False))

    if editor not in cfg.get("editors", {}):
        return {"ok": False, "error": f"Unknown editor: {editor}"}
    if not module_id:
        return {"ok": False, "error": "Missing module id"}

    if not script.endswith(".sh"):
        script = script + ".sh"
    if not script.startswith("./") and not os.path.isabs(script):
        script = "./" + script

    script_path = _safe_abspath(script)
    if os.path.exists(script_path) and not overwrite:
        return {"ok": False, "error": f"Script already exists: {script_path} (set overwrite=true to replace)"}

    if not content:
        content = "#!/bin/zsh\n\nset -e\n\necho \"TODO: implement cleanup\"\n"
    if not content.startswith("#!"):
        content = "#!/bin/zsh\n" + content

    try:
        parent = os.path.dirname(script_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["chmod", "+x", script_path], check=False)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    existing_ids = {m.get("id") for m in cfg["editors"][editor].get("modules", [])}
    if module_id not in existing_ids:
        cfg["editors"][editor].setdefault("modules", []).append(
            {
                "id": module_id,
                "name": name,
                "script": script,
                "enabled": enabled,
                "description": description,
            }
        )

    _save_cleanup_config(cfg)

    return {
        "ok": True,
        "editor": editor,
        "id": module_id,
        "script": script,
        "script_path": script_path,
        "note": "Модуль створено і додано в cleanup_modules.json",
    }


def _tool_run_module(args: Dict[str, Any], allow_run: bool) -> Dict[str, Any]:
    if not allow_run:
        return {"ok": False, "error": "Confirmation required. Add CONFIRM_RUN in your message to allow running scripts."}

    cfg = _load_cleanup_config()
    editor = str(args.get("editor", "")).strip().lower()
    module_id = str(args.get("id", "")).strip()
    if editor not in cfg.get("editors", {}):
        return {"ok": False, "error": f"Unknown editor: {editor}"}
    if not module_id:
        return {"ok": False, "error": "Missing module id"}

    module = next((m for m in cfg["editors"][editor].get("modules", []) if m.get("id") == module_id), None)
    if not module:
        return {"ok": False, "error": f"Module not found: {editor}/{module_id}"}

    script = str(module.get("script") or "")
    if not script:
        return {"ok": False, "error": "Module has no script"}

    script_path = _resolve_script_path(script)
    if not os.path.exists(script_path):
        return {"ok": False, "error": f"Script not found: {script_path}"}

    try:
        subprocess.run(["chmod", "+x", script_path], check=False)
        proc = subprocess.run([script_path], cwd=SCRIPT_DIR, capture_output=True, text=True, env=_script_env())
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _init_agent_tools() -> None:
    if agent_session.tools:
        return
    agent_session.tools = [
        AgentTool(name="scan_traces", description="Scan typical macOS paths for traces of an editor. args: {editor}", handler=_tool_scan_traces),
        AgentTool(name="list_dir", description="List directory entries. args: {path}", handler=_tool_list_dir),
        AgentTool(name="read_file", description="Read file lines. args: {path, limit?}", handler=_tool_read_file),
        AgentTool(name="grep", description="Grep by regex under root. args: {root, query, max_files?, max_hits?}", handler=_tool_grep),
        AgentTool(name="open_app", description="Open a macOS app by name. args: {name}", handler=_tool_open_app),
        AgentTool(name="take_screenshot", description="Take screenshot of focused window or target app. args: {app_name?}", handler=_tool_take_screenshot),
        AgentTool(name="run_shell", description="Run a shell command (requires CONFIRM_SHELL). args: {command}", handler=None),
        AgentTool(name="run_applescript", description="Run AppleScript (requires CONFIRM_APPLESCRIPT). args: {script}", handler=None),
        AgentTool(
            name="create_module",
            description="Create cleanup module (.sh file + add to cleanup_modules.json). args: {editor,id,name,description?,enabled?,script?,script_content?,overwrite?}",
            handler=_tool_create_module,
        ),
        AgentTool(
            name="run_module",
            description="Run module script (requires explicit user confirmation). args: {editor,id}",
            handler=None,
        ),
        AgentTool(
            name="monitor_status",
            description="Get monitoring status. args: {}",
            handler=lambda _args: _tool_monitor_status(),
        ),
        AgentTool(
            name="monitor_set_source",
            description="Set monitoring source. args: {source: watchdog|fs_usage|opensnoop}",
            handler=lambda a: _tool_monitor_set_source(a),
        ),
        AgentTool(
            name="monitor_set_use_sudo",
            description="Toggle sudo usage for monitoring source fs_usage. args: {use_sudo: true|false}",
            handler=lambda a: _tool_monitor_set_use_sudo(a),
        ),
        AgentTool(
            name="monitor_start",
            description="Start monitoring using current settings & targets. args: {}",
            handler=lambda _args: _tool_monitor_start(),
        ),
        AgentTool(
            name="monitor_stop",
            description="Stop monitoring. args: {}",
            handler=lambda _args: _tool_monitor_stop(),
        ),
        AgentTool(
            name="app_command",
            description="Execute any CLI command (same as typing in TUI). args: {command: '/...'}",
            handler=lambda a: _tool_app_command(a),
        ),
        AgentTool(
            name="monitor_targets",
            description="Manage monitor targets. args: {action: list|add|remove|clear|save, key?}",
            handler=lambda a: _tool_monitor_targets(a),
        ),
        AgentTool(
            name="llm_status",
            description="Get LLM provider/models settings. args: {}",
            handler=lambda _a: _tool_llm_status(),
        ),
        AgentTool(
            name="llm_set",
            description="Set LLM provider/models. args: {provider?, main_model?, vision_model?}",
            handler=lambda a: _tool_llm_set(a),
        ),
        AgentTool(
            name="ui_theme_status",
            description="Get current UI theme. args: {}",
            handler=lambda _a: _tool_ui_theme_status(),
        ),
        AgentTool(
            name="ui_theme_set",
            description="Set UI theme. args: {theme: monaco|dracula|nord|gruvbox}",
            handler=lambda a: _tool_ui_theme_set(a),
        ),
    ]


def _agent_send(user_text: str) -> Tuple[bool, str]:
    ok, msg = _ensure_agent_ready()
    if not ok:
        return False, msg

    _init_agent_tools()

    _load_ui_settings()
    unsafe_mode = bool(getattr(state, "ui_unsafe_mode", False))

    allow_run = unsafe_mode or _is_confirmed_run(user_text)
    allow_autopilot = unsafe_mode or _is_confirmed_autopilot(user_text)
    allow_shell = unsafe_mode or _is_confirmed_shell(user_text)
    allow_applescript = unsafe_mode or _is_confirmed_applescript(user_text)
    global _agent_last_permissions
    _agent_last_permissions = CommandPermissions(
        allow_run=allow_run,
        allow_autopilot=allow_autopilot,
        allow_shell=allow_shell,
        allow_applescript=allow_applescript,
    )

    system_prompt = (
        "You are an interactive assistant for a macOS cleanup/monitoring CLI.\n"
        "You can use tools to inspect files, create cleanup modules, control monitoring, and change settings.\n\n"
        "You may execute any in-app command via app_command (equivalent to typing /... in the TUI).\n"
        "You may also control UI theme via ui_theme_status/ui_theme_set (or /theme).\n\n"
        "Safety rules:\n"
        "- If Unsafe mode is OFF: require CONFIRM_RUN / CONFIRM_SHELL / CONFIRM_APPLESCRIPT for execution.\n"
        "- If Unsafe mode is ON: confirmations are bypassed (dangerous). Do not ask the user to confirm; proceed.\n\n"
        f"Reply in {lang_name(state.chat_lang)}. Be concise and practical.\n"
    )

    if not agent_session.messages:
        agent_session.messages = [SystemMessage(content=system_prompt)]

    # Refresh config snapshot for context
    cfg_snapshot = _load_cleanup_config()
    agent_session.messages.append(
        HumanMessage(
            content=json.dumps(
                {
                    "user": user_text,
                    "cleanup_config": cfg_snapshot,
                    "hint": "Якщо потрібно виконати пошук/аналіз — викликай tools.",
                },
                ensure_ascii=False,
            )
        )
    )

    # Bind tools to CopilotLLM (JSON tool_calls protocol)
    llm = agent_session.llm.bind_tools(agent_session.tools)

    last_answer = ""
    for _ in range(5):
        resp = llm.invoke(agent_session.messages)
        content = str(getattr(resp, "content", "") or "")
        last_answer = content
        agent_session.messages.append(resp)

        tool_calls = getattr(resp, "tool_calls", None)
        if not tool_calls:
            break

        results: List[Dict[str, Any]] = []
        for call in tool_calls:
            name = call.get("name")
            args = call.get("args") or {}

            if name == "run_module":
                out = _tool_run_module(args, allow_run=allow_run)
                results.append({"name": name, "args": args, "result": out})
                continue

            if name == "run_shell":
                out = _tool_run_shell(args, allow_shell=allow_shell)
                results.append({"name": name, "args": args, "result": out})
                continue

            if name == "run_applescript":
                out = _tool_run_applescript(args, allow_applescript=allow_applescript)
                results.append({"name": name, "args": args, "result": out})
                continue

            tool = next((t for t in agent_session.tools if t.name == name), None)
            if not tool or not tool.handler:
                results.append({"name": name, "args": args, "result": {"ok": False, "error": "Unknown tool"}})
                continue

            try:
                out = tool.handler(args)
            except Exception as e:
                out = {"ok": False, "error": str(e)}
            results.append({"name": name, "args": args, "result": out})

        agent_session.messages.append(
            HumanMessage(content=json.dumps({"tool_results": results}, ensure_ascii=False, indent=2))
        )

    if not last_answer:
        last_answer = "(без текстової відповіді)"
    return True, last_answer


def _load_cleanup_config() -> Dict[str, Any]:
    if not os.path.exists(CLEANUP_CONFIG_PATH):
        return json.loads(json.dumps(DEFAULT_CLEANUP_CONFIG))

    try:
        with open(CLEANUP_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data.setdefault("editors", {})

    for key, val in DEFAULT_CLEANUP_CONFIG["editors"].items():
        if key not in data["editors"]:
            data["editors"][key] = val
            continue
        # ensure shape
        for field_name in ["label", "install", "modules"]:
            if field_name not in data["editors"][key]:
                data["editors"][key][field_name] = val[field_name]

        # If modules list empty in config file but default has modules, use defaults
        if not data["editors"][key].get("modules") and val.get("modules"):
            data["editors"][key]["modules"] = val["modules"]

    return data


def _save_cleanup_config(cfg: Dict[str, Any]) -> None:
    with open(CLEANUP_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _list_editors(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    result: List[Tuple[str, str]] = []
    for key, meta in cfg.get("editors", {}).items():
        result.append((key, str(meta.get("label", key))))
    return result


def _find_module(cfg: Dict[str, Any], editor: str, module_id: str) -> Optional[ModuleRef]:
    editors = cfg.get("editors", {})
    if editor not in editors:
        return None
    for m in editors[editor].get("modules", []):
        if m.get("id") == module_id:
            return ModuleRef(editor=editor, module_id=module_id)
    return None


def _set_module_enabled(cfg: Dict[str, Any], ref: ModuleRef, enabled: bool) -> bool:
    editor_cfg = cfg.get("editors", {}).get(ref.editor)
    if not editor_cfg:
        return False

    for m in editor_cfg.get("modules", []):
        if m.get("id") == ref.module_id:
            m["enabled"] = enabled
            _save_cleanup_config(cfg)
            return True

    return False


def _run_script(script_path: str) -> int:
    full = _resolve_script_path(script_path)

    if not os.path.exists(full):
        return 1

    try:
        subprocess.run(["chmod", "+x", full], check=False)
        proc = subprocess.run([full], cwd=SCRIPT_DIR, env=_script_env())
        return proc.returncode
    except Exception:
        return 1


def _run_cleanup(cfg: Dict[str, Any], editor: str, dry_run: bool = False) -> Tuple[bool, str]:
    _load_env()
    _load_ui_settings()
    editors = cfg.get("editors", {})
    if editor not in editors:
        return False, f"Невідомий редактор: {editor}"

    meta = editors[editor]
    label = meta.get("label", editor)
    modules: List[Dict[str, Any]] = meta.get("modules", [])
    active = [m for m in modules if m.get("enabled")]

    if not active:
        return False, f"Для {label} немає увімкнених модулів. Налаштуйте їх у Modules або через smart-plan."

    if dry_run:
        names = ", ".join([str(m.get("id")) for m in active])
        return True, f"[DRY-RUN] {label}: {names}"

    for m in active:
        script = m.get("script")
        if not script:
            continue
        code = _run_script(script)
        if code != 0:
            return False, f"Модуль {m.get('id')} завершився з кодом {code}"

    return True, f"Очищення завершено: {label}"


def _perform_install(cfg: Dict[str, Any], editor: str) -> Tuple[bool, str]:
    editors = cfg.get("editors", {})
    if editor not in editors:
        return False, f"Невідомий редактор: {editor}"

    install = editors[editor].get("install", {})
    label = editors[editor].get("label", editor)
    itype = install.get("type")

    if itype == "dmg":
        import fnmatch

        pattern = install.get("pattern", "*.dmg")
        candidates = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(".dmg") and fnmatch.fnmatch(f, pattern)]
        if not candidates:
            return False, f"DMG-файлів за шаблоном '{pattern}' не знайдено в {SCRIPT_DIR}"
        dmg = sorted(candidates)[-1]
        subprocess.run(["open", os.path.join(SCRIPT_DIR, dmg)])
        return True, f"Відкрито DMG для {label}: {dmg}"

    if itype == "zip":
        import fnmatch

        pattern = install.get("pattern", "*.zip")
        candidates = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(".zip") and fnmatch.fnmatch(f, pattern)]
        if not candidates:
            return False, f"ZIP-файлів за шаблоном '{pattern}' не знайдено в {SCRIPT_DIR}"
        z = sorted(candidates)[-1]
        subprocess.run(["open", os.path.join(SCRIPT_DIR, z)])
        return True, f"Відкрито ZIP для {label}: {z}"

    if itype == "url":
        url = install.get("url")
        if not url:
            return False, f"URL для {label} не налаштовано"
        subprocess.run(["open", url])
        return True, f"Відкрито URL для {label}: {url}"

    return False, f"Install не налаштовано для {label}"


def _ensure_llm() -> bool:
    return CopilotLLM is not None and SystemMessage is not None and HumanMessage is not None


def _llm_smart_plan(cfg: Dict[str, Any], editor: str, user_query: str) -> Tuple[bool, str]:
    if not _ensure_llm():
        return False, "LLM недоступний (нема langchain_core або providers/copilot.py)"

    _load_env()

    llm = CopilotLLM()

    system_prompt = (
        "Ти System Cleanup Planner для редакторів коду (Windsurf, VS Code, Antigravity, Cursor).\n"
        "Отримуєш поточну JSON-конфігурацію модулів очищення і запит користувача.\n"
        "ТВОЄ ЗАВДАННЯ: запропонувати, які модулі увімкнути/вимкнути та які нові модулі потрібно створити.\n\n"
        "Відповідай СТРОГО у форматі JSON без пояснень поза JSON:\n"
        "{\n"
        "  \"modules_to_enable\": [{\"editor\": \"windsurf\", \"id\": \"deep_windsurf\"}],\n"
        "  \"modules_to_disable\": [{\"editor\": \"windsurf\", \"id\": \"hardware_spoof\"}],\n"
        "  \"modules_to_add\": [\n"
        "    {\"editor\": \"cursor\", \"id\": \"cursor_deep_cleanup\", \"name\": \"Cursor Deep Cleanup\", \"script\": \"./cursor_deep_cleanup.sh\", \"description\": \"...\", \"enabled\": true}\n"
        "  ],\n"
        "  \"notes\": \"короткі нотатки українською\"\n"
        "}\n"
    )

    payload = {
        "target_editor": editor,
        "current_config": cfg,
        "user_query": user_query,
    }

    resp = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)),
        ]
    )

    content = getattr(resp, "content", "")

    try:
        plan = json.loads(content)
    except Exception:
        return False, f"LLM повернув не-JSON відповідь. Raw: {content[:400]}"

    changed = False

    for item in plan.get("modules_to_enable", []) or []:
        e = item.get("editor")
        mid = item.get("id")
        if not e or not mid:
            continue
        ref = _find_module(cfg, e, mid)
        if ref and _set_module_enabled(cfg, ref, True):
            changed = True

    for item in plan.get("modules_to_disable", []) or []:
        e = item.get("editor")
        mid = item.get("id")
        if not e or not mid:
            continue
        ref = _find_module(cfg, e, mid)
        if ref and _set_module_enabled(cfg, ref, False):
            changed = True

    for item in plan.get("modules_to_add", []) or []:
        e = item.get("editor")
        if not e or e not in cfg.get("editors", {}):
            continue
        module = {
            "id": item.get("id"),
            "name": item.get("name"),
            "script": item.get("script"),
            "description": item.get("description"),
            "enabled": bool(item.get("enabled", True)),
        }
        if not module["id"] or not module["script"]:
            continue
        existing_ids = {m.get("id") for m in cfg["editors"][e].get("modules", [])}
        if module["id"] in existing_ids:
            continue
        cfg["editors"][e].setdefault("modules", []).append(module)
        changed = True

    if changed:
        _save_cleanup_config(cfg)

    notes = str(plan.get("notes") or "")
    return True, notes or "Smart-plan застосовано (оновлено cleanup_modules.json)"


def _llm_ask(cfg: Dict[str, Any], question: str) -> Tuple[bool, str]:
    if not _ensure_llm():
        return False, "LLM недоступний (нема langchain_core або providers/copilot.py)"

    _load_env()

    llm = CopilotLLM()
    _load_ui_settings()
    system_prompt = (
        "You are an assistant for a macOS cleanup CLI (Windsurf/VS Code/Antigravity/Cursor).\n"
        f"Reply in {lang_name(state.chat_lang)}. Be concise and practical.\n"
    )

    payload = {"cleanup_config": cfg, "question": question}
    resp = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)),
        ]
    )

    return True, str(getattr(resp, "content", ""))


# ================== LOCALIZATION ==================

# ================== TUI STATE & THEME ==================

style = DynamicStyle(lambda: Style.from_dict(THEMES.get(state.ui_theme, THEMES["monaco"])))


def log(text: str, category: str = "info") -> None:
    style_map = {
        "info": "class:log.info",
        "user": "class:log.user",
        "action": "class:log.action",
        "error": "class:log.error",
    }
    state.logs.append((style_map.get(category, "class:log.info"), f"{text}\n"))
    if len(state.logs) > 500:
        state.logs = state.logs[-400:]


def get_header():
    primary = localization.primary
    active_locales = " ".join(localization.selected)
    selected_editor = state.selected_editor or "-"

    return [
        ("class:header", " "),
        ("class:header.title", "SYSTEM CLI"),
        ("class:header.sep", " | "),
        ("class:header.label", "Editor: "),
        ("class:header.value", selected_editor),
        ("class:header.sep", " | "),
        ("class:header.label", "Locale: "),
        ("class:header.value", f"{primary} ({active_locales or 'none'})"),
        ("class:header", " "),
    ]


def get_context():
    result: List[Tuple[str, str]] = []

    result.append(("class:context.label", " Cleanup config: "))
    result.append(("class:context.value", f"{CLEANUP_CONFIG_PATH}\n"))
    result.append(("class:context.label", " Locales config: "))
    result.append(("class:context.value", f"{LOCALIZATION_CONFIG_PATH}\n\n"))

    result.append(("class:context.title", " Commands\n"))
    result.append(("class:context.label", " /help\n"))
    result.append(("class:context.label", " /run <editor> [--dry]\n"))
    result.append(("class:context.label", " /modules <editor>\n"))
    result.append(("class:context.label", " /enable <editor> <id> | /disable <editor> <id>\n"))
    result.append(("class:context.label", " /install <editor>\n"))
    result.append(("class:context.label", " /smart <editor> <query...>\n"))
    result.append(("class:context.label", " /ask <question...>\n"))
    result.append(("class:context.label", " /locales ua us eu\n"))
    result.append(("class:context.label", " /autopilot <task...>\n"))
    result.append(("class:context.label", " /monitor status|start|stop|source <watchdog|fs_usage|opensnoop>|sudo <on|off>\n"))
    result.append(("class:context.label", " /monitor-targets list|add <key>|remove <key>|clear|save\n"))
    result.append(("class:context.label", " /llm status|set provider <copilot>|set main <model>|set vision <model>\n"))
    result.append(("class:context.label", " /theme status|set <monaco|dracula|nord|gruvbox>\n"))
    result.append(("class:context.label", " /lang status|set ui <code>|set chat <code>\n"))

    return result


def get_log_cursor_position():
    r = 0
    for _, text in state.logs:
        r += text.count("\n")
    return Point(x=0, y=r)


# ================== MENU CONTENT ==================


def _get_monitoring_menu_items() -> List[Tuple[str, MenuLevel]]:
    return [
        ("menu.monitoring.targets", MenuLevel.MONITOR_TARGETS),
        ("menu.monitoring.start_stop", MenuLevel.MONITOR_CONTROL),
    ]


def _get_custom_tasks_menu_items() -> List[Tuple[str, Any]]:
    return []


def _get_settings_menu_items() -> List[Tuple[str, MenuLevel]]:
    return [
        ("menu.settings.llm", MenuLevel.LLM_SETTINGS),
        ("menu.settings.agent", MenuLevel.AGENT_SETTINGS),
        ("menu.settings.appearance", MenuLevel.APPEARANCE),
        ("menu.settings.language", MenuLevel.LANGUAGE),
        ("menu.settings.locales", MenuLevel.LOCALES),
        ("menu.settings.unsafe_mode", MenuLevel.UNSAFE_MODE),
    ]


def _get_llm_menu_items() -> List[Tuple[str, str]]:
    _load_env()
    _load_llm_settings()
    provider = str(os.getenv("LLM_PROVIDER") or "copilot")
    main_model = str(os.getenv("COPILOT_MODEL") or "")
    vision_model = str(os.getenv("COPILOT_VISION_MODEL") or "")
    return [
        (f"Provider: {provider}", "provider"),
        (f"Main model: {main_model}", "main"),
        (f"Vision model: {vision_model}", "vision"),
    ]


def _get_agent_menu_items() -> List[Tuple[str, str]]:
    global agent_chat_mode
    enabled = "ON" if agent_session.enabled else "OFF"
    mode = "ON" if agent_chat_mode else "OFF"
    return [
        (f"Agent enabled: {enabled}", "agent_enabled"),
        (f"Agent mode: {mode}", "agent_mode"),
        ("Agent reset session", "agent_reset"),
    ]


def _get_editors_list() -> List[Tuple[str, str]]:
    global cleanup_cfg
    cleanup_cfg = _load_cleanup_config()
    return _list_editors(cleanup_cfg)


# ================== INPUT / COMMANDS ==================

def _apply_locales_from_line(text: str) -> None:
    raw_codes = text.strip().split()
    if not raw_codes:
        return

    codes: List[str] = []
    for token in raw_codes:
        code = token.strip().upper().strip(".,;")
        if any(l.code == code for l in AVAILABLE_LOCALES):
            if code not in codes:
                codes.append(code)
        else:
            log(f"Невідома локаль: {token}", "error")

    if not codes:
        return

    localization.selected = codes
    localization.primary = codes[0]
    localization.save()
    log(f"Оновлено локалі: primary={localization.primary}, selected={' '.join(localization.selected)}", "action")


def _handle_command(cmd: str) -> None:
    global cleanup_cfg

    parts = cmd.strip().split(" ")
    command = parts[0].lower()
    args = parts[1:]

    cleanup_cfg = _load_cleanup_config()

    if command in {"/help", "/h"}:
        log("/run <editor> [--dry] | /modules <editor> | /enable <editor> <id> | /disable <editor> <id>", "info")
        log("/install <editor> | /smart <editor> <query...> | /ask <question...> | /locales <codes...>", "info")
        log("/autopilot <task...> (потрібно CONFIRM_AUTOPILOT)", "info")
        log("/monitor status | /monitor start | /monitor stop | /monitor source <watchdog|fs_usage|opensnoop> | /monitor sudo <on|off>", "info")
        log("/monitor-targets list|add <key>|remove <key>|clear|save", "info")
        log("/llm status | /llm set provider <copilot> | /llm set main <model> | /llm set vision <model>", "info")
        log("/theme status | /theme set <monaco|dracula|nord|gruvbox>", "info")
        log("/lang status | /lang set ui <code> | /lang set chat <code>", "info")
        log("/agent-reset | /agent-on | /agent-off | /agent-mode [on|off|toggle] | /chat-help", "info")
        log("Підказка: agent run_module потребує CONFIRM_RUN. Autopilot shell/applescript потребує CONFIRM_SHELL / CONFIRM_APPLESCRIPT.", "info")
        return

    if command == "/chat-help":
        log("Agent chat: введи будь-який текст без '/' — і він піде в чат (якщо /agent-mode on).", "info")
        log("Керування: /agent-on | /agent-off | /agent-reset | /agent-mode [on|off|toggle]", "info")
        log("Безпека: для запуску .sh модулів через agent потрібно додати CONFIRM_RUN у повідомлення.", "info")
        log("Autopilot: /autopilot <task...> + CONFIRM_AUTOPILOT (і опційно CONFIRM_SHELL/CONFIRM_APPLESCRIPT).", "info")
        return

    if command == "/autopilot":
        task = " ".join(args).strip()
        if not task:
            log("Usage: /autopilot <task...> [CONFIRM_AUTOPILOT]", "error")
            return

        _load_ui_settings()
        unsafe_mode = bool(getattr(state, "ui_unsafe_mode", False))

        allow_autopilot = unsafe_mode or _is_confirmed_autopilot(cmd)
        allow_shell = unsafe_mode or _is_confirmed_shell(cmd)
        allow_applescript = unsafe_mode or _is_confirmed_applescript(cmd)

        if not allow_autopilot:
            log("Autopilot confirmation required. Add CONFIRM_AUTOPILOT to the same line (or enable Unsafe mode).", "error")
            return

        def _runner() -> None:
            try:
                from system_ai.autopilot.autopilot_agent import AutopilotAgent

                agent = AutopilotAgent(
                    allow_autopilot=allow_autopilot,
                    allow_shell=allow_shell,
                    allow_applescript=allow_applescript,
                )

                log(f"Autopilot started. shell={'ON' if allow_shell else 'OFF'} applescript={'ON' if allow_applescript else 'OFF'}", "action")

                for event in agent.run_task(task, max_steps=30):
                    step = event.get("step")
                    done = event.get("done")
                    plan = event.get("plan")
                    actions_results = event.get("actions_results") or []
                    thought = getattr(plan, "thought", "") if plan else ""
                    result_message = getattr(plan, "result_message", "") if plan else ""
                    log(f"[AP] Step {step}: {thought}", "info")
                    if result_message:
                        log(f"[AP] {result_message}", "action")
                    for r in actions_results:
                        tool = r.get("tool")
                        status = r.get("status")
                        if tool and status:
                            log(f"[AP] tool={tool} status={status}", "info")
                    if done:
                        log("Autopilot done.", "action")
                        break
            except Exception as e:
                log(f"Autopilot error: {e}", "error")

        threading.Thread(target=_runner, daemon=True).start()
        return

    if command == "/agent-reset":
        agent_session.reset()
        log("Agent session reset.", "action")
        return

    if command == "/agent-off":
        agent_session.enabled = False
        log("Agent chat disabled.", "action")
        return

    if command == "/agent-on":
        agent_session.enabled = True
        log("Agent chat enabled.", "action")
        return

    if command == "/agent-mode":
        global agent_chat_mode
        mode = (args[0].lower() if args else "").strip()
        if mode in {"", "status"}:
            log(f"Agent mode: {'ON' if agent_chat_mode else 'OFF'}", "info")
            return
        if mode == "toggle":
            agent_chat_mode = not agent_chat_mode
            log(f"Agent mode: {'ON' if agent_chat_mode else 'OFF'}", "action")
            return
        if mode in {"on", "enable", "enabled"}:
            agent_chat_mode = True
            log("Agent mode: ON", "action")
            return
        if mode in {"off", "disable", "disabled"}:
            agent_chat_mode = False
            log("Agent mode: OFF", "action")
            return
        log("Usage: /agent-mode [on|off|toggle]", "error")
        return

    if command == "/locales":
        _apply_locales_from_line(" ".join(args))
        return

    if command == "/run":
        if not args:
            log("Usage: /run <editor> [--dry]", "error")
            return
        editor = args[0]
        dry = "--dry" in args or "--dry-run" in args
        ok, msg = _run_cleanup(cleanup_cfg, editor, dry_run=dry)
        log(msg, "action" if ok else "error")
        return

    if command == "/modules":
        if not args:
            log("Usage: /modules <editor>", "error")
            return
        editor = args[0]
        meta = cleanup_cfg.get("editors", {}).get(editor)
        if not meta:
            log(f"Невідомий редактор: {editor}", "error")
            return
        mods = meta.get("modules", [])
        if not mods:
            log(f"Модулів для {editor} немає. Використайте /smart або додайте вручну.", "info")
            return
        for m in mods:
            mark = "ON" if m.get("enabled") else "OFF"
            log(f"[{mark}] {m.get('id')} - {m.get('name')} (script={m.get('script')})", "info")
        return

    if command in {"/enable", "/disable"}:
        if len(args) < 2:
            log("Usage: /enable <editor> <id> | /disable <editor> <id>", "error")
            return
        editor = args[0]
        mid = args[1]
        ref = _find_module(cleanup_cfg, editor, mid)
        if not ref:
            log("Модуль не знайдено.", "error")
            return
        enabled = command == "/enable"
        ok = _set_module_enabled(cleanup_cfg, ref, enabled)
        if ok:
            log(f"Модуль {'увімкнено' if enabled else 'вимкнено'}: {editor}/{mid}", "action")
        else:
            log("Не вдалося змінити статус модуля.", "error")
        return

    if command == "/install":
        if not args:
            log("Usage: /install <editor>", "error")
            return
        ok, msg = _perform_install(cleanup_cfg, args[0])
        log(msg, "action" if ok else "error")
        return

    if command == "/smart":
        if len(args) < 2:
            log("Usage: /smart <editor> <query...>", "error")
            return
        editor = args[0]
        query = " ".join(args[1:])
        ok, msg = _llm_smart_plan(cleanup_cfg, editor, query)
        log(msg, "action" if ok else "error")
        return

    if command == "/ask":
        if not args:
            log("Usage: /ask <question...>", "error")
            return
        ok, msg = _llm_ask(cleanup_cfg, " ".join(args))
        log(msg, "action" if ok else "error")
        return

    if command == "/monitor":
        sub = (args[0].lower() if args else "").strip()
        rest = args[1:]
        if sub in {"", "status"}:
            st = _tool_monitor_status()
            log(
                f"Monitoring: active={st.get('active')} source={st.get('source')} sudo={st.get('use_sudo')} targets={st.get('targets_count')}",
                "info",
            )
            log(f"DB: {st.get('db')}", "info")
            return
        if sub == "start":
            out = _tool_monitor_start()
            log(str(out.get("message") or ""), "action" if out.get("ok") else "error")
            return
        if sub == "stop":
            out = _tool_monitor_stop()
            log(str(out.get("message") or ""), "action" if out.get("ok") else "error")
            return
        if sub == "source":
            if not rest:
                log("Usage: /monitor source <watchdog|fs_usage|opensnoop>", "error")
                return
            out = _tool_monitor_set_source({"source": rest[0]})
            log(str(out.get("source") or out.get("error") or ""), "action" if out.get("ok") else "error")
            return
        if sub == "sudo":
            if not rest:
                log("Usage: /monitor sudo <on|off>", "error")
                return
            raw = rest[0].strip().lower()
            use_sudo = raw in {"1", "true", "yes", "on", "enable", "enabled"}
            out = _tool_monitor_set_use_sudo({"use_sudo": use_sudo})
            if out.get("ok"):
                log(f"sudo={'ON' if out.get('use_sudo') else 'OFF'}", "action")
            else:
                log(str(out.get("error") or ""), "error")
            return
        log("Usage: /monitor status|start|stop|source <...>|sudo <on|off>", "error")
        return

    if command in {"/monitor-targets", "/monitor_targets"}:
        sub = (args[0].lower() if args else "list").strip()
        rest = args[1:]
        if sub in {"list", "ls", "status"}:
            if not state.monitor_targets:
                log("Monitor targets: (none)", "info")
                return
            for k in sorted(state.monitor_targets):
                log(f"[x] {k}", "info")
            return
        if sub in {"add", "+"}:
            if not rest:
                log("Usage: /monitor-targets add <key>", "error")
                return
            key = str(rest[0]).strip()
            if not key:
                log("Invalid key.", "error")
                return
            state.monitor_targets.add(key)
            log(f"Monitor target added: {key}", "action")
            return
        if sub in {"remove", "rm", "-"}:
            if not rest:
                log("Usage: /monitor-targets remove <key>", "error")
                return
            key = str(rest[0]).strip()
            if key in state.monitor_targets:
                state.monitor_targets.remove(key)
                log(f"Monitor target removed: {key}", "action")
            else:
                log(f"Not selected: {key}", "error")
            return
        if sub == "clear":
            state.monitor_targets = set()
            log("Monitor targets cleared.", "action")
            return
        if sub == "save":
            if _save_monitor_targets():
                log("Monitor targets saved.", "action")
            else:
                log("Failed to save monitor targets.", "error")
            return
        log("Usage: /monitor-targets list|add <key>|remove <key>|clear|save", "error")
        return

    if command == "/llm":
        sub = (args[0].lower() if args else "status").strip()
        rest = args[1:]
        if sub in {"", "status"}:
            _load_env()
            _load_llm_settings()
            log(f"LLM provider: {os.getenv('LLM_PROVIDER')}", "info")
            log(f"LLM main model: {os.getenv('COPILOT_MODEL')}", "info")
            log(f"LLM vision model: {os.getenv('COPILOT_VISION_MODEL')}", "info")
            return
        if sub == "set":
            if len(rest) < 2:
                log("Usage: /llm set provider|main|vision <value>", "error")
                return
            field = str(rest[0]).strip().lower()
            val = str(rest[1]).strip()
            _load_env()
            _load_llm_settings()
            provider = str(os.getenv("LLM_PROVIDER") or "copilot").strip().lower() or "copilot"
            main_model = str(os.getenv("COPILOT_MODEL") or "gpt-4o").strip() or "gpt-4o"
            vision_model = str(os.getenv("COPILOT_VISION_MODEL") or "gpt-4.1").strip() or "gpt-4.1"
            if field == "provider":
                provider = val.lower()
            elif field == "main":
                main_model = val
            elif field == "vision":
                vision_model = val
            else:
                log("Unknown field. Use provider|main|vision", "error")
                return
            if _save_llm_settings(provider, main_model, vision_model):
                _reset_agent_llm()
                log("LLM settings saved.", "action")
            else:
                log("Failed to save LLM settings.", "error")
            return
        log("Usage: /llm status|set provider <copilot>|set main <model>|set vision <model>", "error")
        return

    if command == "/theme":
        sub = (args[0].lower() if args else "status").strip()
        rest = args[1:]
        if sub in {"", "status"}:
            log(f"Theme: {state.ui_theme}", "info")
            log(f"UI settings: {UI_SETTINGS_PATH}", "info")
            return
        if sub == "set":
            if not rest:
                log("Usage: /theme set <monaco|dracula|nord|gruvbox>", "error")
                return
            t = str(rest[0]).strip().lower()
            if t not in set(THEME_NAMES):
                log("Unknown theme. Use monaco|dracula|nord|gruvbox", "error")
                return
            state.ui_theme = t
            if _save_ui_settings():
                log(f"Theme set: {state.ui_theme}", "action")
            else:
                log("Failed to save UI settings.", "error")
            return
        log("Usage: /theme status|set <monaco|dracula|nord|gruvbox>", "error")
        return

    if command == "/lang":
        sub = (args[0].lower() if args else "status").strip()
        rest = args[1:]
        if sub in {"", "status"}:
            log(f"UI language: {state.ui_lang} ({lang_name(state.ui_lang)})", "info")
            log(f"Chat language: {state.chat_lang} ({lang_name(state.chat_lang)})", "info")
            return
        if sub == "set":
            if len(rest) < 2:
                log("Usage: /lang set ui <code> | /lang set chat <code>", "error")
                return
            which = str(rest[0]).strip().lower()
            code = normalize_lang(rest[1])
            if which == "ui":
                state.ui_lang = code
                _save_ui_settings()
                log(f"UI language set: {state.ui_lang} ({lang_name(state.ui_lang)})", "action")
                return
            if which == "chat":
                state.chat_lang = code
                _save_ui_settings()
                _reset_agent_llm()
                log(f"Chat language set: {state.chat_lang} ({lang_name(state.chat_lang)})", "action")
                return
            log("Usage: /lang set ui <code> | /lang set chat <code>", "error")
            return
        log("Usage: /lang status|set ui <code>|set chat <code>", "error")
        return

    log(f"Невідома команда: {cmd}", "error")


def _handle_input(buff: Buffer) -> None:
    text = buff.text.strip()
    if not text:
        return
    buff.text = ""

    if text.startswith("/"):
        _handle_command(text)
        return

    # якщо це чисто коди локалей – трактуємо як /locales
    tokens = [t.strip().upper().strip(".,;") for t in text.split() if t.strip()]
    if tokens and all(any(l.code == tok for l in AVAILABLE_LOCALES) for tok in tokens):
        _apply_locales_from_line(text)
        return

    # інакше – агентний чат (за замовчуванням)
    if agent_chat_mode and agent_session.enabled:
        log(text, "user")
        ok, answer = _agent_send(text)
        log(answer, "action" if ok else "error")
    elif not agent_chat_mode:
        log("Agent mode OFF. Увімкни через /agent-mode on або введи /help.", "error")
    else:
        log("Agent chat вимкнено. Увімкни через /agent-on або введи /help.", "error")


input_buffer = Buffer(multiline=False, accept_handler=_handle_input)


def get_input_prompt():
    if state.menu_level != MenuLevel.NONE:
        return [("class:input.menu", " MENU "), ("class:input.hint", " ↑↓ рух | Enter/Space дія | F2 меню ")]
    return [("class:input.prompt", " > ")]


def get_prompt_width() -> int:
    return 55 if state.menu_level != MenuLevel.NONE else 3


def get_status():
    if state.menu_level != MenuLevel.NONE:
        mode_indicator = [("class:status.menu", " MENU "), ("class:status", " ")]
    else:
        mode_indicator = [("class:status.chat", " INPUT "), ("class:status", " ")]

    monitor_tag = f"MON:{'ON' if state.monitor_active else 'OFF'}:{state.monitor_source}"

    return mode_indicator + [
        ("class:status.ready", f" {state.status} "),
        ("class:status", " "),
        ("class:status.key", monitor_tag),
        ("class:status", " | "),
        ("class:status.key", "F2: Menu"),
        ("class:status", " | "),
        ("class:status.key", "Ctrl+C: Quit"),
    ]


@dataclass
class _DummyProcService:
    running: bool = False

    def start(self, *args: Any, **kwargs: Any) -> Tuple[bool, str]:
        self.running = True
        return True, "Monitoring started."

    def stop(self) -> Tuple[bool, str]:
        self.running = False
        return True, "Monitoring stopped."


monitor_service = _DummyProcService()
fs_usage_service = _DummyProcService()
opensnoop_service = _DummyProcService()


def _monitor_start_selected() -> Tuple[bool, str]:
    if state.monitor_source == "watchdog":
        return monitor_service.start()
    if state.monitor_source == "fs_usage":
        return fs_usage_service.start()
    if state.monitor_source == "opensnoop":
        return opensnoop_service.start()
    return False, "Source not implemented"


def _monitor_stop_selected() -> Tuple[bool, str]:
    ok1, msg1 = monitor_service.stop()
    ok2, msg2 = fs_usage_service.stop()
    ok3, msg3 = opensnoop_service.stop()
    if ok1 and ok2 and ok3:
        return True, msg3 or msg2 or msg1
    return False, "Monitoring stop failed"


def _monitor_summary_start_if_needed() -> None:
    try:
        monitor_summary_service.start()
    except Exception:
        return


def _monitor_summary_stop_if_needed() -> None:
    try:
        monitor_summary_service.stop()
    except Exception:
        return


def _get_cleanup_cfg() -> Any:
    global cleanup_cfg
    return cleanup_cfg


def _set_cleanup_cfg(cfg: Any) -> None:
    global cleanup_cfg
    cleanup_cfg = cfg


def run_tui() -> None:
    show_menu, get_menu_content = build_menu(
        state=state,
        MenuLevel=MenuLevel,
        tr=lambda k, l: tr(k, l),
        lang_name=lang_name,
        MAIN_MENU_ITEMS=MAIN_MENU_ITEMS,
        get_custom_tasks_menu_items=_get_custom_tasks_menu_items,
        get_monitoring_menu_items=_get_monitoring_menu_items,
        get_settings_menu_items=_get_settings_menu_items,
        get_llm_menu_items=_get_llm_menu_items,
        get_agent_menu_items=_get_agent_menu_items,
        get_editors_list=_get_editors_list,
        get_cleanup_cfg=lambda: cleanup_cfg,
        AVAILABLE_LOCALES=AVAILABLE_LOCALES,
        localization=localization,
        get_monitor_menu_items=_get_monitor_menu_items,
        normalize_menu_index=_normalize_menu_index,
        MONITOR_TARGETS_PATH=MONITOR_TARGETS_PATH,
        MONITOR_EVENTS_DB_PATH=MONITOR_EVENTS_DB_PATH,
        CLEANUP_CONFIG_PATH=CLEANUP_CONFIG_PATH,
        LOCALIZATION_CONFIG_PATH=LOCALIZATION_CONFIG_PATH,
    )

    kb = build_keybindings(
        state=state,
        MenuLevel=MenuLevel,
        show_menu=show_menu,
        MAIN_MENU_ITEMS=MAIN_MENU_ITEMS,
        get_custom_tasks_menu_items=_get_custom_tasks_menu_items,
        TOP_LANGS=TOP_LANGS,
        lang_name=lang_name,
        log=log,
        save_ui_settings=_save_ui_settings,
        reset_agent_llm=_reset_agent_llm,
        save_monitor_settings=_save_monitor_settings,
        save_monitor_targets=_save_monitor_targets,
        get_monitoring_menu_items=_get_monitoring_menu_items,
        get_settings_menu_items=_get_settings_menu_items,
        get_llm_menu_items=_get_llm_menu_items,
        get_agent_menu_items=_get_agent_menu_items,
        get_editors_list=_get_editors_list,
        get_cleanup_cfg=_get_cleanup_cfg,
        set_cleanup_cfg=_set_cleanup_cfg,
        load_cleanup_config=_load_cleanup_config,
        run_cleanup=lambda cfg, editor, dry: _run_cleanup(cfg, editor, dry_run=dry),
        perform_install=_perform_install,
        find_module=_find_module,
        set_module_enabled=_set_module_enabled,
        AVAILABLE_LOCALES=AVAILABLE_LOCALES,
        localization=localization,
        get_monitor_menu_items=_get_monitor_menu_items,
        normalize_menu_index=_normalize_menu_index,
        monitor_stop_selected=_monitor_stop_selected,
        monitor_start_selected=_monitor_start_selected,
        monitor_resolve_watch_items=_monitor_resolve_watch_items,
        monitor_service=monitor_service,
        fs_usage_service=fs_usage_service,
        opensnoop_service=opensnoop_service,
    )

    app = build_app(
        get_header=get_header,
        get_context=get_context,
        get_logs=lambda: state.logs,
        get_log_cursor_position=get_log_cursor_position,
        get_menu_content=get_menu_content,
        get_input_prompt=get_input_prompt,
        get_prompt_width=get_prompt_width,
        get_status=get_status,
        input_buffer=input_buffer,
        show_menu=show_menu,
        kb=kb,
        style=style,
    )

    runtime = TuiRuntime(
        app=app,
        log=log,
        load_monitor_targets=_load_monitor_targets,
        load_monitor_settings=_load_monitor_settings,
        load_ui_settings=_load_ui_settings,
        load_env=_load_env,
        load_llm_settings=_load_llm_settings,
        apply_default_monitor_targets=_apply_default_monitor_targets,
    )
    tui_run_tui(runtime)


def _tool_app_command(args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = str(args.get("command") or "").strip()
    if not cmd.startswith("/"):
        return {"ok": False, "error": "command must start with '/'"}

    perms = _agent_last_permissions
    cmd_to_run = cmd
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_autopilot and "confirm_autopilot" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_AUTOPILOT"
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_shell and "confirm_shell" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_SHELL"
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_applescript and "confirm_applescript" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_APPLESCRIPT"

    captured: List[Tuple[str, str]] = []
    original_log = globals().get("log")

    def _cap(text: str, category: str = "info") -> None:
        captured.append((category, str(text)))

    try:
        globals()["log"] = _cap
        _handle_command(cmd_to_run)
    finally:
        globals()["log"] = original_log

    return {"ok": True, "lines": captured[:200]}


def _tool_monitor_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "active": bool(state.monitor_active),
        "source": state.monitor_source,
        "use_sudo": bool(state.monitor_use_sudo),
        "targets_count": len(state.monitor_targets),
        "db": MONITOR_EVENTS_DB_PATH,
    }


def _tool_monitor_set_source(args: Dict[str, Any]) -> Dict[str, Any]:
    src = str(args.get("source") or "").strip().lower()
    if src not in {"watchdog", "fs_usage", "opensnoop"}:
        return {"ok": False, "error": "Invalid source. Use watchdog|fs_usage|opensnoop"}
    if state.monitor_active:
        return {"ok": False, "error": "Stop monitoring before changing source"}
    _load_env()
    state.monitor_source = src
    if src in {"fs_usage", "opensnoop"} and not state.monitor_use_sudo:
        if str(os.getenv("SUDO_PASSWORD") or "").strip():
            state.monitor_use_sudo = True
    _save_monitor_settings()
    return {"ok": True, "source": state.monitor_source}


def _tool_monitor_set_use_sudo(args: Dict[str, Any]) -> Dict[str, Any]:
    use_sudo = args.get("use_sudo")
    if not isinstance(use_sudo, bool):
        raw = str(use_sudo or "").strip().lower()
        if raw in {"1", "true", "yes", "on", "enable", "enabled"}:
            use_sudo = True
        elif raw in {"0", "false", "no", "off", "disable", "disabled"}:
            use_sudo = False
        else:
            return {"ok": False, "error": "use_sudo must be boolean"}
    if state.monitor_active:
        return {"ok": False, "error": "Stop monitoring before changing sudo setting"}
    state.monitor_use_sudo = bool(use_sudo)
    _save_monitor_settings()
    return {"ok": True, "use_sudo": state.monitor_use_sudo}


def _tool_monitor_start() -> Dict[str, Any]:
    if state.monitor_active:
        return {"ok": True, "message": "Monitoring already active"}
    if not state.monitor_targets:
        return {"ok": False, "error": "No targets selected"}
    ok, msg = _monitor_start_selected()
    state.monitor_active = bool(monitor_service.running or fs_usage_service.running or opensnoop_service.running)
    if ok and state.monitor_active:
        _monitor_summary_start_if_needed()
    return {"ok": ok, "message": msg, "active": state.monitor_active}


def _tool_monitor_stop() -> Dict[str, Any]:
    ok, msg = _monitor_stop_selected()
    state.monitor_active = bool(monitor_service.running or fs_usage_service.running or opensnoop_service.running)
    _monitor_summary_stop_if_needed()
    return {"ok": ok, "message": msg, "active": state.monitor_active}


def _monitor_resolve_watch_items(targets: Set[str]) -> List[Tuple[str, str]]:
    home = os.path.expanduser("~")
    items: List[Tuple[str, str]] = []

    def add_if_dir(path: str, target_key: str) -> None:
        if os.path.isdir(path):
            items.append((path, target_key))

    for t in sorted(targets):
        if t.startswith("browser:"):
            name = t.split(":", 1)[1]
            low = name.lower()
            if low == "safari":
                add_if_dir(os.path.join(home, "Library", "Safari"), t)
                add_if_dir(os.path.join(home, "Library", "Containers", "com.apple.Safari"), t)
            elif "chrome" in low:
                add_if_dir(os.path.join(home, "Library", "Application Support", "Google", "Chrome"), t)
                add_if_dir(os.path.join(home, "Library", "Caches", "Google", "Chrome"), t)
            elif "chromium" in low:
                add_if_dir(os.path.join(home, "Library", "Application Support", "Chromium"), t)
                add_if_dir(os.path.join(home, "Library", "Caches", "Chromium"), t)
            elif "firefox" in low:
                add_if_dir(os.path.join(home, "Library", "Application Support", "Firefox"), t)
                add_if_dir(os.path.join(home, "Library", "Caches", "Firefox"), t)
            else:
                add_if_dir(os.path.join(home, "Library", "Application Support", name), t)
                add_if_dir(os.path.join(home, "Library", "Caches", name), t)

        if t.startswith("editor:"):
            editor_key = t.split(":", 1)[1]
            label = ""
            try:
                label = str(cleanup_cfg.get("editors", {}).get(editor_key, {}).get("label") or "")
            except Exception:
                label = ""
            add_if_dir(os.path.join(home, "Library", "Application Support", editor_key), t)
            add_if_dir(os.path.join(home, "Library", "Caches", editor_key), t)

    # unique by (path,target)
    seen: Set[Tuple[str, str]] = set()
    uniq: List[Tuple[str, str]] = []
    for p, k in items:
        key = (p, k)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((p, k))
    return uniq


def _load_monitor_targets() -> None:
    try:
        if not os.path.exists(MONITOR_TARGETS_PATH):
            return
        with open(MONITOR_TARGETS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        selected = data.get("selected") or []
        if isinstance(selected, list):
            state.monitor_targets = {str(x) for x in selected if x}
    except Exception:
        return


def _save_monitor_targets() -> bool:
    try:
        os.makedirs(SYSTEM_CLI_DIR, exist_ok=True)
        payload = {"selected": sorted(state.monitor_targets)}
        with open(MONITOR_TARGETS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _scan_installed_apps(app_dirs: List[str]) -> List[str]:
    apps: List[str] = []
    for d in app_dirs:
        try:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if name.endswith(".app"):
                    apps.append(name[:-4])
        except Exception:
            continue
    # unique preserve order
    seen: Set[str] = set()
    out: List[str] = []
    for a in apps:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _scan_installed_app_paths(app_dirs: List[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for d in app_dirs:
        try:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if not name.endswith(".app"):
                    continue
                app_name = name[:-4]
                out.append((app_name, os.path.join(d, name)))
        except Exception:
            continue
    # unique by name, prefer first occurrence
    seen: Set[str] = set()
    uniq: List[Tuple[str, str]] = []
    for app_name, app_path in out:
        if app_name in seen:
            continue
        seen.add(app_name)
        uniq.append((app_name, app_path))
    return uniq


def _read_bundle_id(app_path: str) -> str:
    try:
        plist_path = os.path.join(app_path, "Contents", "Info.plist")
        if not os.path.exists(plist_path):
            return ""
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        bid = data.get("CFBundleIdentifier")
        return str(bid) if bid else ""
    except Exception:
        return ""


def _get_installed_browsers() -> List[str]:
    app_dirs = ["/Applications", os.path.expanduser("~/Applications")]
    installed = _scan_installed_app_paths(app_dirs)
    keywords_name = [
        "safari",
        "chrome",
        "chromium",
        "firefox",
        "brave",
        "arc",
        "edge",
        "opera",
        "vivaldi",
        "orion",
        "tor",
        "duckduckgo",
        "waterfox",
        "librewolf",
        "zen",
        "yandex",
    ]
    keywords_bundle = [
        "safari",
        "chrome",
        "chromium",
        "firefox",
        "brave",
        "arc",
        "edge",
        "opera",
        "vivaldi",
        "orion",
        "torbrowser",
        "duckduckgo",
        "browser",
    ]
    browsers: List[str] = []
    for app_name, app_path in installed:
        low = app_name.lower()
        if any(k in low for k in keywords_name):
            browsers.append(app_name)
            continue
        bid = _read_bundle_id(app_path).lower()
        if bid and any(k in bid for k in keywords_bundle):
            browsers.append(app_name)
    return sorted({b for b in browsers}, key=lambda x: x.lower())


@dataclass
class MonitorMenuItem:
    key: str
    label: str
    selectable: bool
    category: str
    origin: str = ""


def _get_monitor_menu_items() -> List[MonitorMenuItem]:
    items: List[MonitorMenuItem] = []

    # Editors (from cleanup config)
    items.append(MonitorMenuItem(key="__hdr_editors__", label="EDITORS", selectable=False, category="header"))
    for key, label in _get_editors_list():
        items.append(MonitorMenuItem(key=f"editor:{key}", label=f"{key} - {label}", selectable=True, category="editor"))

    # Browsers (auto-detected)
    items.append(MonitorMenuItem(key="__hdr_browsers__", label="BROWSERS", selectable=False, category="header"))
    app_dirs = ["/Applications", os.path.expanduser("~/Applications")]
    installed_paths = dict(_scan_installed_app_paths(app_dirs))
    browsers = _get_installed_browsers()
    if not browsers:
        items.append(MonitorMenuItem(key="__no_browsers__", label="(no browsers detected in /Applications)", selectable=False, category="note"))
    else:
        for app in browsers:
            origin = ""
            p = installed_paths.get(app, "")
            if p:
                origin = os.path.dirname(p)
            items.append(MonitorMenuItem(key=f"browser:{app}", label=app, selectable=True, category="browser", origin=origin))

    return items


def _normalize_menu_index(items: List[MonitorMenuItem]) -> None:
    if not items:
        state.menu_index = 0
        return

    state.menu_index = max(0, min(state.menu_index, len(items) - 1))
    if items[state.menu_index].selectable:
        return

    # move to nearest selectable
    for direction in (1, -1):
        idx = state.menu_index
        while 0 <= idx < len(items):
            if items[idx].selectable:
                state.menu_index = idx
                return
            idx += direction
    state.menu_index = 0


def _apply_default_monitor_targets() -> None:
    # Default test set: antigravity + Safari + Chrome (if available)
    if state.monitor_targets:
        return
    state.monitor_targets.add("editor:antigravity")
    browsers = _get_installed_browsers()
    for preferred in ("Safari", "Google Chrome", "Chrome"):
        if preferred in browsers:
            state.monitor_targets.add(f"browser:{preferred}")


localization = LocalizationConfig.load()
cleanup_cfg = _load_cleanup_config()


def log(text: str, category: str = "info") -> None:
    style_map = {
        "info": "class:log.info",
        "user": "class:log.user",
        "action": "class:log.action",
        "error": "class:log.error",
    }
    state.logs.append((style_map.get(category, "class:log.info"), f"{text}\n"))
    if len(state.logs) > 500:
        state.logs = state.logs[-400:]


def get_header():
    primary = localization.primary
    active_locales = " ".join(localization.selected)
    selected_editor = state.selected_editor or "-"

    return [
        ("class:header", " "),
        ("class:header.title", "SYSTEM CLI"),
        ("class:header.sep", " | "),
        ("class:header.label", "Editor: "),
        ("class:header.value", selected_editor),
        ("class:header.sep", " | "),
        ("class:header.label", "Locale: "),
        ("class:header.value", f"{primary} ({active_locales or 'none'})"),
        ("class:header", " "),
    ]


def get_context():
    result: List[Tuple[str, str]] = []

    result.append(("class:context.label", " Cleanup config: "))
    result.append(("class:context.value", f"{CLEANUP_CONFIG_PATH}\n"))
    result.append(("class:context.label", " Locales config: "))
    result.append(("class:context.value", f"{LOCALIZATION_CONFIG_PATH}\n\n"))

    result.append(("class:context.title", " Commands\n"))
    result.append(("class:context.label", " /help\n"))
    result.append(("class:context.label", " /run <editor> [--dry]\n"))
    result.append(("class:context.label", " /modules <editor>\n"))
    result.append(("class:context.label", " /enable <editor> <id> | /disable <editor> <id>\n"))
    result.append(("class:context.label", " /install <editor>\n"))
    result.append(("class:context.label", " /smart <editor> <query...>\n"))
    result.append(("class:context.label", " /ask <question...>\n"))
    result.append(("class:context.label", " /locales ua us eu\n"))
    result.append(("class:context.label", " /autopilot <task...>\n"))
    result.append(("class:context.label", " /monitor status|start|stop|source <watchdog|fs_usage|opensnoop>|sudo <on|off>\n"))
    result.append(("class:context.label", " /monitor-targets list|add <key>|remove <key>|clear|save\n"))
    result.append(("class:context.label", " /llm status|set provider <copilot>|set main <model>|set vision <model>\n"))
    result.append(("class:context.label", " /theme status|set <monaco|dracula|nord|gruvbox>\n"))
    result.append(("class:context.label", " /lang status|set ui <code>|set chat <code>\n"))

    return result


def get_log_cursor_position():
    r = 0
    for _, text in state.logs:
        r += text.count("\n")
    return Point(x=0, y=r)


# ================== MENU CONTENT ==================


def _get_editors_list() -> List[Tuple[str, str]]:
    global cleanup_cfg
    cleanup_cfg = _load_cleanup_config()
    return _list_editors(cleanup_cfg)


def _handle_input(buff: Buffer) -> None:
    text = buff.text.strip()
    if not text:
        return
    buff.text = ""

    if text.startswith("/"):
        _handle_command(text)
        return

    # якщо це чисто коди локалей – трактуємо як /locales
    tokens = [t.strip().upper().strip(".,;") for t in text.split() if t.strip()]
    if tokens and all(any(l.code == tok for l in AVAILABLE_LOCALES) for tok in tokens):
        _apply_locales_from_line(text)
        return

    # інакше – агентний чат (за замовчуванням)
    if agent_chat_mode and agent_session.enabled:
        log(text, "user")
        ok, answer = _agent_send(text)
        log(answer, "action" if ok else "error")
    elif not agent_chat_mode:
        log("Agent mode OFF. Увімкни через /agent-mode on або введи /help.", "error")
    else:
        log("Agent chat вимкнено. Увімкни через /agent-on або введи /help.", "error")


input_buffer = Buffer(multiline=False, accept_handler=_handle_input)


def get_input_prompt():
    if state.menu_level != MenuLevel.NONE:
        return [("class:input.menu", " MENU "), ("class:input.hint", " ↑↓ рух | Enter/Space дія | F2 меню ")]
    return [("class:input.prompt", " > ")]


def get_prompt_width() -> int:
    return 55 if state.menu_level != MenuLevel.NONE else 3


def get_status():
    if state.menu_level != MenuLevel.NONE:
        mode_indicator = [("class:status.menu", " MENU "), ("class:status", " ")]
    else:
        mode_indicator = [("class:status.chat", " INPUT "), ("class:status", " ")]

    monitor_tag = f"MON:{'ON' if state.monitor_active else 'OFF'}:{state.monitor_source}"

    return mode_indicator + [
        ("class:status.ready", f" {state.status} "),
        ("class:status", " "),
        ("class:status.key", monitor_tag),
        ("class:status", " | "),
        ("class:status.key", "F2: Menu"),
        ("class:status", " | "),
        ("class:status.key", "Ctrl+C: Quit"),
    ]


# ================== KEY BINDINGS ==================


def _get_cleanup_cfg() -> Any:
    global cleanup_cfg
    return cleanup_cfg


def _set_cleanup_cfg(cfg: Any) -> None:
    global cleanup_cfg
    cleanup_cfg = cfg


def _tool_app_command(args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = str(args.get("command") or "").strip()
    if not cmd.startswith("/"):
        return {"ok": False, "error": "command must start with '/'"}

    perms = _agent_last_permissions
    cmd_to_run = cmd
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_autopilot and "confirm_autopilot" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_AUTOPILOT"
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_shell and "confirm_shell" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_SHELL"
    if cmd_to_run.lower().startswith("/autopilot") and perms.allow_applescript and "confirm_applescript" not in cmd_to_run.lower():
        cmd_to_run = cmd_to_run + " CONFIRM_APPLESCRIPT"

    captured: List[Tuple[str, str]] = []
    original_log = globals().get("log")

    def _cap(text: str, category: str = "info") -> None:
        captured.append((category, str(text)))

    try:
        globals()["log"] = _cap
        _handle_command(cmd_to_run)
    finally:
        globals()["log"] = original_log

    return {"ok": True, "lines": captured[:200]}


def _tool_monitor_targets(args: Dict[str, Any]) -> Dict[str, Any]:
    action = str(args.get("action") or "status").strip().lower()
    key = str(args.get("key") or "").strip()
    if action in {"status", "list", "ls"}:
        return {"ok": True, "targets": sorted(state.monitor_targets)}
    if action == "add":
        if not key:
            return {"ok": False, "error": "Missing key"}
        state.monitor_targets.add(key)
        return {"ok": True, "targets": sorted(state.monitor_targets)}
    if action in {"remove", "rm"}:
        if not key:
            return {"ok": False, "error": "Missing key"}
        if key in state.monitor_targets:
            state.monitor_targets.remove(key)
        return {"ok": True, "targets": sorted(state.monitor_targets)}
    if action == "clear":
        state.monitor_targets = set()
        return {"ok": True, "targets": []}
    if action == "save":
        ok = _save_monitor_targets()
        return {"ok": ok, "targets": sorted(state.monitor_targets)}
    return {"ok": False, "error": "Unknown action"}


def _tool_llm_status() -> Dict[str, Any]:
    _load_env()
    _load_llm_settings()
    return {
        "ok": True,
        "provider": str(os.getenv("LLM_PROVIDER") or "copilot"),
        "main_model": str(os.getenv("COPILOT_MODEL") or ""),
        "vision_model": str(os.getenv("COPILOT_VISION_MODEL") or ""),
        "settings_path": LLM_SETTINGS_PATH,
    }


def _tool_llm_set(args: Dict[str, Any]) -> Dict[str, Any]:
    _load_env()
    _load_llm_settings()
    provider = str(args.get("provider") or os.getenv("LLM_PROVIDER") or "copilot").strip().lower() or "copilot"
    main_model = str(args.get("main_model") or os.getenv("COPILOT_MODEL") or "gpt-4o").strip() or "gpt-4o"
    vision_model = str(args.get("vision_model") or os.getenv("COPILOT_VISION_MODEL") or "gpt-4.1").strip() or "gpt-4.1"
    ok = _save_llm_settings(provider, main_model, vision_model)
    if ok:
        _reset_agent_llm()
    return {"ok": ok, "provider": provider, "main_model": main_model, "vision_model": vision_model}


def _tool_ui_theme_status() -> Dict[str, Any]:
    return {"ok": True, "theme": state.ui_theme, "settings_path": UI_SETTINGS_PATH}


def _tool_ui_theme_set(args: Dict[str, Any]) -> Dict[str, Any]:
    theme = str(args.get("theme") or "").strip().lower()
    if theme not in set(THEME_NAMES):
        return {"ok": False, "error": "Unknown theme"}
    state.ui_theme = theme
    ok = _save_ui_settings()
    return {"ok": ok, "theme": state.ui_theme}


# ================== CLI SUBCOMMANDS ==================

def cli_main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser(prog="cli.py", description="System CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("tui", help="Запустити TUI (за замовчуванням)")

    p_list = sub.add_parser("list-editors", help="Список редакторів")

    p_list_mod = sub.add_parser("list-modules", help="Список модулів")
    p_list_mod.add_argument("--editor", required=True)

    p_run = sub.add_parser("run", help="Запустити очищення")
    p_run.add_argument("--editor", required=True)
    p_run.add_argument("--dry-run", action="store_true")

    p_enable = sub.add_parser("enable", help="Увімкнути модуль")
    p_enable.add_argument("--editor", required=True)
    p_enable.add_argument("--id", required=True)

    p_disable = sub.add_parser("disable", help="Вимкнути модуль")
    p_disable.add_argument("--editor", required=True)
    p_disable.add_argument("--id", required=True)

    p_install = sub.add_parser("install", help="Нова установка")
    p_install.add_argument("--editor", required=True)

    p_smart = sub.add_parser("smart-plan", help="LLM smart-plan")
    p_smart.add_argument("--editor", required=True)
    p_smart.add_argument("--query", required=True)

    p_ask = sub.add_parser("ask", help="LLM ask")
    p_ask.add_argument("--question", required=True)

    p_agent_chat = sub.add_parser("agent-chat", help="Agent chat (single-shot)")
    p_agent_chat.add_argument("--message", required=True)

    sub.add_parser("agent-reset", help="Reset in-memory agent session")
    sub.add_parser("agent-on", help="Enable agent chat")
    sub.add_parser("agent-off", help="Disable agent chat")

    p_autopilot = sub.add_parser("autopilot", help="Autopilot: plan->act->observe loop (dangerous)")
    p_autopilot.add_argument("--task", required=True)
    p_autopilot.add_argument("--max-steps", type=int, default=30)
    p_autopilot.add_argument("--confirm-autopilot", action="store_true")
    p_autopilot.add_argument("--confirm-shell", action="store_true")
    p_autopilot.add_argument("--confirm-applescript", action="store_true")

    args = parser.parse_args(argv)

    if not args.command or args.command == "tui":
        run_tui()
        return

    cfg = _load_cleanup_config()

    if args.command == "list-editors":
        for key, label in _list_editors(cfg):
            print(f"{key}: {label}")
        return

    if args.command == "list-modules":
        meta = cfg.get("editors", {}).get(args.editor)
        if not meta:
            print(f"Unknown editor: {args.editor}")
            raise SystemExit(1)
        for m in meta.get("modules", []):
            mark = "ON" if m.get("enabled") else "OFF"
            print(f"[{mark}] {m.get('id')} - {m.get('name')} (script={m.get('script')})")
        return

    if args.command == "run":
        ok, msg = _run_cleanup(cfg, args.editor, dry_run=args.dry_run)
        print(msg)
        raise SystemExit(0 if ok else 1)

    if args.command in {"enable", "disable"}:
        ref = _find_module(cfg, args.editor, args.id)
        if not ref:
            print("Module not found")
            raise SystemExit(1)
        enabled = args.command == "enable"
        if _set_module_enabled(cfg, ref, enabled):
            print("OK")
            raise SystemExit(0)
        print("Failed")
        raise SystemExit(1)

    if args.command == "install":
        ok, msg = _perform_install(cfg, args.editor)
        print(msg)
        raise SystemExit(0 if ok else 1)

    if args.command == "smart-plan":
        ok, msg = _llm_smart_plan(cfg, args.editor, args.query)
        print(msg)
        raise SystemExit(0 if ok else 1)

    if args.command == "ask":
        ok, msg = _llm_ask(cfg, args.question)
        print(msg)
        raise SystemExit(0 if ok else 1)

    if args.command == "agent-reset":
        agent_session.reset()
        print("OK")
        return

    if args.command == "agent-on":
        agent_session.enabled = True
        print("OK")
        return

    if args.command == "agent-off":
        agent_session.enabled = False
        print("OK")
        return

    if args.command == "agent-chat":
        ok, answer = _agent_send(args.message)
        print(answer)
        raise SystemExit(0 if ok else 1)

    if args.command == "autopilot":
        _load_ui_settings()
        unsafe_mode = bool(getattr(state, "ui_unsafe_mode", False))

        if not unsafe_mode and not args.confirm_autopilot:
            print("Confirmation required: pass --confirm-autopilot (or enable Unsafe mode in TUI Settings)")
            raise SystemExit(1)
        try:
            from system_ai.autopilot.autopilot_agent import AutopilotAgent

            agent = AutopilotAgent(
                allow_autopilot=True,
                allow_shell=True if unsafe_mode else bool(args.confirm_shell),
                allow_applescript=True if unsafe_mode else bool(args.confirm_applescript),
            )
            for event in agent.run_task(args.task, max_steps=int(args.max_steps)):
                step = event.get("step")
                plan = event.get("plan")
                thought = getattr(plan, "thought", "") if plan else ""
                result_message = getattr(plan, "result_message", "") if plan else ""
                print(f"[AP] Step {step}: {thought}")
                if result_message:
                    print(f"[AP] {result_message}")
                if event.get("done"):
                    break
            raise SystemExit(0)
        except Exception as e:
            print(f"Autopilot error: {e}")
            raise SystemExit(1)


def main() -> None:
    cli_main(sys.argv[1:])


if __name__ == "__main__":
    main()
