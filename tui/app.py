from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class TuiRuntime:
    app: Any
    log: Callable[[str, str], None]
    load_monitor_targets: Callable[[], None]
    load_monitor_settings: Callable[[], None]
    load_ui_settings: Callable[[], None]
    load_env: Callable[[], None]
    load_llm_settings: Callable[[], None]
    apply_default_monitor_targets: Callable[[], None]


def run_tui(runtime: TuiRuntime) -> None:
    runtime.log("SYSTEM CLI запущено. Натисніть F2 для меню. Команди: /help", "info")
    runtime.load_monitor_targets()
    runtime.load_monitor_settings()
    runtime.load_ui_settings()
    runtime.load_env()
    runtime.load_llm_settings()
    runtime.apply_default_monitor_targets()
    runtime.app.run()
