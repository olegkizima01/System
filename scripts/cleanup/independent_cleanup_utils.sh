#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🔧 INDEPENDENT CLEANUP UTILITIES
#  Створює Machine-ID файли для всіх редакторів незалежно
# ═══════════════════════════════════════════════════════════════

# Кольори
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функції
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Генерація ідентифікаторів
generate_machine_id_32() {
    openssl rand -hex 32
}

# Створення Machine-ID для всіх редакторів
create_all_machine_ids() {
    echo "Створення Machine-ID файлів для всіх редакторів..."
    
    # Windsurf
    WINDSURF_BASE="$HOME/Library/Application Support/Windsurf"
    if [ ! -d "$WINDSURF_BASE" ]; then
        mkdir -p "$WINDSURF_BASE"
    fi
    WINDSURF_ID=$(generate_machine_id_32)
    echo "$WINDSURF_ID" > "$WINDSURF_BASE/machineid"
    print_success "Windsurf Machine-ID створено"
    
    # VS Code
    VSCODE_BASE="$HOME/Library/Application Support/Code"
    if [ ! -d "$VSCODE_BASE" ]; then
        mkdir -p "$VSCODE_BASE"
    fi
    VSCODE_ID=$(generate_machine_id_32)
    echo "$VSCODE_ID" > "$VSCODE_BASE/machineid"
    print_success "VS Code Machine-ID створено"
    
    # Cursor
    CURSOR_BASE="$HOME/Library/Application Support/Cursor"
    if [ ! -d "$CURSOR_BASE" ]; then
        mkdir -p "$CURSOR_BASE"
    fi
    CURSOR_ID=$(generate_machine_id_32)
    echo "$CURSOR_ID" > "$CURSOR_BASE/machineid"
    print_success "Cursor Machine-ID створено"
    
    # Antigravity
    ANTIGRAVITY_BASE="$HOME/Library/Application Support/Antigravity"
    if [ ! -d "$ANTIGRAVITY_BASE" ]; then
        mkdir -p "$ANTIGRAVITY_BASE"
    fi
    ANTIGRAVITY_ID=$(generate_machine_id_32)
    echo "$ANTIGRAVITY_ID" > "$ANTIGRAVITY_BASE/machineid"
    print_success "Antigravity Machine-ID створено"
    
    echo ""
    print_info "Всі Machine-ID файли створено успішно!"
}

# Перевірка існуючих Machine-ID
check_machine_ids() {
    echo "Перевірка Machine-ID файлів..."
    
    local editors=("Windsurf" "Code" "Cursor" "Antigravity")
    local found=0
    local missing=0
    
    for editor in "${editors[@]}"; do
        base_path="$HOME/Library/Application Support/$editor"
        machineid_path="$base_path/machineid"
        
        if [ -f "$machineid_path" ]; then
            id_length=$(wc -c < "$machineid_path" | tr -d ' ')
            if [ "$id_length" -ge 32 ]; then
                print_success "$editor: Machine-ID існує (${id_length} символів)"
                ((found++))
            else
                print_error "$editor: Machine-ID занадто короткий (${id_length} символів)"
                ((missing++))
            fi
        else
            print_error "$editor: Machine-ID відсутній"
            ((missing++))
        fi
    done
    
    echo ""
    if [ $missing -eq 0 ]; then
        print_success "Всі Machine-ID файли в порядку!"
    else
        print_error "$missing файлів відсутні або пошкоджені"
    fi
}

# Головна функція
case "${1:-check}" in
    "create")
        create_all_machine_ids
        ;;
    "check")
        check_machine_ids
        ;;
    "fix")
        create_all_machine_ids
        check_machine_ids
        ;;
    *)
        echo "Використання: $0 [create|check|fix]"
        echo "  create - Створити Machine-ID для всіх редакторів"
        echo "  check  - Перевірити існуючі Machine-ID"
        echo "  fix    - Створити та перевірити Machine-ID"
        exit 1
        ;;
esac
