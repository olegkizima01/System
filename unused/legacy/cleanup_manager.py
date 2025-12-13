#!/usr/bin/env python3
"""
Cleanup Manager: розумний багаторежимний інтерфейс керування очищенням
для редакторів Windsurf / VS Code / Antigravity / Cursor з підтримкою
модулів та LLM-планувальника (Copilot provider).

Викликається з cli.sh, але може працювати й напряму:

  python3 cleanup_manager.py                 # інтерактивне меню
  python3 cleanup_manager.py list-editors
  python3 cleanup_manager.py list-modules --editor windsurf
  python3 cleanup_manager.py run --editor windsurf
  python3 cleanup_manager.py enable-module --editor windsurf --id deep_windsurf
  python3 cleanup_manager.py smart-plan --editor cursor
  python3 cleanup_manager.py chat
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "cleanup_modules.json")

# Імпорт LLM-провайдера
try:
    from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
    from providers.copilot import CopilotLLM  # type: ignore
except Exception:  # Якщо немає langchain/провайдера, LLM-функції будуть відключені
    CopilotLLM = None  # type: ignore
    SystemMessage = HumanMessage = None  # type: ignore


# ================== КОНФІГ ЗА ЗАМОВЧУВАННЯМ ==================
DEFAULT_CONFIG: Dict[str, Any] = {
    "editors": {
        "windsurf": {
            "label": "Windsurf",
            "install": {
                "type": "dmg",
                "pattern": "Windsurf*.dmg",
                "hint": "DMG буде відкрито через open, далі встановлення руками через Finder"
            },
            "modules": [
                {
                    "id": "deep_windsurf",
                    "name": "Deep Windsurf Cleanup",
                    "script": "./deep_windsurf_cleanup.sh",
                    "enabled": True,
                    "description": "Глибоке очищення Windsurf (кеші, дані, профілі)",
                },
                {
                    "id": "advanced_windsurf",
                    "name": "Advanced Windsurf Identifier Cleanup",
                    "script": "./advanced_windsurf_cleanup.sh",
                    "enabled": True,
                    "description": "Розширене очищення ідентифікаторів / трекінгу Windsurf",
                },
                {
                    "id": "windsurf_identifier_cleanup",
                    "name": "Windsurf Identifier Quick Cleanup",
                    "script": "./windsurf_identifier_cleanup.sh",
                    "enabled": False,
                    "description": "Швидке точкове очищення ідентифікаторів",
                },
                {
                    "id": "deep_vscode_for_windsurf",
                    "name": "Deep VS Code Cleanup (Side Effects)",
                    "script": "./deep_vscode_cleanup.sh",
                    "enabled": False,
                    "description": "Очищення VS Code, якщо він використовувався разом із Windsurf",
                },
                {
                    "id": "stealth_cleanup",
                    "name": "Stealth System Traces Cleanup",
                    "script": "./stealth_cleanup.sh",
                    "enabled": False,
                    "description": "Агресивне видалення системних слідів (ризиковий модуль)",
                },
                {
                    "id": "hardware_spoof",
                    "name": "Hardware Fingerprint Spoofing",
                    "script": "./hardware_spoof.sh",
                    "enabled": False,
                    "description": "Маніпуляції з hardware fingerprint (потребує sudo)",
                },
                {
                    "id": "check_identifier_cleanup",
                    "name": "Identifier Cleanup Verification",
                    "script": "./check_identifier_cleanup.sh",
                    "enabled": True,
                    "description": "Фінальна перевірка якості очистки",
                },
            ],
        },
        "vscode": {
            "label": "VS Code / VS Code OSS",
            "install": {
                "type": "zip",
                "pattern": "*VSCode*.zip",
                "hint": "ZIP буде відкрито через open або розпакування у поточну директорію",
            },
            "modules": [
                {
                    "id": "deep_vscode",
                    "name": "Deep VS Code Cleanup",
                    "script": "./deep_vscode_cleanup.sh",
                    "enabled": True,
                    "description": "Глибоке очищення VS Code (кеші, профілі, налаштування)",
                },
                {
                    "id": "vscode_identifier_cleanup",
                    "name": "VS Code Identifier Cleanup",
                    "script": "./vscode_identifier_cleanup.sh",
                    "enabled": False,
                    "description": "Очищення ідентифікаторів / прив'язок VS Code",
                },
                {
                    "id": "vscode_stealth_cleanup",
                    "name": "VS Code Stealth Cleanup",
                    "script": "./vscode_stealth_cleanup.sh",
                    "enabled": False,
                    "description": "Stealth-очищення, коли потрібен мінімальний слід",
                },
                {
                    "id": "check_vscode_backup",
                    "name": "VS Code Backup Status",
                    "script": "./check_vscode_backup.sh",
                    "enabled": False,
                    "description": "Перевірка бекапів VS Code",
                },
            ],
        },
        "antigravity": {
            "label": "Antigravity Editor",
            "install": {
                "type": "url",
                "url": "https://antigravity.example.com/download",  # placeholder
                "hint": "Відкриється сторінка завантаження Antigravity у браузері",
            },
            "modules": [
                {
                    "id": "antigravity_basic",
                    "name": "Antigravity Basic Cleanup",
                    "script": "./antigraviti_cleanup.sh",
                    "enabled": True,
                    "description": "Базове очищення Antigravity Editor",
                },
                {
                    "id": "antigravity_advanced",
                    "name": "Antigravity Advanced Cleanup",
                    "script": "./advanced_antigraviti_cleanup.sh",
                    "enabled": True,
                    "description": "Розширене очищення ідентифікаторів Antigravity",
                },
                {
                    "id": "antigravity_deep_vscode",
                    "name": "Deep VS Code Cleanup (Side Effects)",
                    "script": "./deep_vscode_cleanup.sh",
                    "enabled": False,
                    "description": "VS Code cleanup якщо Antigravity працював поверх VS Code",
                },
            ],
        },
        "cursor": {
            "label": "Cursor IDE",
            "install": {
                "type": "url",
                "url": "https://www.cursor.com/download",
                "hint": "Відкриється офіційна сторінка завантаження Cursor",
            },
            "modules": [
                # За замовчуванням порожній список – планується заповнення через LLM
            ],
        },
    }
}


@dataclass
class ModuleRef:
    editor: str
    module_id: str


def load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(os.path.join(SCRIPT_DIR, ".env"))


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()

    # Легка нормалізація: гарантуємо, що всі редактори з DEFAULT_CONFIG присутні
    base = DEFAULT_CONFIG["editors"]
    data.setdefault("editors", {})
    for key, val in base.items():
        if key not in data["editors"]:
            data["editors"][key] = val
        else:
            # Гарантуємо поле label / install / modules
            for field in ["label", "install", "modules"]:
                if field not in data["editors"][key]:
                    data["editors"][key][field] = val[field]
    return data


def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def list_editors(cfg: Dict[str, Any]) -> None:
    print("Доступні редактори:")
    for key, meta in cfg.get("editors", {}).items():
        print(f"  - {key}: {meta.get('label', key)}")


def list_modules(cfg: Dict[str, Any], editor: str) -> None:
    editors = cfg.get("editors", {})
    if editor not in editors:
        print(f"❌ Невідомий редактор: {editor}")
        return
    meta = editors[editor]
    print(f"Модулі очищення для {meta.get('label', editor)}:")
    modules = meta.get("modules", [])
    if not modules:
        print("  (модулі ще не налаштовані – використайте smart-plan або chat)")
        return
    for m in modules:
        status = "ON " if m.get("enabled") else "OFF"
        print(f"  [{status}] {m.get('id')} - {m.get('name')}")
        desc = m.get("description")
        if desc:
            print(f"       {desc}")
        script = m.get("script")
        if script:
            print(f"       script: {script}")


def find_module(cfg: Dict[str, Any], editor: str, module_id: str) -> ModuleRef | None:
    editors = cfg.get("editors", {})
    if editor not in editors:
        return None
    for m in editors[editor].get("modules", []):
        if m.get("id") == module_id:
            return ModuleRef(editor=editor, module_id=module_id)
    return None


def set_module_enabled(cfg: Dict[str, Any], ref: ModuleRef, enabled: bool) -> bool:
    editors = cfg.get("editors", {})
    editor_cfg = editors.get(ref.editor)
    if not editor_cfg:
        return False
    changed = False
    for m in editor_cfg.get("modules", []):
        if m.get("id") == ref.module_id:
            m["enabled"] = enabled
            changed = True
            break
    if changed:
        save_config(cfg)
    return changed


def run_script(script_path: str) -> int:
    full = script_path
    if not os.path.isabs(full):
        full = os.path.join(SCRIPT_DIR, script_path)
    if not os.path.exists(full):
        print(f"⚠️  Скрипт не знайдено: {full}")
        return 1
    try:
        subprocess.run(["chmod", "+x", full], check=False)
        proc = subprocess.run([full], cwd=SCRIPT_DIR)
        return proc.returncode
    except Exception as e:
        print(f"❌ Помилка запуску {full}: {e}")
        return 1


def run_cleanup(cfg: Dict[str, Any], editor: str, dry_run: bool = False) -> None:
    editors = cfg.get("editors", {})
    if editor not in editors:
        print(f"❌ Невідомий редактор: {editor}")
        return
    meta = editors[editor]
    label = meta.get("label", editor)
    modules: List[Dict[str, Any]] = meta.get("modules", [])
    active = [m for m in modules if m.get("enabled")]

    if not active:
        print(f"⚠️  Для {label} немає увімкнених модулів. Налаштуйте їх через 'modules' або 'smart-plan'.")
        return

    print(f"🚀 Запуск очищення для {label} ({editor})")
    print("Модулі у цьому прогоні:")
    for m in active:
        print(f"  - {m.get('id')} : {m.get('name')}")

    if dry_run:
        print("\n[DRY-RUN] Скрипти не будуть реально виконані – тільки список.")
        return

    for m in active:
        script = m.get("script")
        if not script:
            continue
        print(f"\n▶ Модуль: {m.get('name')} ({m.get('id')})")
        code = run_script(script)
        if code == 0:
            print("   ✅ Успішно")
        else:
            print(f"   ⚠️ Завершено з кодом {code}")

    print("\n✅ Цикл очищення завершено.")


def perform_install(cfg: Dict[str, Any], editor: str) -> None:
    editors = cfg.get("editors", {})
    if editor not in editors:
        print(f"❌ Невідомий редактор: {editor}")
        return
    install = editors[editor].get("install", {})
    label = editors[editor].get("label", editor)
    itype = install.get("type")

    print(f"🧩 Нова установка для {label} ({editor})")

    if itype == "dmg":
        pattern = install.get("pattern", "*.dmg")
        candidates = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(".dmg") and fnmatch_fn(f, pattern)]
        if not candidates:
            print(f"⚠️  DMG-файлів за шаблоном '{pattern}' у {SCRIPT_DIR} не знайдено.")
            return
        dmg = sorted(candidates)[-1]
        full = os.path.join(SCRIPT_DIR, dmg)
        print(f"Відкриваю {full} через 'open' – далі встановлення через стандартний майстер.")
        subprocess.run(["open", full])
    elif itype == "zip":
        pattern = install.get("pattern", "*.zip")
        candidates = [f for f in os.listdir(SCRIPT_DIR) if f.endswith(".zip") and fnmatch_fn(f, pattern)]
        if not candidates:
            print(f"⚠️  ZIP-файлів за шаблоном '{pattern}' у {SCRIPT_DIR} не знайдено.")
            return
        z = sorted(candidates)[-1]
        full = os.path.join(SCRIPT_DIR, z)
        print(f"Відкриваю {full} через 'open' – далі встановлення/розпакування вручну.")
        subprocess.run(["open", full])
    elif itype == "url":
        url = install.get("url")
        if not url:
            print("⚠️  URL для завантаження не налаштовано.")
            return
        print(f"Відкриваю сторінку завантаження у браузері: {url}")
        subprocess.run(["open", url])
    else:
        print("⚠️  Для цього редактора не налаштовано режим установки.")

    hint = install.get("hint")
    if hint:
        print(f"\nПідказка: {hint}")


def fnmatch_fn(name: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(name, pattern)


# ================== LLM: SMART PLAN / CHAT ==================

def ensure_llm_available() -> bool:
    if CopilotLLM is None or SystemMessage is None or HumanMessage is None:
        print("⚠️  LLM-провайдер недоступний (нема langchain_core або providers/copilot).")
        return False
    return True


def llm_smart_plan(cfg: Dict[str, Any], editor: str, user_query: str) -> None:
    if not ensure_llm_available():
        return

    load_env()

    editors = cfg.get("editors", {})
    if editor not in editors:
        print(f"❌ Невідомий редактор: {editor}")
        return

    llm = CopilotLLM()

    system_prompt = (
        "Ти System Cleanup Planner для редакторів коду (Windsurf, VS Code, Antigravity, Cursor).\n"
        "Отримуєш поточну JSON-конфігурацію модулів очищення і запит користувача.\n"
        "ТВОЄ ЗАВДАННЯ: запропонувати, які модулі увімкнути/вимкнути та які нові модулі потрібно створити.\n\n"
        "Обов'язково відповідай СТРОГО у форматі JSON без пояснень поза JSON:\n"
        "{\n"
        "  \"modules_to_enable\": [{\"editor\": \"windsurf\", \"id\": \"deep_windsurf\"}, ...],\n"
        "  \"modules_to_disable\": [{\"editor\": \"windsurf\", \"id\": \"advanced_windsurf\"}, ...],\n"
        "  \"modules_to_add\": [\n"
        "    {\n"
        "      \"editor\": \"cursor\",\n"
        "      \"id\": \"cursor_deep_cleanup\",\n"
        "      \"name\": \"Cursor Deep Cleanup\",\n"
        "      \"script\": \"./cursor_deep_cleanup.sh\",\n"
        "      \"description\": \"що саме робить цей модуль\",\n"
        "      \"enabled\": true\n"
        "    }\n"
        "  ],\n"
        "  \"notes\": \"короткі нотатки українською для користувача\"\n"
        "}\n"
        "Не додавай Markdown, лише чистий JSON."
    )

    payload = {
        "target_editor": editor,
        "current_config": cfg,
        "user_query": user_query,
    }

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)),
    ]

    print("🧠 Викликаю LLM-планувальник... (Copilot)")
    resp = llm.invoke(messages)
    content = getattr(resp, "content", "")

    try:
        plan = json.loads(content)
    except Exception as e:
        print("⚠️  Не вдалося розпарсити відповідь LLM як JSON.")
        print("Сира відповідь:")
        print(content)
        print(f"Помилка: {e}")
        return

    apply_llm_plan(cfg, plan)


def apply_llm_plan(cfg: Dict[str, Any], plan: Dict[str, Any]) -> None:
    editors = cfg.get("editors", {})

    enabled = plan.get("modules_to_enable", []) or []
    disabled = plan.get("modules_to_disable", []) or []
    added = plan.get("modules_to_add", []) or []

    changed = False

    for item in enabled:
        e = item.get("editor")
        mid = item.get("id")
        if not e or not mid:
            continue
        ref = find_module(cfg, e, mid)
        if ref is None:
            continue
        if set_module_enabled(cfg, ref, True):
            print(f"✅ Увімкнено модуль {mid} для {e}")
            changed = True

    for item in disabled:
        e = item.get("editor")
        mid = item.get("id")
        if not e or not mid:
            continue
        ref = find_module(cfg, e, mid)
        if ref is None:
            continue
        if set_module_enabled(cfg, ref, False):
            print(f"✅ Вимкнено модуль {mid} для {e}")
            changed = True

    for item in added:
        e = item.get("editor")
        if not e or e not in editors:
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
        # Уникаємо дублів
        existing_ids = {m.get("id") for m in editors[e].get("modules", [])}
        if module["id"] in existing_ids:
            continue
        editors[e].setdefault("modules", []).append(module)
        print(f"➕ Додано новий модуль {module['id']} для {e} (script={module['script']})")
        changed = True

    if changed:
        save_config(cfg)
        print("\n💾 Конфігурацію оновлено та збережено у cleanup_modules.json")

    notes = plan.get("notes")
    if notes:
        print("\n📝 Нотатки від LLM:")
        print(notes)


def llm_chat(cfg: Dict[str, Any]) -> None:
    if not ensure_llm_available():
        return

    load_env()

    llm = CopilotLLM()
    system_prompt = (
        "Ти інтерактивний ассистент з очищення системи.\n"
        "Твоя спеціалізація – Windsurf, VS Code, Antigravity, Cursor.\n"
        "Ти знаєш, що в системі є JSON-файл cleanup_modules.json з модулями очищення.\n"
        "Допомагай аналізувати ситуацію, пропонувати стратегії і, коли потрібно,\n"
        "рекомендуй запуск 'smart-plan' з конкретним описом задачі.\n"
        "Відповідай стисло, українською."
    )

    print("🤖 Режим інтерактивного чату запущено. Введіть текст (або 'exit' для виходу).")
    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВихід з чату.")
            return
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            print("Вихід з чату.")
            return

        payload = {
            "cleanup_config": cfg,
            "question": user,
        }
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)),
        ]
        resp = llm.invoke(messages)
        content = getattr(resp, "content", "")
        print(f"assistant> {content}\n")


# ================== ІНТЕРАКТИВНЕ МЕНЮ ==================

def interactive_menu() -> None:
    cfg = load_config()
    while True:
        print("""
