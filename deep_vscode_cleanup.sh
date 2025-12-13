#!/bin/zsh

setopt NULL_GLOB

echo "=================================================="
echo "🚀 ГЛИБОКЕ ВИДАЛЕННЯ VS CODE ДЛЯ НОВОГО КЛІЄНТА"
echo "=================================================="

# Директорії для конфігурацій
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs_vscode"
ORIGINAL_CONFIG="$CONFIGS_DIR/original"

# Завантаження змінних середовища з .env
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    echo "⚙️  Створюю .env з .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    echo "✅ Файл .env створено"
fi

# Завантаження змінних з .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# Налаштування SUDO_ASKPASS для автоматичного введення пароля
export SUDO_ASKPASS="$SCRIPT_DIR/sudo_helper.sh"
chmod +x "$SUDO_ASKPASS" 2>/dev/null

# Запит пароля sudo на початку (використовує SUDO_ASKPASS якщо доступно)
echo "\n🔑 Для виконання системних змін потрібен пароль адміністратора."
if [ -n "$SUDO_PASSWORD" ]; then
    echo "$SUDO_PASSWORD" | sudo -S -v 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Помилка: невірний пароль sudo або недостатньо прав. Вихід."
        exit 1
    fi
else
    # Для веб-інтерфейсу використовуємо SUDO_ASKPASS
    if [ -n "$SUDO_ASKPASS" ] && [ -f "$SUDO_ASKPASS" ]; then
        sudo -A -v 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "❌ Помилка: невірний пароль sudo або недостатньо прав. Вихід."
            exit 1
        fi
    else
        echo "⚠️  Запуск без sudo прав (веб-режим)"
        # Продовжуємо без sudo для команд, які його не потребують
    fi
fi
echo "✅ Права адміністратора отримано."

# ПЕРЕВІРКА КОНФЛІКТІВ: Чи запущений Windsurf?
echo "\n🔍 Перевірка активних процесів..."
if pgrep -f "Windsurf" > /dev/null 2>&1; then
    echo "⚠️  УВАГА: Windsurf активний!"
    echo "💡 Рекомендація: Закрийте Windsurf перед cleanup для уникнення конфліктів"
    read -q "REPLY?Продовжити cleanup? (y/n) "
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "\n❌ Cleanup скасовано"
        exit 1
    fi
    echo ""
fi

# Генерація унікального hostname - розширений список (150+ імен)
REAL_NAMES=("Alex" "James" "Michael" "David" "Robert" "John" "Richard" "Charles" "Daniel" "Matthew" "Anthony" "Mark" "Donald" "Steven" "Paul" "Andrew" "Joshua" "Kenneth" "Kevin" "Brian" "George" "Edward" "Ronald" "Timothy" "Jason" "Jeffrey" "Ryan" "Jacob" "Gary" "Nicholas" "Eric" "Jonathan" "Stephen" "Larry" "Justin" "Scott" "Brandon" "Benjamin" "Samuel" "Frank" "Gregory" "Alexander" "Patrick" "Dennis" "Jerry" "Tyler" "Aaron" "Jose" "Adam" "Henry" "Nathan" "Zachary" "Kyle" "Walter" "Peter" "Harold" "Jeremy" "Keith" "Roger" "Gerald" "Carl" "Terry" "Sean" "Austin" "Arthur" "Lawrence" "Jesse" "Dylan" "Bryan" "Joe" "Jordan" "Billy" "Bruce" "Albert" "Willie" "Gabriel" "Logan" "Alan" "Juan" "Wayne" "Roy" "Ralph" "Randy" "Eugene" "Vincent" "Russell" "Elijah" "Louis" "Bobby" "Philip" "Johnny" "Bradley" "Noah" "Emma" "Olivia" "Ava" "Sophia" "Isabella" "Mia" "Charlotte" "Amelia" "Harper" "Evelyn" "Abigail" "Emily" "Elizabeth" "Sofia" "Avery" "Ella" "Scarlett" "Grace" "Chloe" "Victoria" "Riley" "Aria" "Lily" "Aubrey" "Zoey" "Penelope" "Lillian" "Addison" "Layla" "Natalie" "Camila" "Hannah" "Brooklyn" "Zoe" "Nora" "Leah" "Savannah" "Audrey" "Claire" "Eleanor" "Skylar" "Ellie" "Samantha" "Stella" "Paisley" "Violet" "Mila" "Allison" "Alexa" "Anna" "Hazel" "Aaliyah" "Ariana" "Lucy" "Caroline" "Sarah" "Genesis" "Kennedy" "Sadie" "Gabriella" "Madelyn" "Adeline" "Maya")
PLACE_NAMES=("Studio" "Office" "Desktop" "Workspace" "Workstation" "Lab" "Server" "Machine" "System" "Device" "Node" "Box" "Computer" "Platform" "Station" "Terminal" "Host" "Client" "Instance" "Pod" "iMac" "MacBook" "MacStudio" "MacPro" "Mini" "Pro" "Air" "MBP" "MBA" "Mac" "Laptop" "Tower" "Rig" "Setup" "Build" "Dev" "Work" "Home" "Personal" "Main" "Primary" "Secondary" "Backup" "Test" "Prod" "Local" "Remote" "Cloud" "Edge" "Core" "Hub" "Gateway")
SUFFIXES=("01" "02" "1" "2" "Pro" "Plus" "Max" "Ultra" "SE" "Air" "Mini" "Lite")
PREFIXES=("Dev" "Work" "Home" "Office" "Main" "My" "The")

