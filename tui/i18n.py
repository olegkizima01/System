from __future__ import annotations

from typing import Dict, Optional

DEFAULT_LANG = "en"

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "uk": "Українська",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pl": "Polski",
    "pt": "Português",
    "tr": "Türkçe",
    "ru": "Русский",
}

TOP_LANGS = ["en", "uk", "de", "fr", "es", "it", "pl", "pt", "tr", "ru"]

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "menu.main.title": "MAIN MENU (Enter: Select, Q/Esc: Close)",
        "menu.custom_tasks.title": "CUSTOM TASKS (Enter: Run, Q/Esc: Back)",
        "menu.item.custom_tasks": "Custom Tasks",
        "menu.custom.section.recorder": "[Recorder]",
        "menu.custom.section.recordings": "[Recordings]",
        "menu.custom.section.automations": "[Automations]",
        "menu.custom.recorder_start": "Recorder: Start (5s)",
        "menu.custom.recorder_stop": "Recorder: Stop",
        "menu.custom.recorder_open_last": "Recorder: Open last session",
        "menu.custom.recording_analyze_last": "Recorder: Analyze last session",
        "menu.custom.automation_run_last": "Automation: Run from last recording",
        "menu.custom.automation_permissions": "Automation: Permissions help",
        "menu.custom.windsurf_register": "Windsurf Registration",
        "menu.monitoring.title": "MONITORING (Enter: Open, Q/Esc: Back)",
        "menu.settings.title": "SETTINGS (Enter: Open, Q/Esc: Back)",
        "menu.settings.section.appearance": "Appearance & Behavior",
        "menu.settings.appearance": "Theme",
        "menu.settings.layout": "Layout & Panels",
        "menu.settings.language": "Language",
        "menu.settings.locales": "Locales (Region)",
        "menu.settings.section.agent": "Agent & LLM",
        "menu.settings.llm": "LLM Provider",
        "menu.settings.agent": "Agent Settings",
        "menu.settings.section.automation": "Automation & Permissions",
        "menu.settings.automation_permissions": "Automation Permissions",
        "menu.settings.mcp_settings": "MCP Client Settings",
        "menu.settings.section.experimental": "Experimental",
        "menu.settings.unsafe_mode": "Unsafe Mode",
        "menu.settings.self_healing": "Self-Healing (Auto-repair)",
        "menu.self_healing.title": "SELF-HEALING (Enter: Toggle, Q/Esc: Back)",
        "menu.settings.memory_manager": "Memory Manager",
        "menu.memory_manager.title": "MEMORY MANAGER (Enter: Select, Q/Esc: Back)",
        "menu.self_healing.label": "Self-Healing",
        "menu.settings.section.dev": "Development",
        "menu.settings.dev_code_provider": "Code Provider (Dev Mode)",
        "menu.settings.dev": "Development",
        "menu.dev_settings.title": "DEV CODE PROVIDER (Enter: Toggle, Q/Esc: Back)",
        "menu.dev_settings.provider_label": "Provider",
        "menu.dev_settings.vibe_enabled": "Doctor Vibe: Enabled",
        "menu.dev_settings.auto_apply": "Auto-Apply Vibe Edits",
        "menu.dev_settings.auto_resume": "Auto-Resume after Vibe",
        "menu.automation_permissions.title": "AUTOMATION PERMISSIONS (Enter: Toggle, Q/Esc: Back)",
        "menu.monitoring.targets": "Targets",
        "menu.monitoring.start_stop": "Start/Stop",
        "menu.monitor.mode_hint": "Enter on Mode: Toggle auto/manual",
        "menu.appearance.title": "APPEARANCE (Enter: Select Theme, Q/Esc: Back)",
        "menu.language.title": "LANGUAGE (Enter: Change, Q/Esc: Back)",
        "menu.llm.title": "LLM SETTINGS (Enter: Change, Q/Esc: Back)",
        "menu.agent.title": "AGENT SETTINGS (Enter: Toggle/Run, Q/Esc: Back)",
        "menu.locales.title": "LOCALES (Space: ON/OFF, Enter: Primary, Q/Esc: Back)",
        "menu.unsafe_mode.title": "UNSAFE MODE (Enter: Toggle, Q/Esc: Back)",
        "menu.unsafe_mode.label": "Unsafe Mode",
        "menu.layout.title": "LAYOUT (Enter: Select, Left/Right: Adjust, Q/Esc: Back)",
        "menu.layout.left_panel_ratio": "Left Panel Width",
        "menu.layout.hint": "Use Left/Right arrow keys to adjust the ratio.",
        "menu.cleanup.title": "RUN CLEANUP (Enter: Run, D: Dry-run, Q/Esc: Back)",
        "menu.modules.title": "MODULES: CHOOSE EDITOR (Enter: Select, Q/Esc: Back)",
        "menu.install.title": "INSTALL (Enter: Open installer, Q/Esc: Back)",
        "menu.item.run_cleanup": "Run Cleanup",
        "menu.item.modules": "Modules",
        "menu.item.install": "Install",
        "menu.item.monitoring": "Monitoring",
        "menu.item.settings": "Settings",
        "menu.item.eternal_engine": "🔥 Eternal Engine",
        "menu.item.localization": "Localization",
        "menu.back": "Back",
        "prompt.default": " > ",
        "prompt.paused": " (PAUSED) > ",
        "prompt.confirm_shell": " (CONFIRM SHELL) > ",
        "prompt.confirm_applescript": " (CONFIRM APPLESCRIPT) > ",
        "prompt.confirm_gui": " (CONFIRM GUI) > ",
        "prompt.confirm_run": " (CONFIRM RUN) > ",
    },
    "uk": {
        "menu.main.title": "ГОЛОВНЕ МЕНЮ (Enter: Вибір, Q/Esc: Закрити)",
        "menu.custom_tasks.title": "КАСТОМНІ ЗАВДАННЯ (Enter: Запуск, Q/Esc: Назад)",
        "menu.item.custom_tasks": "Кастомні завдання",
        "menu.custom.section.recorder": "[Recorder]",
        "menu.custom.section.recordings": "[Записи]",
        "menu.custom.section.automations": "[Автоматизації]",
        "menu.custom.recorder_start": "Recorder: Старт (5s)",
        "menu.custom.recorder_stop": "Recorder: Стоп",
        "menu.custom.recorder_open_last": "Recorder: Відкрити останню сесію",
        "menu.custom.recording_analyze_last": "Recorder: Аналізувати останню сесію",
        "menu.custom.automation_run_last": "Автоматизація: Запустити з останнього запису",
        "menu.custom.automation_permissions": "Автоматизація: Дозволи (довідка)",
        "menu.custom.windsurf_register": "Реєстрація Windsurf",
        "menu.monitoring.title": "МОНІТОРИНГ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.settings.title": "НАЛАШТУВАННЯ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.settings.section.appearance": "Зовнішній вигляд & Поведінка",
        "menu.settings.appearance": "Тема",
        "menu.settings.layout": "Розмітка & Панелі",
        "menu.settings.language": "Мова",
        "menu.settings.locales": "Локалі (Регіон)",
        "menu.settings.section.agent": "Агент & LLM",
        "menu.settings.llm": "LLM Провайдер",
        "menu.settings.agent": "Налаштування агента",
        "menu.settings.section.automation": "Автоматизація & Дозволи",
        "menu.settings.automation_permissions": "Дозволи автоматизації",
        "menu.settings.mcp_settings": "Налаштування MCP Клієнта",
        "menu.settings.section.experimental": "Експериментальні",
        "menu.settings.unsafe_mode": "Unsafe Mode",
        "menu.settings.self_healing": "Самолікування (Auto-repair)",
        "menu.self_healing.title": "САМОЛІКУВАННЯ (Enter: Перемкнути, Q/Esc: Назад)",
        "menu.settings.memory_manager": "Менеджер пам'яті",
        "menu.memory_manager.title": "МЕНЕДЖЕР ПАМ'ЯТІ (Enter: Вибір, Q/Esc: Назад)",
        "menu.self_healing.label": "Самолікування",
        "menu.settings.section.dev": "Розробка",
        "menu.settings.dev_code_provider": "Код провайдер (Dev Mode)",
        "menu.settings.dev": "Розробка",
        "menu.dev_settings.title": "DEV КОД ПРОВАЙДЕР (Enter: Перемкнути, Q/Esc: Назад)",
        "menu.dev_settings.provider_label": "Провайдер",
        "menu.dev_settings.vibe_enabled": "Doctor Vibe: Увімкнено",
        "menu.dev_settings.auto_apply": "Авто-застосування змін Doctor Vibe",
        "menu.dev_settings.auto_resume": "Автоматичне продовження після Vibe",
        "menu.automation_permissions.title": "ДОЗВОЛИ АВТОМАТИЗАЦІЇ (Enter: Перемкнути, Q/Esc: Назад)",
        "menu.monitoring.targets": "Цілі",
        "menu.monitoring.start_stop": "Старт/Стоп",
        "menu.monitor.mode_hint": "Натисніть Enter на Режим: Перемкнути авто/ручний",
        "menu.appearance.title": "ТЕМА (Enter: Вибрати, Q/Esc: Назад)",
        "menu.language.title": "МОВА (Enter: Змінити, Q/Esc: Назад)",
        "menu.llm.title": "LLM НАЛАШТУВАННЯ (Enter: Змінити, Q/Esc: Назад)",
        "menu.agent.title": "НАЛАШТУВАННЯ АГЕНТА (Enter: Перемкнути/Виконати, Q/Esc: Назад)",
        "menu.locales.title": "ЛОКАЛІ (Space: ON/OFF, Enter: Primary, Q/Esc: Назад)",
        "menu.unsafe_mode.title": "UNSAFE MODE (Enter: Перемкнути, Q/Esc: Назад)",
        "menu.unsafe_mode.label": "Небезпечний режим",
        "menu.layout.title": "РОЗМІТКА (Enter: Вибір, Стрілки: Регулювання, Q/Esc: Назад)",
        "menu.layout.left_panel_ratio": "Ширина лівої панелі",
        "menu.layout.hint": "Використовуйте стрілки Вліво/Вправо для налаштування.",
        "menu.cleanup.title": "ОЧИСТКА (Enter: Запуск, D: Dry-run, Q/Esc: Назад)",
        "menu.modules.title": "МОДУЛІ: ВИБІР РЕДАКТОРА (Enter: Вибір, Q/Esc: Назад)",
        "menu.install.title": "ВСТАНОВЛЕННЯ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.item.run_cleanup": "Очистка",
        "menu.item.modules": "Модулі",
        "menu.item.install": "Встановити",
        "menu.item.monitoring": "Моніторинг",
        "menu.item.settings": "Налаштування",
        "menu.item.eternal_engine": "🔥 Eternal Engine",
        "menu.item.localization": "Локалізація",
        "menu.back": "Назад",
        "prompt.default": " > ",
        "prompt.paused": " (ПАУЗА) > ",
        "prompt.confirm_shell": " (CONFIRM SHELL) > ",
        "prompt.confirm_applescript": " (CONFIRM APPLESCRIPT) > ",
        "prompt.confirm_gui": " (CONFIRM GUI) > ",
        "prompt.confirm_run": " (CONFIRM RUN) > ",
    },
}


def tr(key: str, lang: Optional[str] = None, *, fallback_lang: str = DEFAULT_LANG) -> str:
    """Translate a key into the specified or current UI language."""
    from tui.state import state
    k = str(key)
    l = (lang or getattr(state, "ui_lang", None) or "").strip().lower() or fallback_lang
    if l in TRANSLATIONS and k in TRANSLATIONS[l]:
        return TRANSLATIONS[l][k]
    if fallback_lang in TRANSLATIONS and k in TRANSLATIONS[fallback_lang]:
        return TRANSLATIONS[fallback_lang][k]
    return k
from tui.cli_localization import AVAILABLE_LOCALES, LocalizationConfig  # noqa: F401
localization = LocalizationConfig.load()


def lang_name(code: str) -> str:
    c = (code or "").strip().lower()
    if not c:
        return "(auto)"
    return LANGUAGE_NAMES.get(c, c.upper())


def normalize_lang(code: Optional[str]) -> str:
    c = (code or "").strip().lower()
    if not c:
        return DEFAULT_LANG
    return c
