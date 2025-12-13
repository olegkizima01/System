#!/bin/zsh

echo "==================================================="
echo "🚀 ГЕНЕРАЦІЯ 100 НОВИХ КОНФІГУРАЦІЙ WINDSURF"
echo "==================================================="

# Директорії для конфігурацій
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs"

# Створити директорію configs, якщо не існує
mkdir -p "$CONFIGS_DIR"

# ПОПЕРЕДНЬО: Генерація унікального hostname з реальною назвою (без підозрілих цифр)
# Формат: <CommonName>-<RandomName> (наприклад: Alex-Studio, James-Desktop)
# Список реальних імен:
REAL_NAMES=("Alex" "James" "Michael" "David" "Robert" "John" "Richard" "Charles" "Daniel" "Matthew" "Anthony" "Mark" "Donald" "Steven" "Paul" "Andrew" "Joshua" "Kenneth" "Kevin" "Brian" "George" "Edward" "Ronald" "Timothy" "Jason" "Jeffrey" "Ryan" "Jacob" "Gary" "Nicholas" "Eric" "Jonathan" "Stephen" "Larry" "Justin" "Scott" "Brandon" "Benjamin" "Samuel" "Frank" "Gregory" "Alexander" "Patrick" "Dennis" "Jerry" "Tyler" "Aaron" "Jose" "Adam" "Henry")
PLACE_NAMES=("Studio" "Office" "Desktop" "Workspace" "Workstation" "Lab" "Server" "Machine" "System" "Device" "Node" "Box" "Computer" "Platform" "Station" "Terminal" "Host" "Client" "Instance" "Pod")

# Функція для генерації випадкового UUID
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

# Функція для генерації випадкового machine-id (hex формат)
generate_machine_id() {
    openssl rand -hex 32
}

# Цикл для генерації 100 конфігурацій
for i in {1..100};
do
    echo "\n--- Генерація конфігурації $i/100 ---"

    # Вибір випадкових імені та місця для hostname
    RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
    RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
    NEW_HOSTNAME="${RANDOM_NAME}-${RANDOM_PLACE}"

    NEW_CONFIG_NAME="$NEW_HOSTNAME"
    NEW_CONFIG_PATH="$CONFIGS_DIR/$NEW_CONFIG_NAME"

    # Перевірка на існування, щоб уникнути перезапису (хоча RANDOM робить це малоймовірним)
    if [ -d "$NEW_CONFIG_PATH" ]; then
        echo "⚠️  Конфігурація з іменем \"$NEW_CONFIG_NAME\" вже існує. Пропускаю."
        continue
    fi

    mkdir -p "$NEW_CONFIG_PATH/User/globalStorage"

    # Генерація нових ідентифікаторів
    NEW_MACHINE_ID=$(generate_machine_id)
    NEW_DEVICE_ID=$(generate_uuid)
    NEW_SESSION_ID=$(generate_uuid)
    NEW_SQM_ID=$(generate_uuid)

    # Зберегти machineid
    echo "$NEW_MACHINE_ID" > "$NEW_CONFIG_PATH/machineid"
    echo "  ✓ machineid збережено"

    # Зберегти storage.json
    cat > "$NEW_CONFIG_PATH/storage.json" << EOF
{
  "telemetry.machineId": "$(generate_machine_id)",
  "telemetry.macMachineId": "$(generate_machine_id)",
  "telemetry.devDeviceId": "$NEW_DEVICE_ID",
  "telemetry.sqmId": "{$NEW_SQM_ID}",
  "install.time": "$(date +%s)000",
  "sessionId": "$NEW_SESSION_ID"
}
EOF
    echo "  ✓ storage.json збережено"

    # Зберегти User/globalStorage/storage.json (якщо потрібно, з новими ID)
    cat > "$NEW_CONFIG_PATH/User/globalStorage/storage.json" << EOF
{
  "telemetry.machineId": "$(generate_machine_id)",
  "telemetry.macMachineId": "$(generate_machine_id)",
  "telemetry.devDeviceId": "$NEW_DEVICE_ID",
  "telemetry.sqmId": "{$NEW_SQM_ID}",
  "install.time": "$(date +%s)000",
  "sessionId": "$NEW_SESSION_ID"
}
EOF
    echo "  ✓ User/globalStorage/storage.json збережено"

    # Зберегти hostname
    echo "$NEW_HOSTNAME" > "$NEW_CONFIG_PATH/hostname.txt"
    echo "  ✓ hostname.txt збережено"

    # Метадані
    cat > "$NEW_CONFIG_PATH/metadata.json" << EOF
{
  "name": "$NEW_CONFIG_NAME",
  "created": "$(date +%Y-%m-%d\ %H:%M:%S)",
  "hostname": "$NEW_HOSTNAME",
  "description": "Auto-generated Windsurf profile"
}
EOF
    echo "  ✓ metadata.json збережено"

    echo "✅ Конфігурацію \"$NEW_CONFIG_NAME\" збережено в: $NEW_CONFIG_PATH"
done

echo "\n=================================================="
echo "✅ ГЕНЕРАЦІЮ 100 КОНФІГУРАЦІЙ ЗАВЕРШЕНО УСПІШНО!"
echo "   Всі профілі знаходяться в директорії: $CONFIGS_DIR"
echo "==================================================="
