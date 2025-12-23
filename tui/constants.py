from __future__ import annotations

from typing import List, Tuple

from tui.state import MenuLevel


MAIN_MENU_ITEMS: List[Tuple[str, MenuLevel]] = [
    ("menu.item.custom_tasks", MenuLevel.CUSTOM_TASKS),
    ("menu.item.run_cleanup", MenuLevel.CLEANUP_EDITORS),
    ("menu.item.modules", MenuLevel.MODULE_EDITORS),
    ("menu.item.install", MenuLevel.INSTALL_EDITORS),
    ("menu.item.monitoring", MenuLevel.MONITORING),
    ("menu.item.settings", MenuLevel.SETTINGS),
]


LOG_STYLE_MAP = {
    "info": "class:log.info",
    "user": "class:log.user",
    "action": "class:log.action",
    "error": "class:log.error",
    "tool_success": "class:log.tool.success",
    "tool_fail": "class:log.tool.fail",
    "tool_run": "class:log.tool.run",
    "debug": "class:log.debug",
    "warning": "class:log.warning",
    "critical": "class:log.error",
}
