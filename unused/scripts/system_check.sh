#!/bin/zsh

# Кольори
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║${NC}  ${GREEN}🔍 SYSTEM INTEGRITY CHECK - Deep Cleanup System v3.0${NC}  ${CYAN}║${NC}"
echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TOTAL=0
PASSED=0
FAILED=0

check_file() {
    local file=$1
    local desc=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$file" ]; then
        echo "${GREEN}✅${NC} $desc"
        PASSED=$((PASSED + 1))
    else
        echo "${RED}❌${NC} $desc - NOT FOUND: $file"
        FAILED=$((FAILED + 1))
    fi
}

check_dir() {
    local dir=$1
    local desc=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -d "$dir" ]; then
        echo "${GREEN}✅${NC} $desc"
        PASSED=$((PASSED + 1))
    else
        echo "${YELLOW}⚠️${NC}  $desc - NOT FOUND: $dir"
        FAILED=$((FAILED + 1))
    fi
}

check_executable() {
    local file=$1
    local desc=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -x "$file" ]; then
        echo "${GREEN}✅${NC} $desc"
        PASSED=$((PASSED + 1))
    else
        echo "${RED}❌${NC} $desc - NOT EXECUTABLE: $file"
        FAILED=$((FAILED + 1))
    fi
}

echo "${CYAN}[1/7] Перевірка Windsurf System...${NC}"
check_executable "deep_windsurf_cleanup.sh" "Windsurf cleanup script"
check_executable "restore_windsurf_backup.sh" "Windsurf restore script"
check_executable "check_windsurf_backup.sh" "Windsurf check script"
check_executable "manage_configs.sh" "Windsurf manage script"
check_file ".windsurf_aliases" "Windsurf aliases"
check_file "Windsurf-darwin-arm64-1.12.5.dmg" "Windsurf DMG file"
echo ""

echo "${CYAN}[2/7] Перевірка VS Code System...${NC}"
check_executable "deep_vscode_cleanup.sh" "VS Code cleanup script"
check_executable "restore_vscode_backup.sh" "VS Code restore script"
check_executable "check_vscode_backup.sh" "VS Code check script"
check_executable "manage_vscode_configs.sh" "VS Code manage script"
check_file ".vscode_aliases" "VS Code aliases"
echo ""

echo "${CYAN}[3/7] Перевірка Interactive Menu...${NC}"
check_executable "main_menu.sh" "Main interactive menu"
echo ""

echo "${CYAN}[4/7] Перевірка Web Interface...${NC}"
check_dir "web_interface" "Web interface directory"
check_file "web_interface/server.py" "Web server (Python)"
check_file "web_interface/templates/index.html" "HTML template"
check_file "web_interface/static/style.css" "CSS stylesheet"
check_file "web_interface/static/script.js" "JavaScript file"
echo ""

echo "${CYAN}[5/7] Перевірка History System...${NC}"
check_executable "history_tracker.sh" "History tracker script"
echo ""

echo "${CYAN}[6/7] Перевірка Documentation...${NC}"
check_file "README.md" "Main README"
check_file "README_VSCODE.md" "VS Code README"
check_file "WEB_INTERFACE_README.md" "Web Interface README"
check_file "QUICK_START.md" "Quick Start Guide"
check_file "FINAL_SUMMARY.md" "Final Summary"
check_file "CHANGELOG_V3.md" "Changelog v3.0"
check_file "SUMMARY_V3.txt" "Summary v3.0"
check_file "FILES_LIST.md" "Files List"
echo ""

echo "${CYAN}[7/7] Перевірка Utilities...${NC}"
check_executable "check_api_traces.sh" "API traces checker"
check_executable "start.sh" "Start script"
check_file "SECURITY.md" "Security guide"
check_file "WORKFLOW.md" "Workflow guide"
echo ""

echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo "${CYAN}                    РЕЗУЛЬТАТИ ПЕРЕВІРКИ${NC}"
echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Всього перевірок: ${CYAN}$TOTAL${NC}"
echo "  ${GREEN}Успішно: $PASSED${NC}"
echo "  ${RED}Помилок: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "${GREEN}✅ ВСІ ПЕРЕВІРКИ ПРОЙДЕНО УСПІШНО!${NC}"
    echo "${GREEN}🎉 Система повністю готова до використання!${NC}"
    echo ""
    echo "${CYAN}Швидкий старт:${NC}"
    echo "  ${YELLOW}./main_menu.sh${NC}           - Головне меню"
    echo "  ${YELLOW}./deep_windsurf_cleanup.sh${NC} - Windsurf cleanup"
    echo "  ${YELLOW}./deep_vscode_cleanup.sh${NC}   - VS Code cleanup"
    echo "  ${YELLOW}cd web_interface && python3 server.py${NC} - Web interface"
    exit 0
else
    echo "${RED}❌ ЗНАЙДЕНО ПОМИЛОК: $FAILED${NC}"
    echo "${YELLOW}💡 Деякі файли відсутні або не мають прав на виконання${NC}"
    echo ""
    echo "${CYAN}Рекомендації:${NC}"
    echo "  1. Перевірте що всі файли на місці"
    echo "  2. Надайте права на виконання: ${YELLOW}chmod +x *.sh${NC}"
    echo "  3. Перевірте DMG файл для Windsurf"
    exit 1
fi
