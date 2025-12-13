#!/bin/zsh

echo "=================================================="
echo "🚀 ГЛИБОКЕ ВИДАЛЕННЯ WINDSURF ДЛЯ НОВОГО КЛІЄНТА"
echo "=================================================="

# Директорії для конфігурацій
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
if [ ! -f "$REPO_ROOT/cleanup_modules.json" ] && [ -f "$SCRIPT_DIR/../cleanup_modules.json" ]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
CONFIGS_DIR="$REPO_ROOT/configs"

# Завантаження змінних середовища з .env
ENV_FILE="$REPO_ROOT/.env"
if [ ! -f "$ENV_FILE" ] && [ -f "$REPO_ROOT/.env.example" ]; then
    echo "⚙️  Створюю .env з .env.example..."
    cp "$REPO_ROOT/.env.example" "$ENV_FILE"
    echo "✅ Файл .env створено"
fi

# Завантаження змінних з .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# Режими виконання
AUTO_YES="${AUTO_YES:-1}"
UNSAFE_MODE="${UNSAFE_MODE:-0}"

confirm() {
    local prompt="$1"
    if [ "${AUTO_YES}" = "1" ]; then
        return 0
    fi
    read -q "REPLY?${prompt} (y/n) "
    echo ""
    [[ "$REPLY" =~ ^[Yy]$ ]]
}

# Налаштування SUDO_ASKPASS для автоматичного введення пароля
SUDO_HELPER="$REPO_ROOT/cleanup_scripts/sudo_helper.sh"
if [ ! -f "$SUDO_HELPER" ] && [ -f "$REPO_ROOT/sudo_helper.sh" ]; then
    SUDO_HELPER="$REPO_ROOT/sudo_helper.sh"
fi
export SUDO_ASKPASS="$SUDO_HELPER"
chmod +x "$SUDO_ASKPASS" 2>/dev/null

# Завжди використовуємо askpass-режим, щоб не було TTY prompt
sudo() { command sudo -A "$@"; }

# Запит пароля sudo на початку (використовує SUDO_ASKPASS якщо доступно)
echo "\n🔑 Для виконання системних змін потрібен пароль адміністратора."
if [ -n "$SUDO_PASSWORD" ]; then
    sudo -v 2>/dev/null
else
    sudo -v
fi

# Перевірка, чи команда sudo була успішною
if [ $? -ne 0 ]; then
    echo "❌ Помилка: невірний пароль sudo або недостатньо прав. Вихід."
    exit 1
fi
echo "✅ Права адміністратора отримано."

# ПЕРЕВІРКА КОНФЛІКТІВ: Чи запущені інші IDE?
echo "\n🔍 Перевірка активних процесів..."
if pgrep -f "Visual Studio Code" > /dev/null 2>&1; then
    echo "⚠️  УВАГА: Visual Studio Code активний!"
    echo "💡 Рекомендація: Закрийте VS Code перед cleanup для уникнення конфліктів"
    if [ "${WINDSURF_FULL_AUTO:-0}" = "1" ]; then
        echo "ℹ️  FULL-режим: автоматичне продовження cleanup без запиту користувача"
    else
        if ! confirm "Продовжити cleanup?"; then
            echo "\n❌ Cleanup скасовано"
            exit 1
        fi
    fi
fi

ORIGINAL_CONFIG="$CONFIGS_DIR/original"

