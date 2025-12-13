#!/bin/zsh
# Допоміжний скрипт для автоматичного введення sudo пароля
# Використовується через SUDO_ASKPASS

# Завантаження змінних з .env файлу
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    # Читаємо SUDO_PASSWORD з .env
    SUDO_PASSWORD=$(grep '^SUDO_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    echo "$SUDO_PASSWORD"
else
    # Якщо .env не знайдено, використовуємо значення за замовчуванням
    echo "Qwas@000"
fi
