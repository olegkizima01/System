from __future__ import annotations

from typing import Any, Dict


DEFAULT_CLEANUP_CONFIG: Dict[str, Any] = {
    "editors": {
        "windsurf": {
            "label": "Windsurf",
            "install": {
                "type": "dmg",
                "pattern": "Windsurf*.dmg",
                "hint": "DMG буде відкрито через open, далі встановлення руками через Finder",
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
                "url": "https://antigravity.example.com/download",
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
            "modules": [],
        },
    }
}
