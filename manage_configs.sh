#!/bin/zsh

# Windsurf Configuration Manager
# Управління профілями ідентифікаторів

CONFIGS_DIR="$(dirname "$0")/configs"
ORIGINAL_CONFIG="$CONFIGS_DIR/original"
CURRENT_WINDSURF_DIR=~/Library/Application\ Support/Windsurf
LOG_FILE="$CONFIGS_DIR/audit.log"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║       🔧 WINDSURF CONFIGURATION MANAGER                       ║"
echo "║       Управління профілями ідентифікаторів                    ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Створити директорії якщо не існують
mkdir -p "$CONFIGS_DIR"

# Функція логування
log_action() {
    local action="$1"
    local profile="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $action: $profile" >> "$LOG_FILE"
}

# Функція для збереження поточної конфігурації
save_current_config() {
    local config_name="$1"
    local config_path="$CONFIGS_DIR/$config_name"
    
    mkdir -p "$config_path"
    
    echo "💾 Збереження конфігурації: $config_name"
    
    # Зберегти Machine-ID
    if [ -f "$CURRENT_WINDSURF_DIR/machineid" ]; then
        cp "$CURRENT_WINDSURF_DIR/machineid" "$config_path/machineid"
        echo "  ✓ Machine-ID збережено"
    fi
    
    # Зберегти Storage
    if [ -f "$CURRENT_WINDSURF_DIR/storage.json" ]; then
        cp "$CURRENT_WINDSURF_DIR/storage.json" "$config_path/storage.json"
        echo "  ✓ Storage збережено"
    fi
    
    # Зберегти Global Storage
    if [ -f "$CURRENT_WINDSURF_DIR/User/globalStorage/storage.json" ]; then
        mkdir -p "$config_path/User/globalStorage"
        cp "$CURRENT_WINDSURF_DIR/User/globalStorage/storage.json" "$config_path/User/globalStorage/storage.json"
        echo "  ✓ Global Storage збережено"
    fi
    
    # Зберегти hostname
    scutil --get HostName > "$config_path/hostname.txt" 2>/dev/null || echo "DEVs-Mac-Studio" > "$config_path/hostname.txt"
    echo "  ✓ Hostname збережено: $(cat "$config_path/hostname.txt")"
    
    # Зберегти метадані
    cat > "$config_path/metadata.json" << EOF
{
  "name": "$config_name",
  "created": "$(date +%Y-%m-%d\ %H:%M:%S)",
  "hostname": "$(cat "$config_path/hostname.txt")",
  "description": "Windsurf profile configuration"
}
EOF
    
    echo "✅ Конфігурація '$config_name' успішно збережена в: $config_path"
}

# Функція для відновлення конфігурації
restore_config() {
    local config_name="$1"
    local config_path="$CONFIGS_DIR/$config_name"
    
    if [ ! -d "$config_path" ]; then
        echo "❌ Конфігурація '$config_name' не знайдена!"
        return 1
    fi
    
    echo "🔄 Відновлення конфігурації: $config_name"
    
    # Створити директорії якщо не існують
    mkdir -p "$CURRENT_WINDSURF_DIR"
    mkdir -p "$CURRENT_WINDSURF_DIR/User/globalStorage"
    
    # Відновити Machine-ID
    if [ -f "$config_path/machineid" ]; then
        cp "$config_path/machineid" "$CURRENT_WINDSURF_DIR/machineid"
        echo "  ✓ Machine-ID відновлено"
    fi
    
    # Відновити Storage
    if [ -f "$config_path/storage.json" ]; then
        cp "$config_path/storage.json" "$CURRENT_WINDSURF_DIR/storage.json"
        echo "  ✓ Storage відновлено"
    fi
    
    # Відновити Global Storage
    if [ -f "$config_path/User/globalStorage/storage.json" ]; then
        cp "$config_path/User/globalStorage/storage.json" "$CURRENT_WINDSURF_DIR/User/globalStorage/storage.json"
        echo "  ✓ Global Storage відновлено"
    fi
    
    # Відновити hostname
    if [ -f "$config_path/hostname.txt" ]; then
        local saved_hostname=$(cat "$config_path/hostname.txt")
        echo "  🔄 Відновлення hostname: $saved_hostname"
        sudo scutil --set HostName "$saved_hostname"
        sudo scutil --set LocalHostName "$saved_hostname"
        sudo scutil --set ComputerName "$saved_hostname"
        sudo dscacheutil -flushcache
        sudo killall -HUP mDNSResponder
        echo "  ✓ Hostname відновлено"
    fi
    
    echo "✅ Конфігурація '$config_name' успішно відновлена!"
}