╔══════════════════════════════════════════════╗
║      CLEANUP MANAGER - SMART CLI INTERFACE   ║
╠══════════════════════════════════════════════╣
║ 1) Список редакторів                         ║
║ 2) Список модулів для редактора              ║
║ 3) Запустити очищення (активні модулі)       ║
║ 4) Увімкнути/вимкнути модуль                 ║
║ 5) Нова установка редактора                  ║
║ 6) Smart-plan (LLM для редактора)           ║
║ 7) Інтерактивний LLM-чат                     ║
║ 0) Вихід                                     ║
╚══════════════════════════════════════════════╝
""")
        choice = input("➤ Ваш вибір: ").strip()
        if choice == "1":
            list_editors(cfg)
        elif choice == "2":
            editor = input("Редактор (windsurf/vscode/antigravity/cursor): ").strip()
            list_modules(cfg, editor)
        elif choice == "3":
            editor = input("Редактор для очищення: ").strip()
            dry = input("Dry-run (y/n)? ").strip().lower() == "y"
            run_cleanup(cfg, editor, dry_run=dry)
        elif choice == "4":
            editor = input("Редактор: ").strip()
            module_id = input("ID модуля: ").strip()
            state = input("Увімкнути? (y/n): ").strip().lower()
            ref = find_module(cfg, editor, module_id)
            if not ref:
                print("❌ Модуль не знайдено.")
            else:
                enabled = state == "y"
                if set_module_enabled(cfg, ref, enabled):
                    print("✅ Оновлено.")
                else:
                    print("⚠️ Не вдалося оновити статус модуля.")
        elif choice == "5":
            editor = input("Редактор для встановлення: ").strip()
            perform_install(cfg, editor)
        elif choice == "6":
            editor = input("Редактор для smart-plan: ").strip()
            desc = input("Коротко опишіть ціль очищення / стан системи: ").strip()
            llm_smart_plan(cfg, editor, desc)
            cfg = load_config()  # перезавантажити, якщо було оновлено
        elif choice == "7":
            llm_chat(cfg)
            cfg = load_config()
        elif choice == "0":
            print("👋 Вихід з Cleanup Manager.")
            return
        else:
            print("Невірний вибір.")


# ================== ВХІДНА ТОЧКА (CLI) ==================

def main(argv: List[str]) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup Manager - розумний інтерфейс очищення")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-editors", help="Показати доступні редактори")

    p_list = sub.add_parser("list-modules", help="Показати модулі для редактора")
    p_list.add_argument("--editor", required=True)

    p_run = sub.add_parser("run", help="Запустити очищення для редактора")
    p_run.add_argument("--editor", required=True)
    p_run.add_argument("--dry-run", action="store_true")

    p_enable = sub.add_parser("enable-module", help="Увімкнути модуль")
    p_enable.add_argument("--editor", required=True)
    p_enable.add_argument("--id", required=True)

    p_disable = sub.add_parser("disable-module", help="Вимкнути модуль")
    p_disable.add_argument("--editor", required=True)
    p_disable.add_argument("--id", required=True)

    p_install = sub.add_parser("install", help="Нова установка редактора")
    p_install.add_argument("--editor", required=True)

    p_smart = sub.add_parser("smart-plan", help="LLM-план для редактора")
    p_smart.add_argument("--editor", required=True)
    p_smart.add_argument("--query", required=False, help="Опис задачі")

    sub.add_parser("chat", help="Інтерактивний LLM-чат")

    args = parser.parse_args(argv)

    if not args.command:
        interactive_menu()
        return

    cfg = load_config()

    if args.command == "list-editors":
        list_editors(cfg)
    elif args.command == "list-modules":
        list_modules(cfg, args.editor)
    elif args.command == "run":
        run_cleanup(cfg, args.editor, dry_run=args.dry_run)
    elif args.command == "enable-module":
        ref = find_module(cfg, args.editor, args.id)
        if not ref:
            print("❌ Модуль не знайдено.")
            return
        if set_module_enabled(cfg, ref, True):
            print("✅ Модуль увімкнено.")
        else:
            print("⚠️ Не вдалося оновити модуль.")
    elif args.command == "disable-module":
        ref = find_module(cfg, args.editor, args.id)
        if not ref:
            print("❌ Модуль не знайдено.")
            return
        if set_module_enabled(cfg, ref, False):
            print("✅ Модуль вимкнено.")
        else:
            print("⚠️ Не вдалося оновити модуль.")
    elif args.command == "install":
        perform_install(cfg, args.editor)
    elif args.command == "smart-plan":
        q = args.query or input("Опишіть ціль очищення / стан системи: ")
        llm_smart_plan(cfg, args.editor, q)
    elif args.command == "chat":
        llm_chat(cfg)
    else:
        parser.print_help()


if __name__ == "__main__":
    main(sys.argv[1:])
