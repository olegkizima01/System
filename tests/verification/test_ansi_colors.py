#!/usr/bin/env python3

import re

# Тестові рядки з ANSI-кольорами
test_lines = [
    "\x1b[0;34m[1/11]\x1b[0m Очищення основних директорій...",
    "\x1b[0;32m✓\x1b[0m Основні директорії очищено",
    "\x1b[0;36mℹ\x1b[0m Знайдено Antigravity.dmg, виконуємо очищення...",
    "\x1b[0;33m⚠\x1b[0m Не вдалося створити записуваний образ",
    "\x1b[0;31m✗\x1b[0m Помилка",
]

# Регулярний вираз для видалення ANSI-кольорів
pattern = r'\x1b\[[0-9;]*m'

print("Testing ANSI color removal:")
for line in test_lines:
    clean_line = re.sub(pattern, '', line)
    print(f"Original: {repr(line)}")
    print(f"Cleaned:  {repr(clean_line)}")
    print()