# Функція для виведення списку конфігурацій
list_configs() {
    echo "📋 Доступні конфігурації:"
    echo ""
    
    if [ ! -d "$CONFIGS_DIR" ] || [ -z "$(ls -A "$CONFIGS_DIR" 2>/dev/null | grep -v '.gitkeep\|README.md')" ]; then
        echo "  (немає збережених конфігурацій)"
        return
    fi
    
    local count=1
    for config_dir in "$CONFIGS_DIR"/*; do
        if [ -d "$config_dir" ]; then
            local config_name=$(basename "$config_dir")
            
            # Пропустити .gitkeep та README
            if [[ "$config_name" == ".gitkeep" ]] || [[ "$config_name" == "README.md" ]]; then
                continue
            fi
            
            echo "  [$count] $config_name"
            
            # Показати метадані якщо є
            if [ -f "$config_dir/metadata.json" ]; then
                local created=$(cat "$config_dir/metadata.json" | grep "created" | cut -d'"' -f4)
                local hostname=$(cat "$config_dir/metadata.json" | grep "hostname" | cut -d'"' -f4)
                echo "      📅 Створено: $created"
                echo "      🖥️  Hostname: $hostname"
            fi
            
            # Показати що збережено
            [ -f "$config_dir/machineid" ] && echo "      ✓ Machine-ID"
            [ -f "$config_dir/storage.json" ] && echo "      ✓ Storage"
            [ -f "$config_dir/User/globalStorage/storage.json" ] && echo "      ✓ Global Storage"
            
            echo ""
            ((count++))
        fi
    done
}

# Функція для видалення конфігурації
delete_config() {
    local config_name="$1"
    local config_path="$CONFIGS_DIR/$config_name"
    
    if [ ! -d "$config_path" ]; then
        echo "❌ Конфігурація '$config_name' не знайдена!"
        return 1
    fi
    
    if [[ "$config_name" == "original" ]]; then
        echo "⚠️  УВАГА! Ви намагаєтесь видалити ОРИГІНАЛЬНУ конфігурацію!"
        echo -n "Ви впевнені? (yes/no): "
        read confirm
        if [[ "$confirm" != "yes" ]]; then
            echo "❌ Видалення скасовано"
            return 1
        fi
    fi
    
    rm -rf "$config_path"
    echo "✅ Конфігурація '$config_name' видалена"
}

# Головне меню
show_menu() {
    echo "Оберіть дію:"
    echo ""
    echo "  1️⃣  Зберегти поточну конфігурацію"
    echo "  2️⃣  Відновити конфігурацію"
    echo "  3️⃣  Список конфігурацій"
    echo "  4️⃣  Видалити конфігурацію"
    echo "  5️⃣  Зберегти як ОРИГІНАЛ (для автовідновлення)"
    echo "  0️⃣  Вихід"
    echo ""
    echo -n "Ваш вибір [0-5]: "
}

# Основний цикл
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            echo ""
            echo "💾 Збереження поточної конфігурації"
            echo -n "Введіть назву конфігурації (наприклад: profile1, client2, test): "
            read config_name
            
            if [ -z "$config_name" ]; then
                echo "❌ Назва не може бути порожньою!"
            elif [[ "$config_name" =~ [^a-zA-Z0-9_-] ]]; then
                echo "❌ Використовуйте тільки літери, цифри, - та _"
            else
                save_current_config "$config_name"
            fi
            echo ""
            ;;
            
        2)
            echo ""
            list_configs
            echo -n "Введіть назву конфігурації для відновлення: "
            read config_name
            
            if [ -n "$config_name" ]; then
                restore_config "$config_name"
            fi
            echo ""
            ;;
            
        3)
            echo ""
            list_configs
            echo ""
            ;;
            
        4)
            echo ""
            list_configs
            echo -n "Введіть назву конфігурації для видалення: "
            read config_name
            
            if [ -n "$config_name" ]; then
                delete_config "$config_name"
            fi
            echo ""
            ;;
            
        5)
            echo ""
            echo "💎 Збереження як ОРИГІНАЛ"
            echo "Ця конфігурація буде використовуватись для автовідновлення через 5 годин"
            echo -n "Продовжити? (y/n): "
            read confirm
            
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                save_current_config "original"
            else
                echo "❌ Скасовано"
            fi
            echo ""
            ;;
            
        0)
            echo ""
            echo "👋 До побачення!"
            exit 0
            ;;
            
        *)
            echo ""
            echo "❌ Невірний вибір!"
            echo ""
            ;;
    esac
done
