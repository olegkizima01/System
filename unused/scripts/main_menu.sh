#!/bin/zsh

# Кольори для терміналу
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Функція для очищення екрану
clear_screen() {
    clear
}

# Функція для виведення заголовку
print_header() {
    clear_screen
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${BOLD}${GREEN}⚡ DEEP CLEANUP SYSTEM - MASTER CONTROL PANEL ⚡${NC}      ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Версія: 3.0${NC}                    ${WHITE}Status: ${GREEN}ACTIVE${NC}          ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Функція для виведення меню
print_main_menu() {
    print_header
    echo "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo "${YELLOW}│${NC}  ${BOLD}ОБЕРІТЬ СИСТЕМУ:${NC}                                          ${YELLOW}│${NC}"
    echo "${YELLOW}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[1]${NC} 🌊 ${CYAN}Windsurf System${NC}                                  ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[2]${NC} 💻 ${BLUE}VS Code System${NC}                                   ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[3]${NC} 🌐 ${MAGENTA}Web Interface${NC} (Hacker Dashboard)                 ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[4]${NC} 📊 ${WHITE}System Status${NC}                                    ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[5]${NC} 📚 ${WHITE}Documentation${NC}                                    ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[0]${NC} ❌ ${RED}Exit${NC}                                             ${YELLOW}│${NC}"
    echo "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
}

# Меню Windsurf
windsurf_menu() {
    while true; do
        print_header
        echo "${CYAN}┌─────────────────────────────────────────────────────────────┐${NC}"
        echo "${CYAN}│${NC}  ${BOLD}🌊 WINDSURF SYSTEM${NC}                                       ${CYAN}│${NC}"
        echo "${CYAN}├─────────────────────────────────────────────────────────────┤${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[1]${NC} 🧹 ${WHITE}Full Cleanup + Auto Install${NC}                     ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[2]${NC} 🔄 ${WHITE}Restore from Backup${NC}                             ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[3]${NC} 📊 ${WHITE}Check Status${NC}                                    ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[4]${NC} 🔧 ${WHITE}Manage Profiles${NC}                                 ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[5]${NC} 📦 ${WHITE}Backup Manager${NC}                                  ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[6]${NC} 🔍 ${WHITE}Check API Traces${NC}                                ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${GREEN}[7]${NC} 🚀 ${RED}Advanced ID Cleanup${NC} (Account Limits Fix)         ${CYAN}│${NC}"
        echo "${CYAN}│${NC}  ${RED}[0]${NC} ⬅️  ${RED}Back to Main Menu${NC}                               ${CYAN}│${NC}"
        echo "${CYAN}└─────────────────────────────────────────────────────────────┘${NC}"
        echo ""
        echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
        read choice
        
        case $choice in
            1)
                echo "\n${GREEN}🚀 Запуск повного очищення Windsurf...${NC}"
                sleep 1
                ./deep_windsurf_cleanup.sh
                echo "\n${GREEN}✅ Процес завершено!${NC}"
                echo "${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            2)
                echo "\n${BLUE}🔄 Відновлення з бекапу...${NC}"
                sleep 1
                ./restore_windsurf_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            3)
                echo "\n${CYAN}📊 Перевірка статусу...${NC}"
                sleep 1
                ./check_windsurf_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            4)
                echo "\n${MAGENTA}🔧 Управління профілями...${NC}"
                sleep 1
                ./manage_configs.sh
                ;;
            5)
                echo "\n${BLUE}📦 Менеджер бекапів...${NC}"
                sleep 1
                ./check_windsurf_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            6)
                echo "\n${YELLOW}🔍 Перевірка API слідів...${NC}"
                sleep 1
                ./check_api_traces.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            7)
                echo "\n${RED}🚀 Запуск розширеного очищення ідентифікаторів...${NC}"
                echo "${YELLOW}⚠️  Після завершення потрібне перезавантаження macOS!${NC}"
                sleep 2
                if [ -f "./advanced_windsurf_cleanup.sh" ]; then
                    ./advanced_windsurf_cleanup.sh
                    echo "\n${GREEN}✅ Розширене очищення завершено!${NC}"
                    echo "${RED}🔄 ОБОВ'ЯЗКОВО перезавантажте macOS для повного ефекту!${NC}"
                else
                    echo "${RED}❌ advanced_windsurf_cleanup.sh не знайдено!${NC}"
                fi
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            0)
                return
                ;;
            *)
                echo "${RED}❌ Невірний вибір!${NC}"
                sleep 1
                ;;
        esac
    done
}

