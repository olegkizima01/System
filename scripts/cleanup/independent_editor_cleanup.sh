#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🧹 INDEPENDENT EDITOR CLEANUP
#  Незалежне очищення для будь-якого редактора без залежностей
# ═══════════════════════════════════════════════════════════════

# Кольори
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Функції
print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${WHITE}$1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[$1/$2]${NC} $3"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Генерація ідентифікаторів
generate_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

generate_machine_id() {
    openssl rand -hex 16
}

generate_machine_id_32() {
    openssl rand -hex 32
}

# Безпечне видалення
safe_remove() {
    local target_path="$1"
    if [ -e "$target_path" ]; then
        rm -rf "$target_path" 2>/dev/null
        if [ ! -e "$target_path" ]; then
            print_success "Видалено: $(basename "$target_path")"
            return 0
        else
            print_error "НЕ вдалося видалити: $target_path"
            return 1
        fi
    fi
    return 0
}

# Очищення Keychain
cleanup_keychain() {
    local editor="$1"
    shift
    local services=("$@")
    
    print_info "Очищення Keychain для $editor..."
    for service in "${services[@]}"; do
        security delete-generic-password -s "$service" 2>/dev/null
        security delete-internet-password -s "$service" 2>/dev/null
        security delete-generic-password -l "$service" 2>/dev/null
    done
    print_success "Keychain очищено для $editor"
}

# Очищення браузерних даних
cleanup_browser_data() {
    local editor="$1"
    
    print_info "Очищення браузерних даних для $editor..."
    
    # Chrome
    if [ -d "$HOME/Library/Application Support/Google/Chrome" ]; then
        find "$HOME/Library/Application Support/Google/Chrome" -path "*/IndexedDB/*${editor}*" -exec rm -rf {} + 2>/dev/null
        find "$HOME/Library/Application Support/Google/Chrome" -path "*/Local Storage/*${editor}*" -exec rm -rf {} + 2>/dev/null
        find "$HOME/Library/Application Support/Google/Chrome" -path "*/Session Storage/*${editor}*" -exec rm -rf {} + 2>/dev/null
    fi
    
    # Safari
    find "$HOME/Library/Safari" -name "*${editor}*" -exec rm -rf {} + 2>/dev/null
    
    # Firefox
    find "$HOME/Library/Application Support/Firefox" -name "*${editor}*" -exec rm -rf {} + 2>/dev/null
    
    print_success "Браузерні дані очищено для $editor"
}

# Повне очищення редактора
cleanup_editor() {
    local editor="$1"
    local base_path="$HOME/Library/Application Support/$editor"
    local process_name="$2"
    shift 2
    local keychain_services=("$@")
    
    print_header "🧹 ОЧИЩЕННЯ $editor"
    
    # 1. Зупинка процесу
    print_step 1 6 "Зупинка $process_name..."
    pkill -f "$process_name" 2>/dev/null
    sleep 2
    
    # 2. Створення/оновлення Machine ID
    print_step 2 6 "Створення Machine ID..."
    if [ ! -d "$base_path" ]; then
        mkdir -p "$base_path"
    fi
    local new_id=$(generate_machine_id_32)
    echo "$new_id" > "$base_path/machineid"
    print_success "Machine ID створено: $new_id"
    
    # 3. Очищення Storage файлів
    print_step 3 6 "Очищення Storage файлів..."
    local storage_paths=(
        "$base_path/storage.json"
        "$base_path/User/globalStorage/storage.json"
    )
    
    for storage_path in "${storage_paths[@]}"; do
        if [ -f "$storage_path" ]; then
            local new_device_id=$(generate_uuid)
            local new_session_id=$(generate_uuid)
            local new_machine_id=$(generate_machine_id)
            local new_mac_machine_id=$(generate_machine_id)
            
            cat > "$storage_path" << EOF
{
  "telemetry.machineId": "$new_machine_id",
  "telemetry.macMachineId": "$new_mac_machine_id",
  "telemetry.devDeviceId": "$new_device_id",
  "telemetry.sqmId": "{$(generate_uuid)}",
  "install.time": "$(date +%s)000",
  "sessionId": "$new_session_id",
  "firstSessionDate": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
  "lastSessionDate": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
EOF
            print_success "Storage оновлено: $(basename "$storage_path")"
        fi
    done
    
    # 4. Видалення кешів та баз даних
    print_step 4 6 "Видалення кешів та баз даних..."
    local cache_dirs=(
        "$base_path/Cache"
        "$base_path/CachedData"
        "$base_path/CachedExtensionVSIXs"
        "$base_path/Code Cache"
        "$base_path/GPUCache"
        "$base_path/User/workspaceStorage"
        "$base_path/Local Storage"
        "$base_path/Session Storage"
        "$base_path/IndexedDB"
        "$base_path/databases"
        "$base_path/logs"
        "$base_path/Cookies"
        "$base_path/Cookies-journal"
        "$base_path/Network Persistent State"
        "$base_path/TransportSecurity"
        "$base_path/Trust Tokens"
        "$base_path/SharedStorage"
        "$base_path/WebStorage"
        "$base_path/User/globalStorage/state.vscdb"
        "$base_path/User/globalStorage/state.vscdb.backup"
    )
    
    for target_path in "${cache_dirs[@]}"; do
        safe_remove "$target_path"
    done
    
    # 5. Очищення Keychain
    print_step 5 6 "Очищення Keychain..."
    cleanup_keychain "$editor" "${keychain_services[@]}"
    
    # 6. Очищення браузерних даних
    print_step 6 6 "Очищення браузерних даних..."
    cleanup_browser_data "$editor"
    
    print_success "Очищення $editor завершено!"
}

# Головна функція
case "${1:-help}" in
    "vscode")
        cleanup_editor "Code" "Visual Studio Code" "Code" "Visual Studio Code" "com.microsoft.VSCode" "VS Code" "GitHub" "github.com" "Microsoft" "microsoft.com"
        ;;
    "cursor")
        cleanup_editor "Cursor" "Cursor" "Cursor" "cursor" "com.cursor" "Cursor Editor" "cursor.sh" "api.cursor.sh" "com.todesktop.230313mzl4w4u92"
        ;;
    "antigravity")
        cleanup_editor "Antigravity" "Antigravity" "Antigravity" "antigravity" "Google Antigravity" "google-antigravity" "antigravity.google.com" "api.antigravity.google.com" "com.google.antigravity"
        ;;
    "windsurf")
        print_warning "Windsurf cleanup пропущено (активний редактор)"
        ;;
    "all")
        cleanup_editor "Code" "Visual Studio Code" "Code" "Visual Studio Code" "com.microsoft.VSCode" "VS Code" "GitHub" "github.com" "Microsoft" "microsoft.com"
        cleanup_editor "Cursor" "Cursor" "Cursor" "cursor" "com.cursor" "Cursor Editor" "cursor.sh" "api.cursor.sh" "com.todesktop.230313mzl4w4u92"
        cleanup_editor "Antigravity" "Antigravity" "Antigravity" "antigravity" "Google Antigravity" "google-antigravity" "antigravity.google.com" "api.antigravity.google.com" "com.google.antigravity"
        ;;
    "help"|*)
        echo "Використання: $0 [vscode|cursor|antigravity|windsurf|all]"
        echo "  vscode     - Очистити VS Code"
        echo "  cursor     - Очистити Cursor"
        echo "  antigravity - Очистити Antigravity"
        echo "  windsurf   - Пропустити Windsurf (активний)"
        echo "  all        - Очистити всі редактори (крім Windsurf)"
        exit 1
        ;;
esac
