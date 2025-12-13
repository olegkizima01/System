from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from tui.cli_paths import LOCALIZATION_CONFIG_PATH


@dataclass
class Locale:
    code: str
    name: str
    group: str


AVAILABLE_LOCALES: List[Locale] = [
    Locale("UA", "Україна", "Україна"),
    Locale("EU", "Європейський Союз", "ЄС"),
    Locale("DE", "Німеччина", "ЄС"),
    Locale("FR", "Франція", "ЄС"),
    Locale("IT", "Італія", "ЄС"),
    Locale("ES", "Іспанія", "ЄС"),
    Locale("PL", "Польща", "ЄС"),
    Locale("NL", "Нідерланди", "ЄС"),
    Locale("RU", "Росія", "Близьке зарубіжжя"),
    Locale("BY", "Білорусь", "Близьке зарубіжжя"),
    Locale("KZ", "Казахстан", "Близьке зарубіжжя"),
    Locale("MD", "Молдова", "Близьке зарубіжжя"),
    Locale("GE", "Грузія", "Близьке зарубіжжя"),
    Locale("AM", "Вірменія", "Близьке зарубіжжя"),
    Locale("AZ", "Азербайджан", "Близьке зарубіжжя"),
    Locale("US", "США", "Північна Америка"),
    Locale("CA", "Канада", "Північна Америка"),
]


@dataclass
class LocalizationConfig:
    primary: str = "UA"
    selected: List[str] = field(default_factory=lambda: ["UA", "EU", "US", "CA"])

    def to_dict(self) -> Dict[str, Any]:
        return {"primary": self.primary, "selected": self.selected}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LocalizationConfig":
        primary = str(d.get("primary", "UA"))
        selected = list(d.get("selected", ["UA"]))
        if primary not in selected:
            selected = [primary] + [c for c in selected if c != primary]
        return cls(primary=primary, selected=selected)

    def save(self) -> None:
        os.makedirs(os.path.dirname(LOCALIZATION_CONFIG_PATH), exist_ok=True)
        with open(LOCALIZATION_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls) -> "LocalizationConfig":
        if not os.path.exists(LOCALIZATION_CONFIG_PATH):
            return cls()
        try:
            with open(LOCALIZATION_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return cls()
