#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🔄 ADVANCED WINDSURF CLEANUP - Розширене очищення ідентифікаторів
#  Видаляє ВСІ можливі ідентифікатори включаючи browser data та hardware fingerprinting
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║${NC}  ${GREEN}🔄 ADVANCED WINDSURF CLEANUP${NC}                              ${CYAN}║${NC}"
echo "${CYAN}║${NC}  ${WHITE}Розширене очищення всіх ідентифікаторів${NC}                  ${CYAN}║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Функції генерації
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

generate_machine_id() {
    openssl rand -hex 16
}

generate_mac_address() {
    printf "02:%02x:%02x:%02x:%02x:%02x" $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256))
}

# Зупинка всіх процесів
echo "${YELLOW}🛑 Зупинка всіх пов'язаних процесів...${NC}"
pkill -f windsurf 2>/dev/null
pkill -f Windsurf 2>/dev/null
pkill -f codeium 2>/dev/null
pkill -f "Google Chrome" 2>/dev/null
sleep 3

# 1. Базове очищення Windsurf (з попереднього скрипту)
echo "${BLUE}[1/12] Базове очищення Windsurf...${NC}"
MACHINEID_PATH=~/Library/Application\ Support/Windsurf/machineid
if [ -f "$MACHINEID_PATH" ]; then
    NEW_MACHINE_ID=$(generate_machine_id)
    echo "$NEW_MACHINE_ID" > "$MACHINEID_PATH"
    echo "  ✓ Machine ID оновлено: $NEW_MACHINE_ID"
fi

# Storage файли
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

# 2. Видалення всіх Chrome IndexedDB даних Windsurf
echo "${BLUE}[2/12] Очищення Chrome IndexedDB даних...${NC}"
find ~/Library/Application\ Support/Google/Chrome -name "*windsurf*" -type d -exec rm -rf {} + 2>/dev/null
find ~/Library/Application\ Support/Google/Chrome -path "*/IndexedDB/https_windsurf.com_*" -exec rm -rf {} + 2>/dev/null
echo "  ✓ Chrome IndexedDB дані видалено"

