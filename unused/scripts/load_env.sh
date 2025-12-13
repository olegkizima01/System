#!/bin/zsh
# Функція для завантаження змінних середовища з .env файлу

load_env() {
    local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    local ENV_FILE="$SCRIPT_DIR/.env"
    
    # Якщо .env не існує, створюємо з .env.example
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            echo "⚙️  Створюю .env з .env.example..."
            cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
            echo "✅ Файл .env створено. Будь ласка, налаштуйте свій пароль у .env"
        else
            echo "⚠️  Файл .env не знайдено. Використовую значення за замовчуванням."
            return 1
        fi
    fi
    
    # Завантажуємо змінні з .env
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
        return 0
    fi
    
    return 1
}

# Функція для налаштування SUDO_ASKPASS
setup_sudo_askpass() {
    local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    export SUDO_ASKPASS="$SCRIPT_DIR/sudo_helper.sh"
    
    # Перевірка чи файл існує та виконуваний
    if [ ! -x "$SUDO_ASKPASS" ]; then
        chmod +x "$SUDO_ASKPASS" 2>/dev/null
    fi
}

# Експортуємо функції для використання в інших скриптах
export -f load_env
export -f setup_sudo_askpass
