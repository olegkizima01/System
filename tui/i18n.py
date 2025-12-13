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
        "menu.monitoring.title": "MONITORING (Enter: Open, Q/Esc: Back)",
        "menu.settings.title": "SETTINGS (Enter: Open, Q/Esc: Back)",
        "menu.settings.llm": "LLM",
        "menu.settings.agent": "Agent",
        "menu.settings.appearance": "Appearance",
        "menu.settings.language": "Language",
        "menu.settings.locales": "Locales (Region)",
        "menu.monitoring.targets": "Targets",
        "menu.monitoring.start_stop": "Start/Stop",
        "menu.appearance.title": "APPEARANCE (Enter: Select Theme, Q/Esc: Back)",
        "menu.language.title": "LANGUAGE (Enter: Change, Q/Esc: Back)",
        "menu.llm.title": "LLM SETTINGS (Enter: Change, Q/Esc: Back)",
        "menu.agent.title": "AGENT SETTINGS (Enter: Toggle/Run, Q/Esc: Back)",
        "menu.locales.title": "LOCALES (Space: ON/OFF, Enter: Primary, Q/Esc: Back)",
        "menu.cleanup.title": "RUN CLEANUP (Enter: Run, D: Dry-run, Q/Esc: Back)",
        "menu.modules.title": "MODULES: CHOOSE EDITOR (Enter: Select, Q/Esc: Back)",
        "menu.install.title": "INSTALL (Enter: Open installer, Q/Esc: Back)",
        "menu.item.run_cleanup": "Run Cleanup",
        "menu.item.modules": "Modules",
        "menu.item.install": "Install",
        "menu.item.monitoring": "Monitoring",
        "menu.item.settings": "Settings",
        "menu.item.localization": "Localization",
    },
    "uk": {
        "menu.main.title": "ГОЛОВНЕ МЕНЮ (Enter: Вибір, Q/Esc: Закрити)",
        "menu.monitoring.title": "МОНІТОРИНГ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.settings.title": "НАЛАШТУВАННЯ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.settings.llm": "LLM",
        "menu.settings.agent": "Агент",
        "menu.settings.appearance": "Тема",
        "menu.settings.language": "Мова",
        "menu.settings.locales": "Локалі (Регіон)",
        "menu.monitoring.targets": "Цілі",
        "menu.monitoring.start_stop": "Старт/Стоп",
        "menu.appearance.title": "ТЕМА (Enter: Вибрати, Q/Esc: Назад)",
        "menu.language.title": "МОВА (Enter: Змінити, Q/Esc: Назад)",
        "menu.llm.title": "LLM НАЛАШТУВАННЯ (Enter: Змінити, Q/Esc: Назад)",
        "menu.agent.title": "НАЛАШТУВАННЯ АГЕНТА (Enter: Перемкнути/Виконати, Q/Esc: Назад)",
        "menu.locales.title": "ЛОКАЛІ (Space: ON/OFF, Enter: Primary, Q/Esc: Назад)",
        "menu.cleanup.title": "ОЧИСТКА (Enter: Запуск, D: Dry-run, Q/Esc: Назад)",
        "menu.modules.title": "МОДУЛІ: ВИБІР РЕДАКТОРА (Enter: Вибір, Q/Esc: Назад)",
        "menu.install.title": "ВСТАНОВЛЕННЯ (Enter: Відкрити, Q/Esc: Назад)",
        "menu.item.run_cleanup": "Очистка",
        "menu.item.modules": "Модулі",
        "menu.item.install": "Встановити",
        "menu.item.monitoring": "Моніторинг",
        "menu.item.settings": "Налаштування",
        "menu.item.localization": "Локалізація",
    },
}


def tr(key: str, lang: str, *, fallback_lang: str = DEFAULT_LANG) -> str:
    k = str(key)
    l = (lang or "").strip().lower() or fallback_lang
    if l in TRANSLATIONS and k in TRANSLATIONS[l]:
        return TRANSLATIONS[l][k]
    if fallback_lang in TRANSLATIONS and k in TRANSLATIONS[fallback_lang]:
        return TRANSLATIONS[fallback_lang][k]
    return k


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
