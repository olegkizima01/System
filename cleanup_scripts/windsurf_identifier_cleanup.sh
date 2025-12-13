#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🔄 WINDSURF IDENTIFIER CLEANUP - Повне очищення ідентифікаторів
#  Видаляє всі ідентифікатори для обходу обмежень облікового запису
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
if [ ! -f "$REPO_ROOT/cleanup_modules.json" ] && [ -f "$SCRIPT_DIR/../cleanup_modules.json" ]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

# Завантаження змінних середовища
ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# Режими виконання
AUTO_YES="${AUTO_YES:-1}"
UNSAFE_MODE="${UNSAFE_MODE:-0}"

# SUDO_ASKPASS
SUDO_HELPER="$REPO_ROOT/cleanup_scripts/sudo_helper.sh"
if [ ! -f "$SUDO_HELPER" ] && [ -f "$REPO_ROOT/sudo_helper.sh" ]; then
    SUDO_HELPER="$REPO_ROOT/sudo_helper.sh"
fi
export SUDO_ASKPASS="$SUDO_HELPER"
chmod +x "$SUDO_ASKPASS" 2>/dev/null
sudo() { command sudo -A "$@"; }

if [ "${UNSAFE_MODE}" != "1" ]; then
    echo "\n🛡️  SAFE_MODE: windsurf_identifier_cleanup вимкнено. Увімкніть UNSAFE_MODE=1 якщо потрібно."
    exit 0
fi

# Перевірка sudo доступу (неінтерактивно через SUDO_ASKPASS)
sudo -v 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Помилка: не вдалося отримати sudo права. Перевірте SUDO_PASSWORD у .env"
    exit 1
fi

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║${NC}  ${GREEN}🔄 WINDSURF IDENTIFIER CLEANUP${NC}                            ${CYAN}║${NC}"
echo "${CYAN}║${NC}  ${WHITE}Повне очищення ідентифікаторів для обходу лімітів${NC}        ${CYAN}║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Функція для генерації випадкового UUID
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

# Функція для генерації випадкового machine-id (hex формат)
generate_machine_id() {
    openssl rand -hex 16
}

# Зупинка Windsurf якщо запущений
echo "${YELLOW}🛑 Зупинка Windsurf...${NC}"
pkill -f windsurf 2>/dev/null
pkill -f Windsurf 2>/dev/null
sleep 2

# 1. Очищення Machine ID
echo "${BLUE}[1/8] Очищення Machine ID...${NC}"
MACHINEID_PATH=~/Library/Application\ Support/Windsurf/machineid
if [ -f "$MACHINEID_PATH" ]; then
    NEW_MACHINE_ID=$(generate_machine_id)
    echo "$NEW_MACHINE_ID" > "$MACHINEID_PATH"
    echo "  ✓ Machine ID оновлено: $NEW_MACHINE_ID"
else
    echo "  ℹ️  Machine ID файл не знайдено"
fi

# 2. Очищення Storage файлів
echo "${BLUE}[2/8] Очищення Storage файлів...${NC}"
STORAGE_PATHS=(
    ~/Library/Application\ Support/Windsurf/storage.json
    ~/Library/Application\ Support/Windsurf/User/globalStorage/storage.json
)

