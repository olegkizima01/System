from __future__ import annotations

from typing import Any, Callable, List, Sequence, Tuple

from prompt_toolkit.filters import Condition


def build_menu(
    *,
    state: Any,
    MenuLevel: Any,
    tr: Callable[[str, str], str],
    lang_name: Callable[[str], str],
    MAIN_MENU_ITEMS: Sequence[Tuple[str, Any]],
    get_custom_tasks_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_monitoring_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_settings_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_llm_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_agent_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_editors_list: Callable[[], List[Tuple[str, str]]],
    get_cleanup_cfg: Callable[[], Any],
    AVAILABLE_LOCALES: Sequence[Any],
    localization: Any,
    get_monitor_menu_items: Callable[[], List[Any]],
    normalize_menu_index: Callable[[List[Any]], None],
    MONITOR_TARGETS_PATH: str,
    MONITOR_EVENTS_DB_PATH: str,
    CLEANUP_CONFIG_PATH: str,
    LOCALIZATION_CONFIG_PATH: str,
) -> Tuple[Condition, Callable[[], List[Tuple[str, str]]]]:
    @Condition
    def show_menu() -> bool:
        return state.menu_level != MenuLevel.NONE

    def get_menu_content() -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = []

        if state.menu_level == MenuLevel.MAIN:
            result.append(("class:menu.title", f" {tr('menu.main.title', state.ui_lang)}\n\n"))
            for i, (name, _) in enumerate(MAIN_MENU_ITEMS):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{tr(name, state.ui_lang)}\n"))
            return result

        if state.menu_level == MenuLevel.CUSTOM_TASKS:
            result.append(("class:menu.title", f" {tr('menu.custom_tasks.title', state.ui_lang)}\n\n"))
            items = get_custom_tasks_menu_items()
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{tr(label, state.ui_lang)}\n"))
            return result

        if state.menu_level == MenuLevel.MONITORING:
            result.append(("class:menu.title", f" {tr('menu.monitoring.title', state.ui_lang)}\n\n"))
            items = get_monitoring_menu_items()
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{tr(label, state.ui_lang)}\n"))
            return result

        if state.menu_level == MenuLevel.SETTINGS:
            result.append(("class:menu.title", f" {tr('menu.settings.title', state.ui_lang)}\n\n"))
            items = get_settings_menu_items()
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{tr(label, state.ui_lang)}\n"))
            return result

        if state.menu_level == MenuLevel.LLM_SETTINGS:
            result.append(("class:menu.title", f" {tr('menu.llm.title', state.ui_lang)}\n\n"))
            items = get_llm_menu_items()
            if not items:
                result.append(("class:menu.item", " (no items)\n"))
                return result
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{label}\n"))
            return result

        if state.menu_level == MenuLevel.AGENT_SETTINGS:
            result.append(("class:menu.title", f" {tr('menu.agent.title', state.ui_lang)}\n\n"))
            items = get_agent_menu_items()
            if not items:
                result.append(("class:menu.item", " (no items)\n"))
                return result
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{label}\n"))
            return result

        if state.menu_level == MenuLevel.APPEARANCE:
            result.append(("class:menu.title", f" {tr('menu.appearance.title', state.ui_lang)}\n\n"))
            themes = ["monaco", "dracula", "nord", "gruvbox"]
            state.menu_index = max(0, min(state.menu_index, len(themes) - 1))
            for i, t in enumerate(themes):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                mark = "[*]" if state.ui_theme == t else "[ ]"
                result.append((style_cls, f"{prefix}{mark} {t}\n"))
            return result

        if state.menu_level == MenuLevel.LANGUAGE:
            result.append(("class:menu.title", f" {tr('menu.language.title', state.ui_lang)}\n\n"))
            ui = f"UI: {state.ui_lang} - {lang_name(state.ui_lang)}"
            chat = f"Chat: {state.chat_lang} - {lang_name(state.chat_lang)}"
            items = [(ui, "ui"), (chat, "chat")]
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            for i, (label, _k) in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{label}\n"))
            result.append(("class:menu.item", "\n Enter: cycle | /lang set ui|chat <code>\n"))
            return result

        if state.menu_level == MenuLevel.UNSAFE_MODE:
            result.append(("class:menu.title", f" {tr('menu.unsafe_mode.title', state.ui_lang)}\n\n"))
            on = bool(getattr(state, "ui_unsafe_mode", False))
            toggle_style = "class:toggle.on" if on else "class:toggle.off"
            mark = "ON" if on else "OFF"
            result.append(("class:menu.selected", " > Unsafe mode ["))
            result.append((toggle_style, f"{mark}"))
            result.append(("class:menu.selected", "]\n"))
            return result

        if state.menu_level == MenuLevel.MONITOR_CONTROL:
            result.append(("class:menu.title", " MONITORING (Enter: Start/Stop, S: Source, U: Sudo, Q/Esc: Back)\n"))
            state_line = "ACTIVE" if state.monitor_active else "INACTIVE"
            result.append(("class:menu.item", f" State: {state_line}\n"))
            result.append(("class:menu.item", f" Source: {state.monitor_source}\n"))
            if state.monitor_source in {"fs_usage", "opensnoop"}:
                sudo_line = "ON" if state.monitor_use_sudo else "OFF"
                result.append(("class:menu.item", f" Sudo: {sudo_line}\n"))
            result.append(("class:menu.item", f" Targets: {len(state.monitor_targets)} selected\n"))
            result.append(("class:menu.item", f" DB: {MONITOR_EVENTS_DB_PATH}\n\n"))
            action = "STOP" if state.monitor_active else "START"
            result.append(("class:menu.selected", f" > {action}\n"))
            if state.monitor_source == "watchdog":
                result.append(("class:menu.item", "\n Note: watchdog monitors directories (no process attribution).\n"))
            elif state.monitor_source == "fs_usage":
                result.append(("class:menu.item", "\n Note: fs_usage attributes calls to process name; may require sudo.\n"))
            elif state.monitor_source == "opensnoop":
                result.append(("class:menu.item", "\n Note: opensnoop traces open() calls; may require sudo.\n"))
            else:
                result.append(("class:menu.item", "\n Note: source not implemented yet.\n"))
            return result

        if state.menu_level == MenuLevel.MONITOR_TARGETS:
            result.append(("class:menu.title", " MONITORING TARGETS (Space: Toggle, Enter: Save, Q/Esc: Back)\n"))
            result.append(("class:menu.item", f" Config: {MONITOR_TARGETS_PATH}\n\n"))

            items = get_monitor_menu_items()
            normalize_menu_index(items)

            for i, it in enumerate(items):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"

                if not getattr(it, "selectable", False):
                    result.append(("class:menu.title", f"\n {it.label}\n"))
                    continue

                on = it.key in state.monitor_targets
                mark = "[x]" if on else "[ ]"
                origin = f" ({it.origin})" if getattr(it, "origin", "") else ""
                result.append((style_cls, f"{prefix}{mark} {it.label}{origin}\n"))
            return result

        if state.menu_level == MenuLevel.CLEANUP_EDITORS:
            result.append(("class:menu.title", " RUN CLEANUP (Enter: Run, D: Dry-run, Q/Esc: Back)\n\n"))
            editors = get_editors_list()
            for i, (key, label) in enumerate(editors):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{key} - {label}\n"))
            return result

        if state.menu_level == MenuLevel.MODULE_EDITORS:
            result.append(("class:menu.title", " MODULES: CHOOSE EDITOR (Enter: Select, Q/Esc: Back)\n\n"))
            editors = get_editors_list()
            for i, (key, label) in enumerate(editors):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{key} - {label}\n"))
            return result

        if state.menu_level == MenuLevel.MODULE_LIST:
            editor = state.selected_editor
            if not editor:
                result.append(("class:menu.title", " MODULES (no editor selected)\n"))
                return result

            cfg = get_cleanup_cfg() or {}
            meta = cfg.get("editors", {}).get(editor, {})
            result.append(("class:menu.title", f" MODULES: {editor} (Space: Toggle, Q/Esc: Back)\n\n"))
            mods = meta.get("modules", [])
            if not mods:
                result.append(("class:menu.item", " (немає модулів – використайте /smart або /ask)\n"))
                return result

            for i, m in enumerate(mods):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                on = bool(m.get("enabled"))
                toggle_style = "class:toggle.on" if on else "class:toggle.off"
                mark = "ON" if on else "OFF"
                result.append((style_cls, f"{prefix}{m.get('id')} - {m.get('name')} ["))
                result.append((toggle_style, f"{mark}"))
                result.append((style_cls, "]\n"))
            return result

        if state.menu_level == MenuLevel.INSTALL_EDITORS:
            result.append(("class:menu.title", " INSTALL (Enter: Open installer, Q/Esc: Back)\n\n"))
            editors = get_editors_list()
            for i, (key, label) in enumerate(editors):
                prefix = " > " if i == state.menu_index else "   "
                style_cls = "class:menu.selected" if i == state.menu_index else "class:menu.item"
                result.append((style_cls, f"{prefix}{key} - {label}\n"))
            return result

        if state.menu_level == MenuLevel.LOCALES:
            result.append(("class:menu.title", f" {tr('menu.locales.title', state.ui_lang)}\n\n"))
            for idx, loc in enumerate(AVAILABLE_LOCALES):
                prefix = " > " if idx == state.menu_index else "   "
                style_cls = "class:menu.selected" if idx == state.menu_index else "class:menu.item"

                is_selected = loc.code in localization.selected
                is_primary = loc.code == localization.primary

                primary_mark = "●" if is_primary else " "
                active_mark = "●" if is_selected else " "

                result.append(
                    (
                        style_cls,
                        f"{prefix}[P:{primary_mark}] [A:{active_mark}] {loc.code} - {loc.name} ({loc.group})\n",
                    )
                )
            return result

        result.append(("class:menu.item", "(menu)"))
        return result

    return show_menu, get_menu_content