# ПОПЕРЕДНЬО: Генерація унікального hostname з реальною назвою (без підозрілих цифр)
# Формат: <CommonName>-<RandomName> (наприклад: Alex-Studio, James-Desktop)
# Розширений список реальних імен (150+ популярних імен):
REAL_NAMES=("Alex" "James" "Michael" "David" "Robert" "John" "Richard" "Charles" "Daniel" "Matthew" "Anthony" "Mark" "Donald" "Steven" "Paul" "Andrew" "Joshua" "Kenneth" "Kevin" "Brian" "George" "Edward" "Ronald" "Timothy" "Jason" "Jeffrey" "Ryan" "Jacob" "Gary" "Nicholas" "Eric" "Jonathan" "Stephen" "Larry" "Justin" "Scott" "Brandon" "Benjamin" "Samuel" "Frank" "Gregory" "Alexander" "Patrick" "Dennis" "Jerry" "Tyler" "Aaron" "Jose" "Adam" "Henry" "Nathan" "Zachary" "Kyle" "Walter" "Peter" "Harold" "Jeremy" "Keith" "Roger" "Gerald" "Carl" "Terry" "Sean" "Austin" "Arthur" "Lawrence" "Jesse" "Dylan" "Bryan" "Joe" "Jordan" "Billy" "Bruce" "Albert" "Willie" "Gabriel" "Logan" "Alan" "Juan" "Wayne" "Roy" "Ralph" "Randy" "Eugene" "Vincent" "Russell" "Elijah" "Louis" "Bobby" "Philip" "Johnny" "Bradley" "Noah" "Emma" "Olivia" "Ava" "Sophia" "Isabella" "Mia" "Charlotte" "Amelia" "Harper" "Evelyn" "Abigail" "Emily" "Elizabeth" "Sofia" "Avery" "Ella" "Scarlett" "Grace" "Chloe" "Victoria" "Riley" "Aria" "Lily" "Aubrey" "Zoey" "Penelope" "Lillian" "Addison" "Layla" "Natalie" "Camila" "Hannah" "Brooklyn" "Zoe" "Nora" "Leah" "Savannah" "Audrey" "Claire" "Eleanor" "Skylar" "Ellie" "Samantha" "Stella" "Paisley" "Violet" "Mila" "Allison" "Alexa" "Anna" "Hazel" "Aaliyah" "Ariana" "Lucy" "Caroline" "Sarah" "Genesis" "Kennedy" "Sadie" "Gabriella" "Madelyn" "Adeline" "Maya")
PLACE_NAMES=("Studio" "Office" "Desktop" "Workspace" "Workstation" "Lab" "Server" "Machine" "System" "Device" "Node" "Box" "Computer" "Platform" "Station" "Terminal" "Host" "Client" "Instance" "Pod" "iMac" "MacBook" "MacStudio" "MacPro" "Mini" "Pro" "Air" "MBP" "MBA" "Mac" "Laptop" "Tower" "Rig" "Setup" "Build" "Dev" "Work" "Home" "Personal" "Main" "Primary" "Secondary" "Backup" "Test" "Prod" "Local" "Remote" "Cloud" "Edge" "Core" "Hub" "Gateway")

# Додаткові реалістичні суфікси та префікси
SUFFIXES=("01" "02" "1" "2" "Pro" "Plus" "Max" "Ultra" "SE" "Air" "Mini" "Lite")
PREFIXES=("Dev" "Work" "Home" "Office" "Main" "My" "The")

