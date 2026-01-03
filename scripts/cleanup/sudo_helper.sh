#!/bin/zsh
# Допоміжний скрипт для автоматичного введення sudo пароля
# Використовується через SUDO_ASKPASS

# Завантаження змінних з .env файлу
# Шукаємо корінь проекту (де лежить .env або main.py)
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$CURRENT_DIR"
while [ "$REPO_ROOT" != "/" ]; do
    if [ -f "$REPO_ROOT/.env" ] || [ -f "$REPO_ROOT/main.py" ]; then
        break
    fi
    REPO_ROOT="$(dirname "$REPO_ROOT")"
done
if [ "$REPO_ROOT" = "/" ]; then
    REPO_ROOT="$CURRENT_DIR"
fi
ENV_FILE="$REPO_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    # Читаємо SUDO_PASSWORD з .env
    SUDO_PASSWORD=$(grep '^SUDO_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    echo "$SUDO_PASSWORD"
else
    # Якщо .env не знайдено, використовуємо значення за замовчуванням
    echo ""
fi