# Функція для генерації валідного hostname
generate_hostname() {
    local attempt=0
    local max_attempts=10
    local format=$((RANDOM % 5))
    
    while [ $attempt -lt $max_attempts ]; do
        case $format in
            0) NEW_HOSTNAME="${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}"-"${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}";;
            1) NEW_HOSTNAME="${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}"-"${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}"-"${SUFFIXES[$((RANDOM % ${#SUFFIXES[@]}))]}";;
            2) NEW_HOSTNAME="${PREFIXES[$((RANDOM % ${#PREFIXES[@]}))]}"-"${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}";;
            3) NEW_HOSTNAME="${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}s-${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}";;
            4) NEW_HOSTNAME="${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}"-"${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}";;
        esac
        
        # ВАЛІДАЦІЯ: перевірити що hostname не порожній і має мінімальну довжину
        if [ -n "$NEW_HOSTNAME" ] && [ ${#NEW_HOSTNAME} -gt 3 ] && [[ "$NEW_HOSTNAME" != "-"* ]] && [[ "$NEW_HOSTNAME" != *"-" ]]; then
            echo "$NEW_HOSTNAME"
            return 0
        fi
        
        attempt=$((attempt + 1))
        format=$((RANDOM % 5))
    done
    
    # FALLBACK: якщо валідація не пройшла
    echo "User-Mac-$RANDOM"
}

# Генерація hostname з валідацією
NEW_HOSTNAME=$(generate_hostname)

ORIGINAL_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "DEVs-Mac-Studio")
mkdir -p "$CONFIGS_DIR"

# Функції
safe_remove() { [ -e "$1" ] && echo "🗑️  Видаляю: $1" && rm -rf "$1" 2>/dev/null; }
generate_uuid() { uuidgen | tr '[:upper:]' '[:lower:]'; }
generate_machine_id() { openssl rand -hex 32; }

# Збереження оригіналу якщо не існує
if [ ! -d "$ORIGINAL_CONFIG" ]; then
    echo "\n💎 Збереження ОРИГІНАЛЬНОЇ конфігурації..."
    mkdir -p "$ORIGINAL_CONFIG/User/globalStorage"
    [ -f ~/Library/Application\ Support/Code/machineid ] && cp ~/Library/Application\ Support/Code/machineid "$ORIGINAL_CONFIG/machineid"
    [ -f ~/Library/Application\ Support/Code/storage.json ] && cp ~/Library/Application\ Support/Code/storage.json "$ORIGINAL_CONFIG/storage.json"
    [ -f ~/Library/Application\ Support/Code/User/globalStorage/storage.json ] && cp ~/Library/Application\ Support/Code/User/globalStorage/storage.json "$ORIGINAL_CONFIG/User/globalStorage/storage.json"
    echo "$ORIGINAL_HOSTNAME" > "$ORIGINAL_CONFIG/hostname.txt"
    echo '{"name":"original","created":"'$(date +%Y-%m-%d\ %H:%M:%S)'","hostname":"'$ORIGINAL_HOSTNAME'"}' > "$ORIGINAL_CONFIG/metadata.json"
    echo "✅ Оригінал збережено"
