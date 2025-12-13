from __future__ import annotations

from typing import Any, Callable, List, Sequence, Tuple

from prompt_toolkit.key_binding import KeyBindings

from tui.themes import THEME_NAMES


def build_keybindings(
    *,
    state: Any,
    MenuLevel: Any,
    show_menu: Any,
    MAIN_MENU_ITEMS: Sequence[Tuple[str, Any]],
    get_custom_tasks_menu_items: Callable[[], List[Tuple[str, Any]]],
    TOP_LANGS: Sequence[str],
    lang_name: Callable[[str], str],
    log: Callable[[str, str], None],
    # persistence / side-effects
    save_ui_settings: Callable[[], Any],
    reset_agent_llm: Callable[[], Any],
    save_monitor_settings: Callable[[], Any],
    save_monitor_targets: Callable[[], Any],
    # menu helpers
    get_monitoring_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_settings_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_llm_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_agent_menu_items: Callable[[], List[Tuple[str, Any]]],
    get_editors_list: Callable[[], List[Tuple[str, str]]],
    # cleanup/module operations
    get_cleanup_cfg: Callable[[], Any],
    set_cleanup_cfg: Callable[[Any], None],
    load_cleanup_config: Callable[[], Any],
    run_cleanup: Callable[[Any, str, bool], Tuple[bool, str]],
    perform_install: Callable[[Any, str], Tuple[bool, str]],
    find_module: Callable[[Any, str, str], Any],
    set_module_enabled: Callable[[Any, Any, bool], bool],
    # locales
    AVAILABLE_LOCALES: Sequence[Any],
    localization: Any,
    # monitoring targets
    get_monitor_menu_items: Callable[[], List[Any]],
    normalize_menu_index: Callable[[List[Any]], None],
    monitor_stop_selected: Callable[[], Tuple[bool, str]],
    monitor_start_selected: Callable[[], Tuple[bool, str]],
    monitor_resolve_watch_items: Callable[[Any], Any],
    monitor_service: Any,
    fs_usage_service: Any,
    opensnoop_service: Any,
) -> KeyBindings:
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        event.app.exit()

    @kb.add("f2")
    def _(event):
        if state.menu_level == MenuLevel.NONE:
            state.menu_level = MenuLevel.MAIN
            state.menu_index = 0
        else:
            state.menu_level = MenuLevel.NONE
            state.menu_index = 0

    @kb.add("escape")
    @kb.add("q")
    def _(event):
        if state.menu_level == MenuLevel.MAIN:
            state.menu_level = MenuLevel.NONE
            state.menu_index = 0
        elif state.menu_level in {
            MenuLevel.CUSTOM_TASKS,
            MenuLevel.CLEANUP_EDITORS,
            MenuLevel.MODULE_EDITORS,
            MenuLevel.MODULE_LIST,
            MenuLevel.INSTALL_EDITORS,
            MenuLevel.LOCALES,
            MenuLevel.MONITORING,
            MenuLevel.MONITOR_TARGETS,
            MenuLevel.MONITOR_CONTROL,
            MenuLevel.SETTINGS,
            MenuLevel.UNSAFE_MODE,
            MenuLevel.LLM_SETTINGS,
            MenuLevel.AGENT_SETTINGS,
            MenuLevel.APPEARANCE,
            MenuLevel.LANGUAGE,
        }:
            state.menu_level = MenuLevel.MAIN
            state.menu_index = 0

    @kb.add("up", filter=show_menu)
    def _(event):
        state.menu_index = max(0, state.menu_index - 1)
        if state.menu_level == MenuLevel.MONITOR_TARGETS:
            items = get_monitor_menu_items()
            normalize_menu_index(items)

    @kb.add("down", filter=show_menu)
    def _(event):
        max_idx = 0
        if state.menu_level == MenuLevel.MAIN:
            max_idx = len(MAIN_MENU_ITEMS) - 1
        elif state.menu_level == MenuLevel.CUSTOM_TASKS:
            max_idx = max(0, len(get_custom_tasks_menu_items()) - 1)
        elif state.menu_level == MenuLevel.MONITORING:
            max_idx = max(0, len(get_monitoring_menu_items()) - 1)
        elif state.menu_level in {MenuLevel.CLEANUP_EDITORS, MenuLevel.MODULE_EDITORS, MenuLevel.INSTALL_EDITORS}:
            max_idx = max(0, len(get_editors_list()) - 1)
        elif state.menu_level == MenuLevel.MODULE_LIST:
            cfg = get_cleanup_cfg() or {}
            mods = cfg.get("editors", {}).get(state.selected_editor or "", {}).get("modules", [])
            max_idx = max(0, len(mods) - 1)
        elif state.menu_level == MenuLevel.LOCALES:
            max_idx = len(AVAILABLE_LOCALES) - 1
        elif state.menu_level == MenuLevel.SETTINGS:
            max_idx = max(0, len(get_settings_menu_items()) - 1)
        elif state.menu_level == MenuLevel.UNSAFE_MODE:
            max_idx = 0
        elif state.menu_level == MenuLevel.MONITOR_TARGETS:
            max_idx = max(0, len(get_monitor_menu_items()) - 1)
        elif state.menu_level == MenuLevel.MONITOR_CONTROL:
            max_idx = 0
        elif state.menu_level == MenuLevel.LLM_SETTINGS:
            max_idx = max(0, len(get_llm_menu_items()) - 1)
        elif state.menu_level == MenuLevel.AGENT_SETTINGS:
            max_idx = max(0, len(get_agent_menu_items()) - 1)
        elif state.menu_level == MenuLevel.APPEARANCE:
            max_idx = max(0, len(THEME_NAMES) - 1)
        elif state.menu_level == MenuLevel.LANGUAGE:
            max_idx = 1

        state.menu_index = min(max_idx, state.menu_index + 1)

        if state.menu_level == MenuLevel.MONITOR_TARGETS:
            items = get_monitor_menu_items()
            normalize_menu_index(items)

    @kb.add("d", filter=show_menu)
    def _(event):
        if state.menu_level != MenuLevel.CLEANUP_EDITORS:
            return

        editors = get_editors_list()
        if not editors:
            return
        key = editors[state.menu_index][0]
        state.selected_editor = key
        ok, msg = run_cleanup(load_cleanup_config(), key, True)
        log(msg, "action" if ok else "error")

    @kb.add("space", filter=show_menu)
    def _(event):
        if state.menu_level == MenuLevel.MODULE_LIST:
            editor = state.selected_editor
            if not editor:
                return
            cfg = get_cleanup_cfg() or {}
            meta = cfg.get("editors", {}).get(editor, {})
            mods = meta.get("modules", [])
            if not mods:
                return
            m = mods[state.menu_index]
            mid = m.get("id")
            if not mid:
                return
            ref = find_module(cfg, editor, str(mid))
            if not ref:
                return
            new_state = not bool(m.get("enabled"))
            if set_module_enabled(cfg, ref, new_state):
                set_cleanup_cfg(load_cleanup_config())
                log(f"{editor}/{mid}: {'ON' if new_state else 'OFF'}", "action")
            else:
                log("Не вдалося змінити модуль.", "error")

        elif state.menu_level == MenuLevel.LOCALES:
            loc = AVAILABLE_LOCALES[state.menu_index]
            if loc.code == localization.primary:
                log("Не можна вимкнути primary локаль.", "error")
                return
            if loc.code in localization.selected:
                localization.selected = [c for c in localization.selected if c != loc.code]
                log(f"Вимкнено: {loc.code}", "action")
            else:
                localization.selected.append(loc.code)
                log(f"Увімкнено: {loc.code}", "action")
            localization.save()

        elif state.menu_level == MenuLevel.MONITOR_TARGETS:
            items = get_monitor_menu_items()
            if not items:
                return
            normalize_menu_index(items)
            it = items[state.menu_index]
            if not getattr(it, "selectable", False):
                return
            if it.key in state.monitor_targets:
                state.monitor_targets.remove(it.key)
                log(f"Monitor: OFF {it.label}", "action")
            else:
                state.monitor_targets.add(it.key)
                log(f"Monitor: ON {it.label}", "action")

    @kb.add("s", filter=show_menu)
    def _(event):
        if state.menu_level != MenuLevel.MONITOR_CONTROL:
            return
        if state.monitor_active:
            log("Stop monitoring before changing source.", "error")
            return
        order = ["watchdog", "fs_usage", "opensnoop"]
        cur = state.monitor_source if state.monitor_source in order else "watchdog"
        idx = order.index(cur)
        state.monitor_source = order[(idx + 1) % len(order)]
        save_monitor_settings()
        log(f"Monitoring source: {state.monitor_source}", "action")

    @kb.add("u", filter=show_menu)
    def _(event):
        if state.menu_level != MenuLevel.MONITOR_CONTROL:
            return
        if state.monitor_active:
            log("Stop monitoring before changing sudo setting.", "error")
            return
        state.monitor_use_sudo = not state.monitor_use_sudo
        save_monitor_settings()
        log(f"Monitoring sudo: {'ON' if state.monitor_use_sudo else 'OFF'}", "action")

    @kb.add("enter", filter=show_menu)
    def _(event):
        if state.menu_level == MenuLevel.MAIN:
            _, lvl = MAIN_MENU_ITEMS[state.menu_index]
            state.menu_level = lvl
            state.menu_index = 0
            return

        if state.menu_level == MenuLevel.CUSTOM_TASKS:
            items = get_custom_tasks_menu_items()
            if not items:
                return
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            _label, action = items[state.menu_index]
            try:
                ok, msg = action()
                log(msg, "action" if ok else "error")
            except Exception as e:
                log(f"Custom task failed: {e}", "error")
            return

        if state.menu_level == MenuLevel.MONITORING:
            items = get_monitoring_menu_items()
            if not items:
                return
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            _, lvl = items[state.menu_index]
            state.menu_level = lvl
            state.menu_index = 0
            return

        if state.menu_level == MenuLevel.SETTINGS:
            items = get_settings_menu_items()
            if not items:
                return
            state.menu_index = max(0, min(state.menu_index, len(items) - 1))
            _, lvl = items[state.menu_index]
            state.menu_level = lvl
            state.menu_index = 0
            return

        if state.menu_level == MenuLevel.UNSAFE_MODE:
            state.ui_unsafe_mode = not bool(getattr(state, "ui_unsafe_mode", False))
            save_ui_settings()
            log(f"Unsafe mode: {'ON' if state.ui_unsafe_mode else 'OFF'}", "action")
            return

        if state.menu_level == MenuLevel.APPEARANCE:
            themes = list(THEME_NAMES)
            state.menu_index = max(0, min(state.menu_index, len(themes) - 1))
            state.ui_theme = themes[state.menu_index]
            save_ui_settings()
            log(f"Theme set: {state.ui_theme}", "action")
            return

        if state.menu_level == MenuLevel.LANGUAGE:
            langs = list(TOP_LANGS)
            if not langs:
                return
            state.menu_index = max(0, min(state.menu_index, 1))
            if state.menu_index == 0:
                cur = state.ui_lang if state.ui_lang in langs else langs[0]
                state.ui_lang = langs[(langs.index(cur) + 1) % len(langs)]
                save_ui_settings()
                log(f"UI language set: {state.ui_lang} ({lang_name(state.ui_lang)})", "action")
                return

            cur = state.chat_lang if state.chat_lang in langs else langs[0]
            state.chat_lang = langs[(langs.index(cur) + 1) % len(langs)]
            save_ui_settings()
            reset_agent_llm()
            log(f"Chat language set: {state.chat_lang} ({lang_name(state.chat_lang)})", "action")
            return

        if state.menu_level == MenuLevel.CLEANUP_EDITORS:
            editors = get_editors_list()
            if not editors:
                return
            key = editors[state.menu_index][0]
            state.selected_editor = key
            ok, msg = run_cleanup(load_cleanup_config(), key, False)
            log(msg, "action" if ok else "error")
            return

        if state.menu_level == MenuLevel.MODULE_EDITORS:
            editors = get_editors_list()
            if not editors:
                return
            key = editors[state.menu_index][0]
            state.selected_editor = key
            set_cleanup_cfg(load_cleanup_config())
            state.menu_level = MenuLevel.MODULE_LIST
            state.menu_index = 0
            return

        if state.menu_level == MenuLevel.INSTALL_EDITORS:
            editors = get_editors_list()
            if not editors:
                return
            key = editors[state.menu_index][0]
            state.selected_editor = key
            ok, msg = perform_install(load_cleanup_config(), key)
            log(msg, "action" if ok else "error")
            return

        if state.menu_level == MenuLevel.LOCALES:
            loc = AVAILABLE_LOCALES[state.menu_index]
            localization.primary = loc.code
            if loc.code not in localization.selected:
                localization.selected.insert(0, loc.code)
            else:
                localization.selected = [loc.code] + [c for c in localization.selected if c != loc.code]
            localization.save()
            log(f"Primary встановлено: {loc.code}", "action")
            return

        if state.menu_level == MenuLevel.MONITOR_TARGETS:
            if save_monitor_targets():
                log(f"Saved monitor targets: {', '.join(sorted(state.monitor_targets)) or '(none)'}", "action")
            else:
                log("Failed to save monitor targets.", "error")
            state.menu_level = MenuLevel.MAIN
            state.menu_index = 0
            return

        if state.menu_level == MenuLevel.MONITOR_CONTROL:
            if state.monitor_active:
                ok, msg = monitor_stop_selected()
                state.monitor_active = bool(monitor_service.running or fs_usage_service.running or opensnoop_service.running)
                log(msg, "action" if ok else "error")
                return

            if not state.monitor_targets:
                log("Monitoring: обери цілі у 'Monitoring Targets' (потрібні хрестики) і натисни Save.", "error")
                return

            watch_items = monitor_resolve_watch_items(state.monitor_targets)
            if state.monitor_source == "watchdog" and not watch_items:
                log("Monitoring: не вдалося знайти локальні директорії для вибраних цілей.", "error")
                return

            ok, msg = monitor_start_selected()
            state.monitor_active = bool(monitor_service.running or fs_usage_service.running or opensnoop_service.running)
            log(msg, "action" if ok else "error")
            return

    return kb