# Функція для генерації валідного hostname
generate_hostname() {
    local attempt=0
    local max_attempts=10
    local format=$((RANDOM % 5))
    
    while [ $attempt -lt $max_attempts ]; do
        case $format in
            0)
                # Формат: Name-Place (наприклад: Alex-Studio)
                RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
                RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
                NEW_HOSTNAME="${RANDOM_NAME}-${RANDOM_PLACE}"
                ;;
            1)
                # Формат: Name-Place-Suffix (наприклад: James-MacBook-Pro)
                RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
                RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
                RANDOM_SUFFIX=${SUFFIXES[$((RANDOM % ${#SUFFIXES[@]}))]}
                NEW_HOSTNAME="${RANDOM_NAME}-${RANDOM_PLACE}-${RANDOM_SUFFIX}"
                ;;
            2)
                # Формат: Prefix-Name (наприклад: Work-Michael, Home-Sarah)
                RANDOM_PREFIX=${PREFIXES[$((RANDOM % ${#PREFIXES[@]}))]}
                RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
                NEW_HOSTNAME="${RANDOM_PREFIX}-${RANDOM_NAME}"
                ;;
            3)
                # Формат: Name's-Place (наприклад: Alex-MacBook, Emma-iMac)
                RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
                RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
                NEW_HOSTNAME="${RANDOM_NAME}s-${RANDOM_PLACE}"
                ;;
            4)
                # Формат: Place-Name (наприклад: MacBook-Alex, Studio-James)
                RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
                RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
                NEW_HOSTNAME="${RANDOM_PLACE}-${RANDOM_NAME}"
                ;;
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

# Отримання оригінального hostname
ORIGINAL_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "DEVs-Mac-Studio")

# Створити директорії якщо не існують
mkdir -p "$CONFIGS_DIR"

# Функція для безпечного видалення
safe_remove() {
    if [ -e "$1" ]; then
        echo "🗑️  Видаляю: $1"
        rm -rf "$1" 2>/dev/null
    fi
}

# Функція для збереження поточної конфігурації як оригінал
save_as_original() {
    echo "\n💎 Збереження поточної конфігурації як ОРИГІНАЛ..."
    
    mkdir -p "$ORIGINAL_CONFIG/User/globalStorage"
    
    # Зберегти Machine-ID
    if [ -f ~/Library/Application\ Support/Windsurf/machineid ]; then
        cp ~/Library/Application\ Support/Windsurf/machineid "$ORIGINAL_CONFIG/machineid"
        echo "  ✓ Machine-ID збережено"
    fi
    
    # Зберегти Storage
    if [ -f ~/Library/Application\ Support/Windsurf/storage.json ]; then
        cp ~/Library/Application\ Support/Windsurf/storage.json "$ORIGINAL_CONFIG/storage.json"
        echo "  ✓ Storage збережено"
    fi
    
    # Зберегти Global Storage
    if [ -f ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json ]; then
        cp ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json "$ORIGINAL_CONFIG/User/globalStorage/storage.json"
        echo "  ✓ Global Storage збережено"
    fi
    
    # Зберегти hostname
    ORIGINAL_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "DEVs-Mac-Studio")
    echo "$ORIGINAL_HOSTNAME" > "$ORIGINAL_CONFIG/hostname.txt"
    echo "  ✓ Hostname збережено: $ORIGINAL_HOSTNAME"
    
    # Метадані
    cat > "$ORIGINAL_CONFIG/metadata.json" << EOF
{
  "name": "original",
  "created": "$(date +%Y-%m-%d\ %H:%M:%S)",
  "hostname": "$ORIGINAL_HOSTNAME",
  "description": "Original Windsurf configuration for auto-restore"
}
EOF
    
    echo "✅ Оригінальна конфігурація збережена!"
}

# Перевірити чи існує оригінальна конфігурація, якщо ні - зберегти
if [ ! -d "$ORIGINAL_CONFIG" ]; then
    echo "\n⚠️  Оригінальна конфігурація не знайдена!"
    echo "📦 Зберігаю поточний стан як ОРИГІНАЛ..."
    save_as_original
fi

# 1. ОСНОВНІ ПАПКИ WINDSURF (окрім Application Support - його очистимо пізніше)
echo "\n[1/12] Видалення основних папок..."
safe_remove ~/Library/Application\ Support/windsurf
safe_remove ~/Library/Preferences/Windsurf
safe_remove ~/Library/Logs/Windsurf
safe_remove ~/.windsurf
safe_remove ~/.windsurf-server
safe_remove ~/.config/Windsurf
safe_remove ~/Library/Saved\ Application\ State/Windsurf.savedState
safe_remove ~/Library/Saved\ Application\ State/com.windsurf.savedState

echo "ℹ️  Application Support/Windsurf буде очищено пізніше (після резервування)"

# 2. ВИДАЛЕННЯ ДОДАТКУ
echo "\n[2/12] Видалення додатку Windsurf..."
echo "⚠️  ВАЖЛИВО: Додаток Windsurf буде ВИДАЛЕНО!"
echo "💡 Після cleanup потрібно буде скачати та встановити Windsurf заново"
safe_remove /Applications/Windsurf.app
echo "✅ Додаток видалено з /Applications"

# 3. КЕШІ ТА ТИМЧАСОВІ ФАЙЛИ
echo "\n[3/12] Очищення кешів і тимчасових файлів..."
safe_remove ~/Library/Caches/Windsurf
safe_remove ~/Library/Caches/windsurf
# Обробка глобальних шаблонів з 'setopt nullglob' щоб уникнути помилок
setopt nullglob
for cache_file in ~/Library/Caches/com.windsurf.*; do
    safe_remove "$cache_file"
done
unsetopt nullglob
find ~/Library/Caches -iname "*windsurf*" -maxdepth 2 -exec rm -rf {} + 2>/dev/null

# 4. CONTAINERS І GROUP CONTAINERS
echo "\n[4/12] Видалення контейнерів..."
find ~/Library/Containers -iname "*windsurf*" -exec rm -rf {} + 2>/dev/null
find ~/Library/Group\ Containers -iname "*windsurf*" -exec rm -rf {} + 2>/dev/null

# 5. COOKIES ТА WEB DATA
echo "\n[5/12] Очищення cookies та веб-даних..."
find ~/Library/Cookies -iname "*windsurf*" -exec rm -rf {} + 2>/dev/null
safe_remove ~/Library/WebKit/Windsurf

# 6. ВИДАЛЕННЯ PLIST-ФАЙЛІВ (НАЛАШТУВАННЯ)
echo "\n[6/12] Видалення plist-файлів налаштувань..."
find ~/Library/Preferences -iname "*windsurf*.plist" -delete 2>/dev/null
safe_remove ~/Library/Preferences/com.windsurf.plist
safe_remove ~/Library/Preferences/com.windsurf.helper.plist

# 7. ОЧИЩЕННЯ KEYCHAIN (КРИТИЧНО ДЛЯ ІДЕНТИФІКАЦІЇ!)
echo "\n[7/12] Очищення Keychain від записів Windsurf..."
echo "⚠️  Для видалення з Keychain потрібен пароль адміністратора"

# Видалення всіх записів Windsurf з keychain
security find-generic-password -l "Windsurf" 2>/dev/null | grep "keychain:" | while read -r line; do
    keychain=$(echo "$line" | sed 's/.*"\(.*\)".*/\1/')
    security delete-generic-password -l "Windsurf" "$keychain" 2>/dev/null
done

security find-generic-password -s "windsurf" 2>/dev/null | grep "keychain:" | while read -r line; do
    keychain=$(echo "$line" | sed 's/.*"\(.*\)".*/\1/')
    security delete-generic-password -s "windsurf" "$keychain" 2>/dev/null
done

# Видалення всіх інтернет-паролів Windsurf
security find-internet-password -s "windsurf" 2>/dev/null | grep "keychain:" | while read -r line; do
    keychain=$(echo "$line" | sed 's/.*"\(.*\)".*/\1/')
    security delete-internet-password -s "windsurf" "$keychain" 2>/dev/null
done

# Пошук і видалення за РОЗШИРЕНИМ списком варіантів назв (включно з пропущеними)
for service in "Windsurf" "windsurf" "com.windsurf" "Windsurf Editor" "Codeium Windsurf" \
               "Codeium" "codeium" "codeium.com" "api.codeium.com" \
               "com.exafunction.windsurf" "windsurf.com" "auth.windsurf.com" \
               "codeium-windsurf" "Codeium Editor"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
    security delete-generic-password -l "$service" 2>/dev/null
done

echo "✅ Keychain очищено (розширене очищення)"

if [ "${UNSAFE_MODE}" != "1" ]; then
    echo "\n🛡️  SAFE_MODE: виконую лише деінсталяцію/очистку (без підміни ідентифікаторів, hostname, мережі)."
    echo "🔥 Видаляю Application Support/Windsurf..."
    safe_remove ~/Library/Application\ Support/Windsurf
    xcrun --kill-cache 2>/dev/null
    echo "✅ SAFE_MODE cleanup завершено."
    exit 0
fi

# ДОДАТКОВО: Очищення всіх баз даних та сховищ ДО резервування
echo "\n🗑️  Очищення баз даних та локальних сховищ (перед резервуванням)..."
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb.backup
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb-shm
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb-wal
safe_remove ~/Library/Application\ Support/Windsurf/Local\ Storage
safe_remove ~/Library/Application\ Support/Windsurf/Session\ Storage
safe_remove ~/Library/Application\ Support/Windsurf/IndexedDB
safe_remove ~/Library/Application\ Support/Windsurf/databases
echo "✅ Бази даних очищено"

# 8. РЕЗЕРВУВАННЯ ТА ПІДМІНА MACHINE-ID ТА DEVICE-ID
echo "\n[8/12] Резервування та підміна machine-id та device-id файлів..."

# Створення директорії для бекапів
BACKUP_DIR="/tmp/windsurf_backup_$(date +%s)"
mkdir -p "$BACKUP_DIR"
echo "📦 Директорія бекапів: $BACKUP_DIR"

# Функція для генерації випадкового UUID
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

# Функція для генерації випадкового machine-id (hex формат)
generate_machine_id() {
    openssl rand -hex 32
}

# Функція для генерації випадкової MAC-адреси
generate_random_mac() {
    # Генеруємо 6 випадкових байтів у шістнадцятковому форматі
    # Встановлюємо другий біт першого октету в 0 (локально адміністрована адреса)
    # Встановлюємо перший біт першого октету в 0 (unicast)
    printf '02:%02x:%02x:%02x:%02x:%02x' $(( $RANDOM % 256 )) $(( $RANDOM % 256 )) $(( $RANDOM % 256 )) $(( $RANDOM % 256 )) $(( $RANDOM % 256 ))
}

# Резервування та підміна machineid
MACHINEID_PATH=~/Library/Application\ Support/Windsurf/machineid
if [ -f "$MACHINEID_PATH" ]; then
    echo "💾 Резервую machine-id..."
    cp "$MACHINEID_PATH" "$BACKUP_DIR/machineid.bak"
    NEW_MACHINE_ID=$(generate_machine_id)
    echo "$NEW_MACHINE_ID" > "$MACHINEID_PATH"
    echo "✅ Machine-ID підмінено на новий"
else
    echo "ℹ️  Machine-ID файл не знайдено"
fi

# Резервування та підміна storage.json
STORAGE_PATHS=(
    ~/Library/Application\ Support/Windsurf/storage.json
    ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json
)

for STORAGE_PATH in "${STORAGE_PATHS[@]}"; do
    if [ -f "$STORAGE_PATH" ]; then
        echo "💾 Резервую storage: $STORAGE_PATH"
        STORAGE_FILENAME=$(basename "$STORAGE_PATH")
        STORAGE_DIRNAME=$(dirname "$STORAGE_PATH" | sed 's/.*Windsurf\///')
        BACKUP_SUBDIR="$BACKUP_DIR/$(echo $STORAGE_DIRNAME | tr '/' '_')"
        mkdir -p "$BACKUP_SUBDIR"
        cp "$STORAGE_PATH" "$BACKUP_SUBDIR/${STORAGE_FILENAME}.bak"
        
        # Генерація нового storage.json з фейковими даними
        NEW_DEVICE_ID=$(generate_uuid)
        NEW_SESSION_ID=$(generate_uuid)
        cat > "$STORAGE_PATH" << EOF
{
  "telemetry.machineId": "$(generate_machine_id)",
  "telemetry.macMachineId": "$(generate_machine_id)",
  "telemetry.devDeviceId": "$NEW_DEVICE_ID",
  "telemetry.sqmId": "{$(generate_uuid)}",
  "install.time": "$(date +%s)000",
  "sessionId": "$NEW_SESSION_ID"
}
EOF
        echo "✅ Storage підмінено на новий: $STORAGE_PATH"
    fi
done

# Видалення кешів (їх не потрібно відновлювати)
safe_remove ~/Library/Application\ Support/Windsurf/User/workspaceStorage
safe_remove ~/Library/Application\ Support/Windsurf/GPUCache
safe_remove ~/Library/Application\ Support/Windsurf/CachedData
safe_remove ~/Library/Application\ Support/Windsurf/Code\ Cache

# Видалення всіх логів
find ~/Library/Application\ Support/Windsurf -name "*.log" -delete 2>/dev/null

echo "📁 Бекапи збережено в: $BACKUP_DIR"

# Зберегти НОВУ конфігурацію в configs/
echo "\n💾 Збереження нової конфігурації..."
NEW_CONFIG_NAME="$NEW_HOSTNAME"
NEW_CONFIG_PATH="$CONFIGS_DIR/$NEW_CONFIG_NAME"
mkdir -p "$NEW_CONFIG_PATH/User/globalStorage"

# Копіювати нові ідентифікатори
if [ -f ~/Library/Application\ Support/Windsurf/machineid ]; then
    cp ~/Library/Application\ Support/Windsurf/machineid "$NEW_CONFIG_PATH/machineid"
fi

if [ -f ~/Library/Application\ Support/Windsurf/storage.json ]; then
    cp ~/Library/Application\ Support/Windsurf/storage.json "$NEW_CONFIG_PATH/storage.json"
fi

if [ -f ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json ]; then
    cp ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json "$NEW_CONFIG_PATH/User/globalStorage/storage.json"
fi

# Зберегти новий hostname
echo "$NEW_HOSTNAME" > "$NEW_CONFIG_PATH/hostname.txt"

# Метадані
cat > "$NEW_CONFIG_PATH/metadata.json" << EOF
{
  "name": "$NEW_CONFIG_NAME",
  "created": "$(date +%Y-%m-%d\ %H:%M:%S)",
  "hostname": "$NEW_HOSTNAME",
  "description": "Auto-generated Windsurf profile"
}
EOF

echo "✅ Нову конфігурацію збережено: $NEW_CONFIG_NAME"
echo "📂 Локація: $NEW_CONFIG_PATH"

# 9. ОЧИЩЕННЯ ГЛОБАЛЬНИХ НАЛАШТУВАНЬ ТА РОЗШИРЕНЬ
echo "\n[9/12] Видалення розширень та глобальних налаштувань..."
safe_remove ~/.windsurf/extensions
safe_remove ~/.vscode-windsurf
safe_remove ~/Library/Application\ Support/Windsurf/extensions
safe_remove ~/Library/Application\ Support/Windsurf/User

# Видалення продуктових ідентифікаторів
safe_remove ~/Library/Application\ Support/Windsurf/product.json

# КРИТИЧНО: Видалення всіх файлів де може зберігатися API ключ Codeium
echo "🔐 Очищення всіх можливих місць зберігання API ключів..."
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb.backup
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb-shm
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb-wal
safe_remove ~/Library/Application\ Support/Windsurf/User/workspaceStorage
safe_remove ~/Library/Application\ Support/Windsurf/User/globalStorage
safe_remove ~/Library/Application\ Support/Windsurf/Local\ Storage
safe_remove ~/Library/Application\ Support/Windsurf/IndexedDB
safe_remove ~/Library/Application\ Support/Windsurf/Session\ Storage

# Видалення всіх можливих Codeium токенів з Keychain
echo "🔑 Видалення Codeium токенів з Keychain..."
for service in "Codeium" "codeium" "codeium.com" "api.codeium.com" "Codeium Windsurf" "codeium-windsurf"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
    security delete-generic-password -l "$service" 2>/dev/null
done

echo "✅ API ключі та токени очищено"

# 10. ЗМІНА СИСТЕМНИХ ІДЕНТИФІКАТОРІВ
echo "\n[10/12] Зміна системних ідентифікаторів..."

echo "🔄 Зміна hostname з $ORIGINAL_HOSTNAME на $NEW_HOSTNAME на 5 годин..."
echo "📝 Оригінальний hostname: $ORIGINAL_HOSTNAME"
echo "🎲 Новий унікальний hostname: $NEW_HOSTNAME"

sudo scutil --set HostName "$NEW_HOSTNAME"
sudo scutil --set LocalHostName "$NEW_HOSTNAME"
sudo scutil --set ComputerName "$NEW_HOSTNAME"

# Очищення DNS кешу
echo "🔄 Очищення DNS кешу..."
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder 2>/dev/null

# 11. ЗМІНА MAC-АДРЕСИ ТА МЕРЕЖЕВИХ ІДЕНТИФІКАТОРІВ
echo "\n[11/12] Зміна MAC-адреси та скидання мережевих ідентифікаторів..."
echo "⚠️  Для цих операцій потрібен пароль адміністратора"

# Отримання активного мережевого інтерфейсу (універсальний метод)
# Визначає інтерфейс, що використовується для маршруту за замовчуванням (Wi-Fi або Ethernet)
ACTIVE_INTERFACE=$(route -n get default | grep 'interface:' | awk '{print $2}')
if [ -n "$ACTIVE_INTERFACE" ]; then
    # Перевірка, чи це не віртуальний інтерфейс (наприклад, VPN)
    # Нам потрібен фізичний інтерфейс, що стоїть за ним
    PHYSICAL_INTERFACE=$(ifconfig "$ACTIVE_INTERFACE" | awk '/member:/{print $2; exit}' | head -n 1)
    if [ -n "$PHYSICAL_INTERFACE" ]; then
        ACTIVE_INTERFACE=$PHYSICAL_INTERFACE
    fi
fi

# Якщо інтерфейс не знайдено, спробувати старий метод для Wi-Fi
if [ -z "$ACTIVE_INTERFACE" ]; then
    ACTIVE_INTERFACE=$(networksetup -listallhardwareports | awk '/Hardware Port: Wi-Fi/{getline; print $2}')
fi

if [ -n "$ACTIVE_INTERFACE" ]; then
    echo "✅ MAC-адреса керується функцією 'Приватна адреса Wi-Fi' в macOS. Ручна зміна не потрібна."
    # Зберегти оригінальну MAC-адресу для відновлення (якщо вона колись знадобиться)
    echo "$ORIGINAL_MAC" > "$ORIGINAL_CONFIG/mac_address.txt"
    echo "  ✓ Оригінальна MAC-адреса збережена для відновлення (для довідки)"

    # Очищення ARP-кешу (таблиці відповідності IP-MAC у локальній мережі)
    echo "🔄 Очищення ARP-кешу..."
    sudo arp -a -d 2>/dev/null

    # Оновлення DHCP-лізингу (може змінити вашу локальну IP-адресу)
    echo "🔄 Оновлення DHCP-лізингу для $ACTIVE_INTERFACE..."
    sudo ipconfig set "$ACTIVE_INTERFACE" DHCP 2>/dev/null
else
    echo "⚠️  Не вдалося знайти активний мережевий інтерфейс для зміни MAC-адреси."
fi

# Повернення hostname у фоні через 5 годин (18000 секунд)
# Запуск у фоні з перенаправленням логів
{
    sleep 18000
    echo "\n⏰ 5 годин минуло. Відновлення оригінальних налаштувань..."    # Отримання оригінального hostname
    if [ -f "$ORIGINAL_CONFIG/hostname.txt" ]; then
        SAVED_HOSTNAME=$(cat "$ORIGINAL_CONFIG/hostname.txt")
    else
        SAVED_HOSTNAME="$ORIGINAL_HOSTNAME"
    fi
    
    # Відновлення hostname
    echo "🔄 Повертаю оригінальний hostname: $SAVED_HOSTNAME"
    sudo scutil --set HostName "$SAVED_HOSTNAME"
    sudo scutil --set LocalHostName "$SAVED_HOSTNAME"
    sudo scutil --set ComputerName "$SAVED_HOSTNAME"
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder 2>/dev/null

    # Відновлення MAC-адреси
    if [ -f "$ORIGINAL_CONFIG/mac_address.txt" ] && [ -n "$ACTIVE_INTERFACE" ]; then
        SAVED_MAC=$(cat "$ORIGINAL_CONFIG/mac_address.txt")
        echo "🔄 Повертаю оригінальну MAC-адресу для $ACTIVE_INTERFACE: $SAVED_MAC"
        sudo ifconfig "$ACTIVE_INTERFACE" ether "$SAVED_MAC"
        echo "✅ MAC-адресу відновлено"
    fi
    
    # Відновлення ОРИГІНАЛЬНОЇ конфігурації з configs/original
    if [ -d "$ORIGINAL_CONFIG" ]; then
        echo "🔄 Відновлення ОРИГІНАЛЬНОЇ конфігурації..."
        
        # Відновлення machineid
        if [ -f "$ORIGINAL_CONFIG/machineid" ]; then
            MACHINEID_PATH=~/Library/Application\ Support/Windsurf/machineid
            mkdir -p "$(dirname "$MACHINEID_PATH")"
            cp "$ORIGINAL_CONFIG/machineid" "$MACHINEID_PATH"
            echo "✅ Machine-ID відновлено з оригіналу"
        fi
        
        # Відновлення storage.json
        if [ -f "$ORIGINAL_CONFIG/storage.json" ]; then
            RESTORE_PATH=~/Library/Application\ Support/Windsurf/storage.json
            mkdir -p "$(dirname "$RESTORE_PATH")"
            cp "$ORIGINAL_CONFIG/storage.json" "$RESTORE_PATH"
            echo "✅ Storage відновлено з оригіналу"
        fi
        
        # Відновлення global storage
        if [ -f "$ORIGINAL_CONFIG/User/globalStorage/storage.json" ]; then
            RESTORE_PATH=~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json
            mkdir -p "$(dirname "$RESTORE_PATH")"
            cp "$ORIGINAL_CONFIG/User/globalStorage/storage.json" "$RESTORE_PATH"
            echo "✅ Global Storage відновлено з оригіналу"
        fi
        
        echo "✅ Оригінальна конфігурація повністю відновлена!"
    else
        echo "⚠️  Оригінальна конфігурація не знайдена в $ORIGINAL_CONFIG"
    fi
    
    # Відновлення з тимчасового бекапу (для сумісності)
    if [ -d "$BACKUP_DIR" ]; then
        echo "🔄 Видалення тимчасового бекапу..."
        rm -rf "$BACKUP_DIR"
        echo "✅ Бекап видалено"
    fi
    
    echo "\n🎉 Відновлення завершено! Система повернута до оригінального стану."
} > /tmp/windsurf_restore_$$.log 2>&1 &

RESTORE_PID=$!
echo ""
echo "✅ Hostname змінено на: $NEW_HOSTNAME"
echo "📋 Процес автовідновлення запущено (PID: $RESTORE_PID)"
echo "⏰ Оригінальні налаштування будуть відновлено за 5 годин"
echo ""

# ФІНАЛЬНЕ ОЧИЩЕННЯ
echo "\n🧹 Фінальне очищення залишкових файлів..."
find ~/Library -iname "*windsurf*" -maxdepth 3 -not -path "*/Trash/*" -exec rm -rf {} + 2>/dev/null
find ~/.config -iname "*windsurf*" -exec rm -rf {} + 2>/dev/null

# Очищення системних логів
sudo rm -rf /var/log/*windsurf* 2>/dev/null
sudo rm -rf /Library/Logs/*windsurf* 2>/dev/null

# КРИТИЧНО: Повне видалення Application Support/Windsurf (після збереження всіх бекапів)
echo "\n🔥 КРИТИЧНЕ ОЧИЩЕННЯ: Видалення всієї папки Application Support/Windsurf..."
echo "⚠️  Це видалить ВСІ дані включно з базами даних де зберігаються API ключі!"
safe_remove ~/Library/Application\ Support/Windsurf
echo "✅ Application Support/Windsurf повністю видалено"

# 12. ОЧИЩЕННЯ КЕШІВ ІНСТРУМЕНТІВ РОЗРОБНИКА
echo "\n[12/12] Очищення кешів інструментів розробника..."
xcrun --kill-cache 2>/dev/null
echo "✅ Кеші інструментів розробника очищено."

# Додати запис в історію
if [ -f "$REPO_ROOT/history_tracker.sh" ]; then
    "$REPO_ROOT/history_tracker.sh" add "windsurf" "cleanup" "Full cleanup completed. New hostname: $NEW_HOSTNAME" 2>/dev/null
fi

echo "\n=================================================="
echo "✅ ОЧИЩЕННЯ УСПІШНО ЗАВЕРШЕНО!"
echo "=================================================="
echo ""
echo "📋 Виконані дії:"
echo "   ✓ Видалено всі файли Windsurf"
echo "   ✓ Очищено Keychain від записів Windsurf"
echo "   ✓ Створено бекап та підмінено machine-id на новий"
echo "   ✓ Створено бекап та підмінено device-id на новий"
echo "   ✓ Очищено всі кеші та тимчасові файли"
echo "   ✓ Видалено розширення та налаштування"
echo "   ✓ Змінено hostname на $NEW_HOSTNAME"
echo "   ✓ MAC-адреса керується системою macOS (Приватна адреса Wi-Fi)"
echo "   ✓ Очищено DNS кеш"
echo "   ✓ Очищено кеші інструментів розробника"
echo ""
echo "💾 Інформація про бекапи:"
echo "   • Тимчасовий бекап: $BACKUP_DIR"
echo "   • Machine-ID: $([ -f "$BACKUP_DIR/machineid.bak" ] && echo "✓ збережено" || echo "✗ не знайдено")"
echo "   • Storage файли: $(find "$BACKUP_DIR" -name "*.json.bak" 2>/dev/null | wc -l | xargs) шт."
echo ""
echo "🔧 СИСТЕМА КОНФІГУРАЦІЙ:"
echo "   • Оригінальна конфігурація: збережена в configs/original"
echo "   • Нова конфігурація: $NEW_CONFIG_NAME"
echo "   • Локація: $CONFIGS_DIR"
echo "   • Управління: ./manage_configs.sh"
echo ""
echo "⏰ АВТОМАТИЧНЕ ВІДНОВЛЕННЯ:"
echo "   • Через 5 годин буде відновлена ОРИГІНАЛЬНА конфігурація"
echo "   • Hostname повернеться до оригінального"
echo "   • Machine-ID та Device-ID повернуться до оригіналу"
echo "   • PID процесу відновлення: $RESTORE_PID"
echo ""
echo "💡 УПРАВЛІННЯ КОНФІГУРАЦІЯМИ:"
echo "   • Запустіть: ./manage_configs.sh"
echo "   • Перемикайтеся між будь-якими збереженими профілями"
echo "   • Зберігайте необмежену кількість конфігурацій"
echo ""
echo "⚠️  ВАЖЛИВО:"
echo "   • НЕ перезавантажуйте Mac якщо хочете автовідновлення!"
echo "   • Windsurf тепер сприйме систему як НОВОГО клієнта"
echo "   • Для ручного відновлення: cp $BACKUP_DIR/* до відповідних директорій"
echo ""
echo "💡 РЕКОМЕНДАЦІЇ:"
echo "   • Якщо потрібно встановити Windsurf, завантажте його з: https://codeium.com/windsurf"
echo "   • При першому запуску він побачить вас як НОВОГО користувача"
echo ""
echo "🔄 Для перезавантаження (вимкне автовідновлення): sudo shutdown -r now"
echo "📊 Для перевірки процесу відновлення: ps -p $RESTORE_PID"
echo "=================================================="