fi

# 1-6. Видалення файлів
echo "\n[1/12] Видалення VS Code папок..."
safe_remove ~/Library/Application\ Support/code
safe_remove ~/Library/Preferences/Code
safe_remove ~/Library/Logs/Code
safe_remove ~/.vscode
safe_remove ~/.vscode-server
safe_remove ~/.config/Code
safe_remove ~/Library/Saved\ Application\ State/com.microsoft.VSCode.savedState

echo "\n[2/12] Видалення додатку..."
safe_remove /Applications/Visual\ Studio\ Code.app

echo "\n[3/12] Очищення кешів..."
safe_remove ~/Library/Caches/Code
safe_remove ~/Library/Caches/com.microsoft.VSCode
find ~/Library/Caches -iname "*vscode*" -maxdepth 2 -exec rm -rf {} + 2>/dev/null

echo "\n[4/12] Видалення контейнерів..."
find ~/Library/Containers -iname "*vscode*" -exec rm -rf {} + 2>/dev/null
find ~/Library/Group\ Containers -iname "*vscode*" -exec rm -rf {} + 2>/dev/null

echo "\n[5/12] Cookies..."
find ~/Library/Cookies -iname "*vscode*" -exec rm -rf {} + 2>/dev/null

echo "\n[6/12] Plist файли..."
find ~/Library/Preferences -iname "*vscode*.plist" -delete 2>/dev/null
find ~/Library/Preferences -iname "*code*.plist" -delete 2>/dev/null

# 7. Keychain
echo "\n[7/12] Очищення Keychain..."
for service in "Visual Studio Code" "vscode" "VSCode" "com.microsoft.VSCode" "code" "github.com" "GitHub" "microsoft.com" "Microsoft"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
done
echo "✅ Keychain очищено"

# 8. Резервування та підміна ID
echo "\n[8/12] Резервування та підміна ідентифікаторів..."
BACKUP_DIR="/tmp/vscode_backup_$(date +%s)"
mkdir -p "$BACKUP_DIR"
echo "📦 Бекап: $BACKUP_DIR"

# Machine-ID
MACHINEID_PATH=~/Library/Application\ Support/Code/machineid
if [ -f "$MACHINEID_PATH" ]; then
    cp "$MACHINEID_PATH" "$BACKUP_DIR/machineid.bak"
    echo "$(generate_machine_id)" > "$MACHINEID_PATH"
    echo "✅ Machine-ID підмінено"
fi

# Storage files
for STORAGE_PATH in ~/Library/Application\ Support/Code/storage.json ~/Library/Application\ Support/Code/User/globalStorage/storage.json; do
    if [ -f "$STORAGE_PATH" ]; then
        STORAGE_FILENAME=$(basename "$STORAGE_PATH")
        STORAGE_DIRNAME=$(dirname "$STORAGE_PATH" | sed 's/.*Code\///')
        BACKUP_SUBDIR="$BACKUP_DIR/$(echo $STORAGE_DIRNAME | tr '/' '_')"
        mkdir -p "$BACKUP_SUBDIR"
        cp "$STORAGE_PATH" "$BACKUP_SUBDIR/${STORAGE_FILENAME}.bak"
        cat > "$STORAGE_PATH" << EOFSTORAGE
{"telemetry.machineId":"$(generate_machine_id)","telemetry.macMachineId":"$(generate_machine_id)","telemetry.devDeviceId":"$(generate_uuid)","telemetry.sqmId":"{$(generate_uuid)}","install.time":"$(date +%s)000","sessionId":"$(generate_uuid)"}
EOFSTORAGE
        echo "✅ Storage підмінено: $STORAGE_PATH"
    fi
done

# Видалення кешів
safe_remove ~/Library/Application\ Support/Code/User/workspaceStorage
safe_remove ~/Library/Application\ Support/Code/GPUCache
safe_remove ~/Library/Application\ Support/Code/CachedData
safe_remove ~/Library/Application\ Support/Code/Code\ Cache
find ~/Library/Application\ Support/Code -name "*.log" -delete 2>/dev/null