for STORAGE_PATH in "${STORAGE_PATHS[@]}"; do
    if [ -f "$STORAGE_PATH" ]; then
        NEW_DEVICE_ID=$(generate_uuid)
        NEW_SESSION_ID=$(generate_uuid)
        NEW_MACHINE_ID_TELEMETRY=$(generate_machine_id)
        NEW_MAC_MACHINE_ID=$(generate_machine_id)
        
        cat > "$STORAGE_PATH" << EOF
{
  "telemetry.machineId": "$NEW_MACHINE_ID_TELEMETRY",
  "telemetry.macMachineId": "$NEW_MAC_MACHINE_ID",
  "telemetry.devDeviceId": "$NEW_DEVICE_ID",
  "telemetry.sqmId": "{$(generate_uuid)}",
  "install.time": "$(date +%s)000",
  "sessionId": "$NEW_SESSION_ID",
  "firstSessionDate": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "lastSessionDate": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
EOF
        echo "  ✓ Storage оновлено: $(basename "$STORAGE_PATH")"
    fi
done

# 3. Видалення кешів та баз даних
echo "${BLUE}[3/8] Видалення кешів та баз даних...${NC}"
rm -rf ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Local\ Storage 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Session\ Storage 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/IndexedDB 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/databases 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/GPUCache 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/CachedData 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Code\ Cache 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/User/workspaceStorage 2>/dev/null
echo "  ✓ Кеші та бази даних видалено"

# 4. Очищення Keychain
echo "${BLUE}[4/8] Очищення Keychain...${NC}"
for service in "Windsurf" "windsurf" "com.windsurf" "Windsurf Editor" "Codeium Windsurf" "Codeium" "codeium" "codeium.com" "api.codeium.com"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
    security delete-generic-password -l "$service" 2>/dev/null
done
echo "  ✓ Keychain очищено"

# 5. Видалення cookies та веб-даних
echo "${BLUE}[5/8] Видалення cookies та веб-даних...${NC}"
rm -rf ~/Library/Application\ Support/Windsurf/Cookies* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Network\ Persistent\ State 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/TransportSecurity 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Trust\ Tokens* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/SharedStorage* 2>/dev/null
echo "  ✓ Cookies та веб-дані видалено"

# 6. Генерація нового hostname (тимчасово)
echo "${BLUE}[6/8] Генерація нового hostname...${NC}"
REAL_NAMES=("Alex" "James" "Michael" "David" "Robert" "John" "Richard" "Charles" "Daniel" "Matthew" "Anthony" "Mark" "Emma" "Olivia" "Ava" "Sophia" "Isabella" "Mia" "Charlotte" "Amelia")
PLACE_NAMES=("Studio" "Office" "Desktop" "Workspace" "MacBook" "iMac" "MacStudio" "Pro" "Air" "Mini")

RANDOM_NAME=${REAL_NAMES[$((RANDOM % ${#REAL_NAMES[@]}))]}
RANDOM_PLACE=${PLACE_NAMES[$((RANDOM % ${#PLACE_NAMES[@]}))]}
NEW_HOSTNAME="${RANDOM_NAME}-${RANDOM_PLACE}"

ORIGINAL_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "Unknown")
echo "  📝 Оригінальний hostname: $ORIGINAL_HOSTNAME"
echo "  🎲 Новий hostname: $NEW_HOSTNAME"

sudo scutil --set HostName "$NEW_HOSTNAME" 2>/dev/null
sudo scutil --set LocalHostName "$NEW_HOSTNAME" 2>/dev/null
sudo scutil --set ComputerName "$NEW_HOSTNAME" 2>/dev/null

# 7. Очищення DNS кешу
echo "${BLUE}[7/8] Очищення DNS кешу...${NC}"
sudo dscacheutil -flushcache 2>/dev/null
sudo killall -HUP mDNSResponder 2>/dev/null
echo "  ✓ DNS кеш очищено"

# 8. Планування відновлення hostname через 4 години
echo "${BLUE}[8/8] Планування відновлення hostname...${NC}"
{
    sleep 14400  # 4 години
    echo "⏰ Відновлення оригінального hostname: $ORIGINAL_HOSTNAME"
    sudo scutil --set HostName "$ORIGINAL_HOSTNAME" 2>/dev/null
    sudo scutil --set LocalHostName "$ORIGINAL_HOSTNAME" 2>/dev/null
    sudo scutil --set ComputerName "$ORIGINAL_HOSTNAME" 2>/dev/null
    sudo dscacheutil -flushcache 2>/dev/null
    sudo killall -HUP mDNSResponder 2>/dev/null
} > /tmp/windsurf_hostname_restore_$$.log 2>&1 &

RESTORE_PID=$!
echo "  ✓ Відновлення заплановано (PID: $RESTORE_PID)"
echo "  ⏰ Hostname буде відновлено через 4 години"

echo ""
echo "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║${NC}  ${WHITE}✅ ОЧИЩЕННЯ ІДЕНТИФІКАТОРІВ ЗАВЕРШЕНО!${NC}                    ${GREEN}║${NC}"
echo "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo "${GREEN}║${NC}  ${CYAN}📋 Виконані дії:${NC}                                          ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Machine ID оновлено                                  ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Storage файли оновлено                               ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Кеші та бази даних видалено                          ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Keychain очищено                                     ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Cookies та веб-дані видалено                         ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Hostname змінено на: ${YELLOW}$NEW_HOSTNAME${NC}                    ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ DNS кеш очищено                                      ${GREEN}║${NC}"
echo "${GREEN}║${NC}                                                            ${GREEN}║${NC}"
echo "${GREEN}║${NC}  ${YELLOW}💡 Тепер можна запускати Windsurf як новий користувач${NC}     ${GREEN}║${NC}"
echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