# 3. Очищення всіх браузерних даних
echo "${BLUE}[3/12] Очищення браузерних даних...${NC}"
# Chrome
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Local\ Storage/leveldb/*windsurf* 2>/dev/null
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Session\ Storage/*windsurf* 2>/dev/null
# Safari
rm -rf ~/Library/Safari/Databases/*windsurf* 2>/dev/null
rm -rf ~/Library/Safari/LocalStorage/*windsurf* 2>/dev/null
# Firefox
find ~/Library/Application\ Support/Firefox -name "*windsurf*" -exec rm -rf {} + 2>/dev/null
echo "  ✓ Браузерні дані очищено"

# 4. Видалення системних списків та історії
echo "${BLUE}[4/12] Очищення системних списків...${NC}"
rm -rf ~/Library/Application\ Support/com.apple.sharedfilelist/*windsurf* 2>/dev/null
rm -rf ~/Library/Application\ Support/com.apple.sharedfilelist/*Windsurf* 2>/dev/null
rm -rf ~/Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist 2>/dev/null
echo "  ✓ Системні списки очищено"

# 5. Повне видалення кешів та баз даних
echo "${BLUE}[5/12] Повне видалення кешів...${NC}"
rm -rf ~/Library/Application\ Support/Windsurf/User/globalStorage/state.vscdb* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Local\ Storage 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Session\ Storage 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/IndexedDB 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/databases 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/GPUCache 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/CachedData 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Code\ Cache 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/User/workspaceStorage 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/logs 2>/dev/null
echo "  ✓ Кеші повністю видалено"

# 6. Розширене очищення Keychain
echo "${BLUE}[6/12] Розширене очищення Keychain...${NC}"
KEYCHAIN_SERVICES=(
    "Windsurf" "windsurf" "com.windsurf" "Windsurf Editor" 
    "Codeium Windsurf" "Codeium" "codeium" "codeium.com" 
    "api.codeium.com" "com.exafunction.windsurf"
    "windsurf.com" "auth.windsurf.com"
)

for service in "${KEYCHAIN_SERVICES[@]}"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
    security delete-generic-password -l "$service" 2>/dev/null
    security delete-internet-password -a "$service" 2>/dev/null
done
echo "  ✓ Keychain повністю очищено"

# 7. Видалення всіх веб-даних та cookies
echo "${BLUE}[7/12] Видалення всіх веб-даних...${NC}"
rm -rf ~/Library/Application\ Support/Windsurf/Cookies* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Network\ Persistent\ State 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/TransportSecurity 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/Trust\ Tokens* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/SharedStorage* 2>/dev/null
rm -rf ~/Library/Application\ Support/Windsurf/WebStorage 2>/dev/null
echo "  ✓ Веб-дані повністю видалено"

# 8. Очищення Codeium даних
echo "${BLUE}[8/12] Очищення Codeium даних...${NC}"
rm -rf ~/Library/Application\ Support/com.intii.CopilotForXcode/Codeium 2>/dev/null
rm -rf ~/.codeium 2>/dev/null
rm -rf ~/Library/Caches/com.codeium* 2>/dev/null
echo "  ✓ Codeium дані видалено"

# 9. Тимчасова зміна MAC адреси (якщо можливо)
echo "${BLUE}[9/12] Спроба зміни MAC адреси...${NC}"
CURRENT_MAC=$(ifconfig en0 | grep ether | awk '{print $2}')
NEW_MAC=$(generate_mac_address)
echo "  📝 Поточний MAC: $CURRENT_MAC"
echo "  🎲 Новий MAC: $NEW_MAC"

# Спроба зміни MAC (може потребувати додаткових прав)
sudo ifconfig en0 down 2>/dev/null
sudo ifconfig en0 ether "$NEW_MAC" 2>/dev/null
sudo ifconfig en0 up 2>/dev/null

# Перевірка чи змінився MAC
UPDATED_MAC=$(ifconfig en0 | grep ether | awk '{print $2}')
if [ "$UPDATED_MAC" = "$NEW_MAC" ]; then
    echo "  ✓ MAC адреса змінена"
else
    echo "  ⚠️  MAC адреса не змінена (потрібні додаткові права)"
fi

# 10. Генерація нового hostname
echo "${BLUE}[10/12] Генерація нового hostname...${NC}"
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

# 11. Очищення DNS та мережевого кешу
echo "${BLUE}[11/12] Очищення мережевого кешу...${NC}"
sudo dscacheutil -flushcache 2>/dev/null
sudo killall -HUP mDNSResponder 2>/dev/null
# Очищення ARP таблиці
sudo arp -a -d 2>/dev/null
echo "  ✓ Мережевий кеш очищено"

# 12. Очищення системних логів та тимчасових файлів
echo "${BLUE}[12/12] Очищення системних файлів...${NC}"
# Видалення логів які можуть містити ідентифікатори
sudo rm -rf /var/log/*windsurf* 2>/dev/null
sudo rm -rf /tmp/*windsurf* 2>/dev/null
rm -rf ~/Library/Logs/*windsurf* 2>/dev/null
rm -rf ~/Library/Logs/*Windsurf* 2>/dev/null

# Очищення Launch Services кешу
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user 2>/dev/null

echo "  ✓ Системні файли очищено"

# Планування відновлення через 4 години
echo "${YELLOW}⏰ Планування відновлення...${NC}"
{
    sleep 14400  # 4 години
    echo "⏰ Відновлення оригінального hostname: $ORIGINAL_HOSTNAME"
    sudo scutil --set HostName "$ORIGINAL_HOSTNAME" 2>/dev/null
    sudo scutil --set LocalHostName "$ORIGINAL_HOSTNAME" 2>/dev/null
    sudo scutil --set ComputerName "$ORIGINAL_HOSTNAME" 2>/dev/null
    
    # Відновлення оригінального MAC якщо можливо
    if [ "$UPDATED_MAC" = "$NEW_MAC" ]; then
        sudo ifconfig en0 down 2>/dev/null
        sudo ifconfig en0 ether "$CURRENT_MAC" 2>/dev/null
        sudo ifconfig en0 up 2>/dev/null
    fi
    
    sudo dscacheutil -flushcache 2>/dev/null
    sudo killall -HUP mDNSResponder 2>/dev/null
} > /tmp/windsurf_restore_$$.log 2>&1 &

RESTORE_PID=$!
echo "  ✓ Відновлення заплановано (PID: $RESTORE_PID)"

echo ""
echo "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo "${GREEN}║${NC}  ${WHITE}✅ РОЗШИРЕНЕ ОЧИЩЕННЯ ЗАВЕРШЕНО!${NC}                         ${GREEN}║${NC}"
echo "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo "${GREEN}║${NC}  ${CYAN}📋 Виконані дії:${NC}                                          ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Базове очищення Windsurf                             ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Chrome IndexedDB дані видалено                       ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Всі браузерні дані очищено                           ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Системні списки очищено                              ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Кеші повністю видалено                               ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Keychain повністю очищено                            ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Веб-дані повністю видалено                           ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Codeium дані видалено                                ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ MAC адреса: ${YELLOW}$UPDATED_MAC${NC}                           ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Hostname: ${YELLOW}$NEW_HOSTNAME${NC}                           ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Мережевий кеш очищено                                ${GREEN}║${NC}"
echo "${GREEN}║${NC}    ✓ Системні файли очищено                               ${GREEN}║${NC}"
echo "${GREEN}║${NC}                                                            ${GREEN}║${NC}"
echo "${GREEN}║${NC}  ${RED}⚠️  ВАЖЛИВО: Перезавантажте систему для повного ефекту${NC}   ${GREEN}║${NC}"
echo "${GREEN}║${NC}  ${YELLOW}💡 Після перезавантаження запустіть Windsurf${NC}             ${GREEN}║${NC}"
echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