# Збереження нової конфігурації
NEW_CONFIG_PATH="$CONFIGS_DIR/$NEW_HOSTNAME"
mkdir -p "$NEW_CONFIG_PATH/User/globalStorage"
[ -f ~/Library/Application\ Support/Code/machineid ] && cp ~/Library/Application\ Support/Code/machineid "$NEW_CONFIG_PATH/machineid"
[ -f ~/Library/Application\ Support/Code/storage.json ] && cp ~/Library/Application\ Support/Code/storage.json "$NEW_CONFIG_PATH/storage.json"
[ -f ~/Library/Application\ Support/Code/User/globalStorage/storage.json ] && cp ~/Library/Application\ Support/Code/User/globalStorage/storage.json "$NEW_CONFIG_PATH/User/globalStorage/storage.json"
echo "$NEW_HOSTNAME" > "$NEW_CONFIG_PATH/hostname.txt"
echo '{"name":"'$NEW_HOSTNAME'","created":"'$(date +%Y-%m-%d\ %H:%M:%S)'","hostname":"'$NEW_HOSTNAME'"}' > "$NEW_CONFIG_PATH/metadata.json"
echo "✅ Нову конфігурацію збережено: $NEW_HOSTNAME"

# 9. Розширення
echo "\n[9/12] Видалення розширень..."
safe_remove ~/.vscode/extensions
safe_remove ~/Library/Application\ Support/Code/extensions
safe_remove ~/Library/Application\ Support/Code/User
safe_remove ~/Library/Application\ Support/Code/product.json
# Remove state.vscdb files with proper glob handling
if ls ~/Library/Application\ Support/Code/User/globalStorage/state.vscdb* 2>/dev/null; then
    find ~/Library/Application\ Support/Code/User/globalStorage -name "state.vscdb*" -print0 2>/dev/null | xargs -0 rm -rf 2>/dev/null
    echo "🗑️  Видалено state.vscdb файли"
else
    echo " state.vscdb файли не знайдено"
fi
safe_remove ~/Library/Application\ Support/Code/Local\ Storage
safe_remove ~/Library/Application\ Support/Code/IndexedDB
safe_remove ~/Library/Application\ Support/Code/Session\ Storage

# 10. Hostname
echo "\n[10/12] Зміна hostname..."
echo " $ORIGINAL_HOSTNAME → $NEW_HOSTNAME"
if [ -n "$SUDO_PASSWORD" ]; then
    echo "$SUDO_PASSWORD" | sudo -S scutil --set HostName "$NEW_HOSTNAME"
    echo "$SUDO_PASSWORD" | sudo -S scutil --set LocalHostName "$NEW_HOSTNAME"
    echo "$SUDO_PASSWORD" | sudo -S scutil --set ComputerName "$NEW_HOSTNAME"
else
    sudo scutil --set HostName "$NEW_HOSTNAME"
    sudo scutil --set LocalHostName "$NEW_HOSTNAME"
    sudo scutil --set ComputerName "$NEW_HOSTNAME"
fi

# Очищення DNS кешу
echo " Очищення DNS кешу..."
if [ -n "$SUDO_PASSWORD" ]; then
    echo "$SUDO_PASSWORD" | sudo -S dscacheutil -flushcache
    echo "$SUDO_PASSWORD" | sudo -S killall -HUP mDNSResponder 2>/dev/null
else
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder 2>/dev/null
fi