# Меню VS Code
vscode_menu() {
    while true; do
        print_header
        echo "${BLUE}┌─────────────────────────────────────────────────────────────┐${NC}"
        echo "${BLUE}│${NC}  ${BOLD}💻 VS CODE SYSTEM${NC}                                        ${BLUE}│${NC}"
        echo "${BLUE}├─────────────────────────────────────────────────────────────┤${NC}"
        echo "${BLUE}│${NC}  ${GREEN}[1]${NC} 🧹 ${WHITE}Full Cleanup${NC}                                     ${BLUE}│${NC}"
        echo "${BLUE}│${NC}  ${GREEN}[2]${NC} 🔄 ${WHITE}Restore from Backup${NC}                             ${BLUE}│${NC}"
        echo "${BLUE}│${NC}  ${GREEN}[3]${NC} 📊 ${WHITE}Check Status${NC}                                    ${BLUE}│${NC}"
        echo "${BLUE}│${NC}  ${GREEN}[4]${NC} 🔧 ${WHITE}Manage Profiles${NC}                                 ${BLUE}│${NC}"
        echo "${BLUE}│${NC}  ${GREEN}[5]${NC} 📦 ${WHITE}Backup Manager${NC}                                  ${BLUE}│${NC}"
        echo "${BLUE}│${NC}  ${RED}[0]${NC} ⬅️  ${RED}Back to Main Menu${NC}                               ${BLUE}│${NC}"
        echo "${BLUE}└─────────────────────────────────────────────────────────────┘${NC}"
        echo ""
        echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
        read choice
        
        case $choice in
            1)
                echo "\n${GREEN}🚀 Запуск повного очищення VS Code...${NC}"
                sleep 1
                ./deep_vscode_cleanup.sh
                echo "\n${GREEN}✅ Процес завершено!${NC}"
                echo "${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            2)
                echo "\n${BLUE}🔄 Відновлення з бекапу...${NC}"
                sleep 1
                ./restore_vscode_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            3)
                echo "\n${CYAN}📊 Перевірка статусу...${NC}"
                sleep 1
                ./check_vscode_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            4)
                echo "\n${MAGENTA}🔧 Управління профілями...${NC}"
                sleep 1
                ./manage_vscode_configs.sh
                ;;
            5)
                echo "\n${BLUE}📦 Менеджер бекапів...${NC}"
                sleep 1
                ./check_vscode_backup.sh
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            0)
                return
                ;;
            *)
                echo "${RED}❌ Невірний вибір!${NC}"
                sleep 1
                ;;
        esac
    done
}

# Статус системи
system_status() {
    print_header
    echo "${WHITE}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo "${WHITE}│${NC}  ${BOLD}📊 SYSTEM STATUS${NC}                                         ${WHITE}│${NC}"
    echo "${WHITE}├─────────────────────────────────────────────────────────────┤${NC}"
    
    # Hostname
    CURRENT_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "Not set")
    echo "${WHITE}│${NC}  ${CYAN}Hostname:${NC} $CURRENT_HOSTNAME"
    
    # Windsurf Status
    if [ -d "/Applications/Windsurf.app" ]; then
        echo "${WHITE}│${NC}  ${GREEN}Windsurf:${NC} ✅ Installed"
    else
        echo "${WHITE}│${NC}  ${RED}Windsurf:${NC} ❌ Not installed"
    fi
    
    # VS Code Status
    if [ -d "/Applications/Visual Studio Code.app" ]; then
        echo "${WHITE}│${NC}  ${GREEN}VS Code:${NC} ✅ Installed"
    else
        echo "${WHITE}│${NC}  ${RED}VS Code:${NC} ❌ Not installed"
    fi
    
    # Windsurf Configs
    WINDSURF_CONFIGS=$(ls -1 configs/ 2>/dev/null | wc -l | xargs)
    echo "${WHITE}│${NC}  ${CYAN}Windsurf Profiles:${NC} $WINDSURF_CONFIGS"
    
    # VS Code Configs
    VSCODE_CONFIGS=$(ls -1 configs_vscode/ 2>/dev/null | wc -l | xargs)
    echo "${WHITE}│${NC}  ${CYAN}VS Code Profiles:${NC} $VSCODE_CONFIGS"
    
    # Backups
    WINDSURF_BACKUPS=$(ls -1d /tmp/windsurf_backup_* 2>/dev/null | wc -l | xargs)
    VSCODE_BACKUPS=$(ls -1d /tmp/vscode_backup_* 2>/dev/null | wc -l | xargs)
    echo "${WHITE}│${NC}  ${CYAN}Active Backups:${NC} Windsurf: $WINDSURF_BACKUPS, VS Code: $VSCODE_BACKUPS"
    
    # Restore Processes
    WINDSURF_RESTORE=$(ps aux | grep "sleep 18000" | grep "windsurf_restore" | grep -v grep | wc -l | xargs)
    VSCODE_RESTORE=$(ps aux | grep "sleep 18000" | grep "vscode_restore" | grep -v grep | wc -l | xargs)
    if [ $WINDSURF_RESTORE -gt 0 ] || [ $VSCODE_RESTORE -gt 0 ]; then
        echo "${WHITE}│${NC}  ${GREEN}Auto-Restore:${NC} ✅ Active (Windsurf: $WINDSURF_RESTORE, VS Code: $VSCODE_RESTORE)"
    else
        echo "${WHITE}│${NC}  ${YELLOW}Auto-Restore:${NC} ⚠️  Inactive"
    fi
    
    echo "${WHITE}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo "${YELLOW}Натисніть Enter для продовження...${NC}"
    read
}

