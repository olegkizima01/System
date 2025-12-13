#!/bin/zsh

echo "=================================================="
echo "🔧 УПРАВЛІННЯ КОНФІГУРАЦІЯМИ VS CODE"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs_vscode"

# Перевірка чи існує папка конфігурацій
if [ ! -d "$CONFIGS_DIR" ]; then
    echo "❌ Папка конфігурацій не знайдена: $CONFIGS_DIR"
    echo "💡 Спочатку запустіть: ./deep_vscode_cleanup.sh"
    exit 1
fi

# Функція для відображення списку конфігурацій
list_configs() {
    echo "\n📂 Доступні конфігурації:"
    local index=1
    for config_dir in "$CONFIGS_DIR"/*; do
        if [ -d "$config_dir" ]; then
            local config_name=$(basename "$config_dir")
            local hostname=""
            local created=""
            
            if [ -f "$config_dir/metadata.json" ]; then
                hostname=$(grep hostname "$config_dir/metadata.json" | cut -d'"' -f4)
                created=$(grep created "$config_dir/metadata.json" | cut -d'"' -f4)
            fi
            
            echo "  [$index] $config_name"
            [ -n "$hostname" ] && echo "      Hostname: $hostname"
            [ -n "$created" ] && echo "      Створено: $created"
            echo ""
            
            ((index++))
        fi
    done
}

# Функція для застосування конфігурації
apply_config() {
    local config_name=$1
    local config_path="$CONFIGS_DIR/$config_name"
    
    if [ ! -d "$config_path" ]; then
        echo "❌ Конфігурація не знайдена: $config_name"
        return 1
    fi
    
    echo "\n🔄 Застосування конфігурації: $config_name"
    
    # Відновлення Machine-ID
    if [ -f "$config_path/machineid" ]; then
        mkdir -p ~/Library/Application\ Support/Code
        cp "$config_path/machineid" ~/Library/Application\ Support/Code/machineid
        echo "✅ Machine-ID застосовано"
    fi
    
    # Відновлення Storage
    if [ -f "$config_path/storage.json" ]; then
        mkdir -p ~/Library/Application\ Support/Code
        cp "$config_path/storage.json" ~/Library/Application\ Support/Code/storage.json
        echo "✅ Storage застосовано"
    fi
    
    # Відновлення Global Storage
    if [ -f "$config_path/User/globalStorage/storage.json" ]; then
        mkdir -p ~/Library/Application\ Support/Code/User/globalStorage
        cp "$config_path/User/globalStorage/storage.json" ~/Library/Application\ Support/Code/User/globalStorage/storage.json
        echo "✅ Global Storage застосовано"
    fi
    
    # Відновлення Hostname
    if [ -f "$config_path/hostname.txt" ]; then
        local new_hostname=$(cat "$config_path/hostname.txt")
        echo "🔄 Зміна hostname на: $new_hostname"
        sudo scutil --set HostName "$new_hostname"
        sudo scutil --set LocalHostName "$new_hostname"
        sudo scutil --set ComputerName "$new_hostname"
        sudo dscacheutil -flushcache
        sudo killall -HUP mDNSResponder 2>/dev/null
        echo "✅ Hostname змінено"
    fi
    
    echo "\n✅ Конфігурацію застосовано!"
    echo "💡 Перезапустіть VS Code для застосування змін"
}

# Функція для видалення конфігурації
delete_config() {
    local config_name=$1
    local config_path="$CONFIGS_DIR/$config_name"
    
    if [ "$config_name" = "original" ]; then
        echo "❌ Не можна видалити оригінальну конфігурацію!"
        return 1
    fi
    
    if [ ! -d "$config_path" ]; then
        echo "❌ Конфігурація не знайдена: $config_name"
        return 1
    fi
    
    echo "\n⚠️  Видалення конфігурації: $config_name"
    echo "❓ Ви впевнені? (y/n)"
    read -r confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "$config_path"
        echo "✅ Конфігурацію видалено"
    else
        echo "❌ Видалення скасовано"
    fi
}

# Головне меню
while true; do
    list_configs
    
    echo "=================================================="
    echo "Оберіть дію:"
    echo "  [номер] - Застосувати конфігурацію"
    echo "  [d]     - Видалити конфігурацію"
    echo "  [c]     - Поточний стан системи"
    echo "  [q]     - Вихід"
    echo "=================================================="
    echo -n "Ваш вибір: "
    read -r choice
    
    case $choice in
        q|Q)
            echo "👋 До побачення!"
            exit 0
            ;;
        d|D)
            echo -n "Введіть назву конфігурації для видалення: "
            read -r config_to_delete
            delete_config "$config_to_delete"
            ;;
        c|C)
            echo "\n🖥️  Поточний стан системи:"
            echo "   Hostname: $(scutil --get HostName 2>/dev/null || echo 'Не встановлено')"
            [ -f ~/Library/Application\ Support/Code/machineid ] && echo "   Machine-ID: Присутній" || echo "   Machine-ID: Відсутній"
            [ -d ~/Library/Application\ Support/Code ] && echo "   VS Code: Встановлено" || echo "   VS Code: Не встановлено"
            echo "\nНатисніть Enter для продовження..."
            read
            ;;
        [0-9]*)
            # Отримати конфігурацію за індексом
            local configs_array=($(ls -1 "$CONFIGS_DIR"))
            local selected_index=$((choice - 1))
            
            if [ $selected_index -ge 0 ] && [ $selected_index -lt ${#configs_array[@]} ]; then
                apply_config "${configs_array[$selected_index]}"
                echo "\nНатисніть Enter для продовження..."
                read
            else
                echo "❌ Невірний номер конфігурації"
                sleep 2
            fi
            ;;
        *)
            echo "❌ Невірний вибір"
            sleep 1
            ;;
    esac
done