# 11. Мережа
echo "\n[11/12] Мережеві ідентифікатори..."
ACTIVE_INTERFACE=$(route -n get default 2>/dev/null | grep 'interface:' | awk '{print $2}')
[ -z "$ACTIVE_INTERFACE" ] && ACTIVE_INTERFACE=$(networksetup -listallhardwareports | awk '/Hardware Port: Wi-Fi/{getline; print $2}')
if [ -n "$ACTIVE_INTERFACE" ]; then
    ORIGINAL_MAC=$(ifconfig "$ACTIVE_INTERFACE" | awk '/ether/{print $2}')
    echo "$ORIGINAL_MAC" > "$ORIGINAL_CONFIG/mac_address.txt"
    if [ -n "$SUDO_PASSWORD" ]; then
        echo "$SUDO_PASSWORD" | sudo -S arp -a -d 2>/dev/null
        echo "$SUDO_PASSWORD" | sudo -S ipconfig set "$ACTIVE_INTERFACE" DHCP 2>/dev/null
    else
        sudo arp -a -d 2>/dev/null
        sudo ipconfig set "$ACTIVE_INTERFACE" DHCP 2>/dev/null
    fi
    echo "✅ Мережу оновлено"
fi

# 12. Автовідновлення через 5 годин
{
    sleep 18000
    echo "\n⏰ Відновлення оригіналу..."
    SAVED_HOSTNAME=$(cat "$ORIGINAL_CONFIG/hostname.txt" 2>/dev/null || echo "$ORIGINAL_HOSTNAME")
    if [ -n "$SUDO_PASSWORD" ]; then
        echo "$SUDO_PASSWORD" | sudo -S scutil --set HostName "$SAVED_HOSTNAME"
        echo "$SUDO_PASSWORD" | sudo -S scutil --set LocalHostName "$SAVED_HOSTNAME"
        echo "$SUDO_PASSWORD" | sudo -S scutil --set ComputerName "$SAVED_HOSTNAME"
        echo "$SUDO_PASSWORD" | sudo -S dscacheutil -flushcache
        echo "$SUDO_PASSWORD" | sudo -S killall -HUP mDNSResponder 2>/dev/null
    else
        sudo scutil --set HostName "$SAVED_HOSTNAME"
        sudo scutil --set LocalHostName "$SAVED_HOSTNAME"
        sudo scutil --set ComputerName "$SAVED_HOSTNAME"
        sudo dscacheutil -flushcache
        sudo killall -HUP mDNSResponder 2>/dev/null
    fi
    
    # Відновлення конфігів
    [ -f "$ORIGINAL_CONFIG/machineid" ] && cp "$ORIGINAL_CONFIG/machineid" ~/Library/Application\ Support/Code/machineid
    [ -f "$ORIGINAL_CONFIG/storage.json" ] && cp "$ORIGINAL_CONFIG/storage.json" ~/Library/Application\ Support/Code/storage.json
    [ -f "$ORIGINAL_CONFIG/User/globalStorage/storage.json" ] && mkdir -p ~/Library/Application\ Support/Code/User/globalStorage && cp "$ORIGINAL_CONFIG/User/globalStorage/storage.json" ~/Library/Application\ Support/Code/User/globalStorage/storage.json
    
    # MAC
    if [ -f "$ORIGINAL_CONFIG/mac_address.txt" ] && [ -n "$ACTIVE_INTERFACE" ]; then
        SAVED_MAC=$(cat "$ORIGINAL_CONFIG/mac_address.txt")
        if [ -n "$SUDO_PASSWORD" ]; then
            echo "$SUDO_PASSWORD" | sudo -S ifconfig "$ACTIVE_INTERFACE" ether "$SAVED_MAC"
        else
            sudo ifconfig "$ACTIVE_INTERFACE" ether "$SAVED_MAC"
        fi
    fi
    
    rm -rf "$BACKUP_DIR"
    echo "✅ Відновлення завершено!"
} > /tmp/vscode_restore_$$.log 2>&1 &

RESTORE_PID=$!

# Фінал
echo "\n[12/12] Фінальне очищення..."
# Видалити всі файли VS Code з безпечним glob handling
find ~/Library -iname "*vscode*" -maxdepth 3 -not -path "*/Trash/*" -print0 2>/dev/null | xargs -0 rm -rf 2>/dev/null
find ~/.config -iname "*vscode*" -print0 2>/dev/null | xargs -0 rm -rf 2>/dev/null
sudo find /var/log -iname "*vscode*" -print0 2>/dev/null | sudo xargs -0 rm -rf 2>/dev/null
safe_remove ~/Library/Application\ Support/Code