# Документація
documentation_menu() {
    print_header
    echo "${MAGENTA}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo "${MAGENTA}│${NC}  ${BOLD}📚 DOCUMENTATION${NC}                                         ${MAGENTA}│${NC}"
    echo "${MAGENTA}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[1]${NC} 📖 ${WHITE}Main README${NC}                                      ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[2]${NC} 📖 ${WHITE}VS Code README${NC}                                   ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[3]${NC} 📝 ${WHITE}Changelog V3${NC}                                     ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[4]${NC} 📊 ${WHITE}Summary V3${NC}                                       ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[5]${NC} 🔒 ${WHITE}Security Guide${NC}                                   ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${GREEN}[6]${NC} 🔄 ${WHITE}Workflow Guide${NC}                                   ${MAGENTA}│${NC}"
    echo "${MAGENTA}│${NC}  ${RED}[0]${NC} ⬅️  ${RED}Back${NC}                                             ${MAGENTA}│${NC}"
    echo "${MAGENTA}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
    read choice
    
    case $choice in
        1) cat README.md | less ;;
        2) cat README_VSCODE.md | less ;;
        3) cat CHANGELOG_V3.md | less ;;
        4) cat SUMMARY_V3.txt | less ;;
        5) cat SECURITY.md | less ;;
        6) cat WORKFLOW.md | less ;;
        0) return ;;
        *) echo "${RED}❌ Невірний вибір!${NC}"; sleep 1 ;;
    esac
}

# Запуск веб-інтерфейсу
start_web_interface() {
    print_header
    echo "${MAGENTA}🌐 Запуск Web Interface...${NC}"
    echo ""
    
    # Перевірка чи існує веб-сервер
    if [ -f "web_interface/server.py" ]; then
        echo "${GREEN}✅ Знайдено веб-сервер${NC}"
        echo "${CYAN}🚀 Запуск на http://localhost:8888${NC}"
        echo ""
        echo "${YELLOW}Натисніть Ctrl+C для зупинки сервера${NC}"
        echo ""
        cd web_interface && python3 server.py
    else
        echo "${RED}❌ Веб-інтерфейс не знайдено!${NC}"
        echo "${YELLOW}💡 Створюю веб-інтерфейс...${NC}"
        sleep 2
        echo "${YELLOW}Натисніть Enter для продовження...${NC}"
        read
    fi
}

# Головний цикл
main() {
    # Перевірка що скрипт запущено з правильної директорії
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    cd "$SCRIPT_DIR"
    
    while true; do
        print_main_menu
        read choice
        
        case $choice in
            1)
                windsurf_menu
                ;;
            2)
                vscode_menu
                ;;
            3)
                start_web_interface
                ;;
            4)
                system_status
                ;;
            5)
                documentation_menu
                ;;
            0)
                clear_screen
                echo "${GREEN}👋 До побачення!${NC}"
                echo ""
                exit 0
                ;;
            *)
                echo "${RED}❌ Невірний вибір! Спробуйте ще раз.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Запуск головної функції
main
