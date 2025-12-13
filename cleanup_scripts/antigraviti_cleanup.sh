#!/bin/zsh

setopt NULL_GLOB

# ═══════════════════════════════════════════════════════════════
#  🛰  ANTIGRAVITY EDITOR CLEANUP - Очищення ідентифікаторів Google Antigravity
#  Видаляє ВСІ можливі ідентифікатори та дані для Google Antigravity редактора
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
echo "${CYAN}║${NC}  ${GREEN}🛰  ANTIGRAVITY EDITOR CLEANUP${NC}                            ${CYAN}║${NC}"
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
echo "${YELLOW}🛑 Зупинка всіх пов'язаних процесів Antigravity...${NC}"
pkill -f antigravity 2>/dev/null
pkill -f Antigravity 2>/dev/null
pkill -f "Google Chrome" 2>/dev/null
sleep 2

# 1. Очищення основних директорій та додатку Antigravity
echo "${BLUE}[1/10] Очищення основних директорій Antigravity...${NC}"

# Видалення основного додатку (якщо існує)
ANTIGRAVITY_APPS=(
    /Applications/Antigravity.app
    /Applications/Google\ Antigravity.app
    "$HOME"/Applications/Antigravity.app
)

for app in "${ANTIGRAVITY_APPS[@]}"; do
    if [ -e "$app" ]; then
        rm -rf "$app" 2>/dev/null
        echo "  ✓ Видалено додаток: $(basename "$app")"
    fi
done