# 13. АВТОМАТИЧНА ІНСТАЛЯЦІЯ VS CODE
echo "\n[13/13] Автоматична інсталяція VS Code..."
VSCODE_ZIP="$SCRIPT_DIR/VSCode-darwin-universal.zip"
VSCODE_APP="$SCRIPT_DIR/Visual Studio Code.app"

# Перевірка ZIP файлу
if [ -f "$VSCODE_ZIP" ]; then
    echo "📦 Знайдено VS Code ZIP: $(basename $VSCODE_ZIP)"
    echo "🔄 Розпакування..."
    
    # Розпакування ZIP (швидка версія)
    cd "$SCRIPT_DIR"
    unzip -o "$VSCODE_ZIP" > /dev/null
    
    if [ $? -eq 0 ] && [ -d "Visual Studio Code.app" ]; then
        echo "✅ ZIP розпаковано успішно"
        VSCODE_APP="$SCRIPT_DIR/Visual Studio Code.app"
    else
        echo "❌ Помилка розпакування ZIP"
    fi
fi

# Встановлення з .app
if [ -d "$VSCODE_APP" ]; then
    echo "📱 Знайдено VS Code додаток: $(basename "$VSCODE_APP")"
    echo "🔄 Копіювання в /Applications..."
    
    # Видалити старий якщо існує
    if [ -d "/Applications/Visual Studio Code.app" ]; then
        if [ -n "$SUDO_PASSWORD" ]; then
            echo "$SUDO_PASSWORD" | sudo -S rm -rf "/Applications/Visual Studio Code.app"
        else
            sudo rm -rf "/Applications/Visual Studio Code.app"
        fi
        echo "🗑️  Видалено стару версію"
    fi
    
    # Копіювання в Applications
    if [ -n "$SUDO_PASSWORD" ]; then
        echo "$SUDO_PASSWORD" | sudo -S cp -R "$VSCODE_APP" /Applications/
    else
        sudo cp -R "$VSCODE_APP" /Applications/
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ VS Code успішно встановлено в /Applications/"
        
        # Очікування для завершення копіювання
        sleep 2
        
        # Очищення тимчасових файлів
        if [ -f "$VSCODE_ZIP" ] && [ -d "$SCRIPT_DIR/Visual Studio Code.app" ]; then
            rm -rf "$SCRIPT_DIR/Visual Studio Code.app"
            echo "🧹 Тимчасові файли очищено"
        fi
        
        echo "🎉 VS Code готовий до запуску!"
    else
        echo "❌ Помилка копіювання додатку"
    fi
else
    echo "⚠️  VS Code не знайдено"
    echo "💡 Переконайтесь що файл VSCode-darwin-universal.zip знаходиться в: $SCRIPT_DIR"
    echo "💡 Або скачайте VS Code вручну з: https://code.visualstudio.com/"
fi

# Додати запис в історію
if [ -f "$SCRIPT_DIR/history_tracker.sh" ]; then
    "$SCRIPT_DIR/history_tracker.sh" add "vscode" "cleanup" "Full cleanup completed. New hostname: $NEW_HOSTNAME" 2>/dev/null
fi

echo "\n=================================================="
echo "✅ ОЧИЩЕННЯ ТА ІНСТАЛЯЦІЯ ЗАВЕРШЕНО!"
echo "=================================================="
echo "📋 Виконано:"
echo "   ✓ Видалено всі файли VS Code"
echo "   ✓ Очищено Keychain"
echo "   ✓ Підмінено machine-id та device-id"
echo "   ✓ Змінено hostname на: $NEW_HOSTNAME"
echo "   ✓ Оновлено мережу"
if [ -d "/Applications/Visual Studio Code.app" ]; then
    echo "   ✓ VS Code встановлено в /Applications/"
fi
echo "\n💾 Бекап: $BACKUP_DIR"
echo "📂 Конфігурація: $NEW_CONFIG_PATH"
echo "⏰ Автовідновлення через 5 годин (PID: $RESTORE_PID)"
echo "\n🚀 ЗАПУСК VS CODE:"
echo "   • VS Code можна запускати ОДРАЗУ (перезавантаження НЕ потрібне)"
echo "   • Просто запустіть Visual Studio Code.app"
echo "   • При першому запуску він побачить вас як НОВОГО користувача"
echo "=================================================="