ANTIGRAVITY_PATHS=(
    ~/Library/Application\ Support/Antigravity
    ~/Library/Application\ Support/Google/Antigravity
    ~/Library/Caches/Antigravity
    ~/Library/Caches/Google/Antigravity
    ~/Library/Preferences/com.google.antigravity*
    ~/Library/Saved\ Application\ State/com.google.antigravity*
    ~/Library/Preferences/ByHost/*antigravity*
    ~/Library/Containers/*antigravity*
    ~/Library/Group\ Containers/*antigravity*
    ~/Library/Application\ Scripts/*antigravity*
    ~/Library/HTTPStorages/*antigravity*
    ~/Library/WebKit/*antigravity*
)

for path in "${ANTIGRAVITY_PATHS[@]}"; do
    if [ -e "$path" ]; then
        rm -rf "$path" 2>/dev/null
        echo "  ✓ Видалено: $(basename "$path")"
    fi
done

# 2. Очищення Chrome IndexedDB даних для Antigravity
echo "${BLUE}[2/10] Очищення Chrome IndexedDB даних...${NC}"
find ~/Library/Application\ Support/Google/Chrome -path "*/IndexedDB/*antigravity*" -exec rm -rf {} + 2>/dev/null
find ~/Library/Application\ Support/Google/Chrome -path "*/IndexedDB/*google*" -name "*antigravity*" -exec rm -rf {} + 2>/dev/null
echo "  ✓ Chrome IndexedDB дані видалено"

# 3. Очищення браузерних даних
echo "${BLUE}[3/10] Очищення браузерних даних...${NC}"
# Chrome Local Storage
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Local\ Storage/leveldb/*antigravity* 2>/dev/null
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Local\ Storage/*antigravity* 2>/dev/null
# Chrome Session Storage
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Session\ Storage/*antigravity* 2>/dev/null
# Safari
rm -rf ~/Library/Safari/Databases/*antigravity* 2>/dev/null
rm -rf ~/Library/Safari/LocalStorage/*antigravity* 2>/dev/null
# Firefox
find ~/Library/Application\ Support/Firefox -name "*antigravity*" -exec rm -rf {} + 2>/dev/null
echo "  ✓ Браузерні дані очищено"

# 4. Очищення Cookies та Site Data
echo "${BLUE}[4/10] Очищення Cookies та Site Data...${NC}"
# Chrome Cookies
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Cookies* 2>/dev/null
# Chrome Web Data
rm -rf ~/Library/Application\ Support/Google/Chrome/*/Web\ Data* 2>/dev/null
echo "  ✓ Cookies та Site Data очищено"

# 5. Очищення кешу браузера
echo "${BLUE}[5/10] Очищення кешу браузера...${NC}"
rm -rf ~/Library/Caches/Google/Chrome 2>/dev/null
rm -rf ~/Library/Caches/Firefox 2>/dev/null
rm -rf ~/Library/Safari/History.db* 2>/dev/null
echo "  ✓ Кеш браузера очищено"

# 6. Очищення Google-пов'язаних даних
echo "${BLUE}[6/10] Очищення Google-пов'язаних даних...${NC}"
rm -rf ~/Library/Application\ Support/Google 2>/dev/null
rm -rf ~/Library/Caches/Google 2>/dev/null
rm -rf ~/Library/Preferences/com.google* 2>/dev/null
echo "  ✓ Google-дані очищено"

# 7. Очищення API ключів та токенів з Keychain
echo "${BLUE}[7/10] Видалення API ключів та токенів з Keychain...${NC}"
for service in "Antigravity" "antigravity" "Google Antigravity" "google-antigravity" "antigravity.google.com" "api.antigravity.google.com"; do
    security delete-generic-password -s "$service" 2>/dev/null
    security delete-internet-password -s "$service" 2>/dev/null
    security delete-generic-password -l "$service" 2>/dev/null
done
echo "  ✓ API ключі та токени очищено"

# 8. Очищення системних логів та історії
echo "${BLUE}[8/10] Очищення системних логів та історії...${NC}"
rm -rf ~/Library/Logs/Antigravity* 2>/dev/null
rm -rf ~/Library/Logs/Google* 2>/dev/null
# Очищення bash/zsh історії для antigravity команд
sed -i '' '/antigravity/d' ~/.bash_history 2>/dev/null
sed -i '' '/antigravity/d' ~/.zsh_history 2>/dev/null
sed -i '' '/Antigravity/d' ~/.bash_history 2>/dev/null
sed -i '' '/Antigravity/d' ~/.zsh_history 2>/dev/null
echo "  ✓ Логи та історія очищено"

# 9. Очищення тимчасових файлів
echo "${BLUE}[9/10] Очищення тимчасових файлів...${NC}"
rm -rf /tmp/*antigravity* 2>/dev/null
rm -rf /var/tmp/*antigravity* 2>/dev/null
rm -rf ~/Library/Application\ Support/CrashReporter/*antigravity* 2>/dev/null
echo "  ✓ Тимчасові файли очищено"

# 10. Перевірка та звіт
echo "${BLUE}[10/10] Перевірка результатів очищення...${NC}"
echo ""
echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo "${WHITE}📊 ЗВІТ ОЧИЩЕННЯ ANTIGRAVITY EDITOR:${NC}"
echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

REMAINING_ANTIGRAVITY_PATHS=$(find ~/Library -name "*antigravity*" -o -name "*Antigravity*" 2>/dev/null)

if [ -n "$REMAINING_ANTIGRAVITY_PATHS" ]; then
    echo "${YELLOW}⚠️  Знайдено залишкові файли/папки Antigravity у ~/Library. Видаляю:${NC}"
    echo "$REMAINING_ANTIGRAVITY_PATHS"
    echo "$REMAINING_ANTIGRAVITY_PATHS" | while read -r path; do
        [ -n "$path" ] && rm -rf "$path" 2>/dev/null
    done
fi

REMAINING_ANTIGRAVITY=$(find ~/Library -name "*antigravity*" -o -name "*Antigravity*" 2>/dev/null | wc -l)
REMAINING_GOOGLE=$(find ~/Library/Application\ Support -name "*Google*" 2>/dev/null | wc -l)

if [ "$REMAINING_ANTIGRAVITY" -eq 0 ]; then
    echo "${GREEN}✅ Antigravity ідентифікатори: ОЧИЩЕНО${NC}"
else
    echo "${YELLOW}⚠️  Antigravity ідентифікатори: Знайдено $REMAINING_ANTIGRAVITY залишків${NC}"
fi

if [ "$REMAINING_GOOGLE" -lt 5 ]; then
    echo "${GREEN}✅ Google-дані: ОЧИЩЕНО${NC}"
else
    echo "${YELLOW}⚠️  Google-дані: Знайдено $REMAINING_GOOGLE залишків${NC}"
fi

# Перевірка Keychain
KEYCHAIN_ANTIGRAVITY=$(security find-generic-password -s "Antigravity" 2>/dev/null | wc -l)
if [ "$KEYCHAIN_ANTIGRAVITY" -eq 0 ]; then
    echo "${GREEN}✅ Keychain: ОЧИЩЕНО${NC}"
else
    echo "${YELLOW}⚠️  Keychain: Знайдено записи${NC}"
fi

echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "${GREEN}✅ Очищення Antigravity Editor завершено!${NC}"
echo ""
