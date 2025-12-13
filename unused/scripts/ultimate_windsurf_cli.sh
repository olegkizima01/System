#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

pause() {
    echo ""
    echo -n "${YELLOW}Натисніть Enter для повернення в меню...${NC}"
    read _
}

run_full_windsurf_cycle() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${GREEN}ULTIMATE WINDSURF CLI CLEANUP${NC}                              ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Повний ланцюжок очищення без веб-інтерфейсу${NC}               ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${WHITE}Будуть виконані кроки:${NC}"
    echo "  • Глибоке видалення Windsurf (deep_windsurf_cleanup.sh)"
    echo "  • Розширене очищення ідентифікаторів (advanced_windsurf_cleanup.sh)"
    echo "  • Фінальна перевірка якості cleanup (check_identifier_cleanup.sh)"
    echo ""
    echo -n "${YELLOW}Продовжити? (y/n): ${NC}"
    read answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi

    echo "\n${BLUE}▶ Крок 1/3: deep_windsurf_cleanup.sh${NC}"
    if [ -f "./deep_windsurf_cleanup.sh" ]; then
        ./deep_windsurf_cleanup.sh
    else
        echo "${RED}deep_windsurf_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 2/3: advanced_windsurf_cleanup.sh${NC}"
    if [ -f "./advanced_windsurf_cleanup.sh" ]; then
        ./advanced_windsurf_cleanup.sh
    else
        echo "${RED}advanced_windsurf_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 3/3: check_identifier_cleanup.sh${NC}"
    if [ -f "./check_identifier_cleanup.sh" ]; then
        ./check_identifier_cleanup.sh
    else
        echo "${YELLOW}check_identifier_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${GREEN}✅ Повний CLI-цикл очищення Windsurf завершено.${NC}"
    pause
}

run_identifier_reset() {
    clear
    echo "${CYAN}🔄 Швидке очищення ідентифікаторів Windsurf (identifier cleanup)${NC}"
    echo ""
    if [ -f "./windsurf_identifier_cleanup.sh" ]; then
        ./windsurf_identifier_cleanup.sh
    else
        echo "${RED}windsurf_identifier_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_advanced_only() {
    clear
    echo "${CYAN}🚀 Тільки advanced_windsurf_cleanup.sh${NC}"
    echo ""
    if [ -f "./advanced_windsurf_cleanup.sh" ]; then
        ./advanced_windsurf_cleanup.sh
    else
        echo "${RED}advanced_windsurf_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_vscode_cleanup() {
    clear
    echo "${CYAN}💻 Глибоке очищення VS Code${NC}"
    echo ""
    if [ -f "./deep_vscode_cleanup.sh" ]; then
        ./deep_vscode_cleanup.sh
    else
        echo "${RED}deep_vscode_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_stealth_cleanup() {
    clear
    echo "${CYAN}🕵️  Stealth cleanup (stealth_cleanup.sh)${NC}"
    echo "${YELLOW}Увага: це режим з агресивною зачисткою системних слідів.${NC}"
    echo -n "${YELLOW}Продовжити? (y/n): ${NC}"
    read answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi
    if [ -f "./stealth_cleanup.sh" ]; then
        ./stealth_cleanup.sh
    else
        echo "${RED}stealth_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_hardware_spoof() {
    clear
    echo "${CYAN}🧬 Hardware spoofing (hardware_spoof.sh)${NC}"
    echo "${YELLOW}Увага: змінює апаратні fingerprint-и, потребує sudo і може бути ризиковим.${NC}"
    echo -n "${YELLOW}Продовжити? (y/n): ${NC}"
    read answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi
    if [ -f "./hardware_spoof.sh" ]; then
        ./hardware_spoof.sh
    else
        echo "${RED}hardware_spoof.sh не знайдено.${NC}"
    fi
    pause
}

run_verification() {
    clear
    echo "${CYAN}🔍 Перевірка якості cleanup (check_identifier_cleanup.sh)${NC}"
    echo ""
    if [ -f "./check_identifier_cleanup.sh" ]; then
        ./check_identifier_cleanup.sh
    else
        echo "${RED}check_identifier_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_antigraviti_cleanup() {
    clear
    echo "${CYAN}🛰  Antigravity Editor Cleanup${NC}"
    echo ""
    if [ -f "./antigraviti_cleanup.sh" ]; then
        ./antigraviti_cleanup.sh
    else
        echo "${RED}antigraviti_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_antigraviti_advanced() {
    clear
    echo "${CYAN}🚀 Тільки advanced_antigraviti_cleanup.sh${NC}"
    echo ""
    if [ -f "./advanced_antigraviti_cleanup.sh" ]; then
        ./advanced_antigraviti_cleanup.sh
    else
        echo "${RED}advanced_antigraviti_cleanup.sh не знайдено.${NC}"
    fi
    pause
}

run_antigraviti_full_cycle() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${GREEN}ANTIGRAVITY EDITOR FULL CLEANUP CYCLE${NC}                    ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Повний ланцюжок очищення Antigravity Editor${NC}             ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${WHITE}Будуть виконані кроки:${NC}"
    echo "  • Основне очищення Antigravity (antigraviti_cleanup.sh)"
    echo "  • Розширене очищення ідентифікаторів (advanced_antigraviti_cleanup.sh)"
    echo "  • Видалення API ключів та токенів"
    echo ""
    echo -n "${YELLOW}Продовжити? (y/n): ${NC}"
    read answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi

    echo "\n${BLUE}▶ Крок 1/2: antigraviti_cleanup.sh${NC}"
    if [ -f "./antigraviti_cleanup.sh" ]; then
        ./antigraviti_cleanup.sh
    else
        echo "${RED}antigraviti_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 2/2: advanced_antigraviti_cleanup.sh${NC}"
    if [ -f "./advanced_antigraviti_cleanup.sh" ]; then
        ./advanced_antigraviti_cleanup.sh
    else
        echo "${RED}advanced_antigraviti_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${GREEN}✅ Повний цикл очищення Antigravity Editor завершено.${NC}"
    pause
}

run_windsurf_full_ultimate() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${RED}🌊 WINDSURF FULL ULTIMATE CLEANUP${NC}                         ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}ПОВНЕ ВИДАЛЕННЯ ВСІХ СЛІДІВ - БЕЗ ЖОДНИХ ЗАЛИШКІВ${NC}      ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${WHITE}Будуть виконані кроки:${NC}"
    echo "  1. Глибоке видалення Windsurf (deep_windsurf_cleanup.sh)"
    echo "  2. Розширене очищення ідентифікаторів (advanced_windsurf_cleanup.sh)"
    echo "  3. Глибоке очищення VS Code (deep_vscode_cleanup.sh)"
    echo "  4. Агресивне очищення системних слідів (stealth_cleanup.sh)"
    echo "  5. Підміна апаратних fingerprint-ів (hardware_spoof.sh)"
    echo "  6. Фінальна перевірка якості cleanup (check_identifier_cleanup.sh)"
    echo ""
    echo "${YELLOW}⚠️  УВАГА: Це МАКСИМАЛЬНЕ очищення!${NC}"
    echo "${YELLOW}Потребує sudo та може вплинути на роботу системи.${NC}"
    echo ""
    echo -n "${RED}Ви впевнені? Введіть 'WINDSURF FULL' для підтвердження: ${NC}"
    read confirmation
    if [ "$confirmation" != "WINDSURF FULL" ]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi

    echo "\n${BLUE}▶ Крок 1/6: deep_windsurf_cleanup.sh${NC}"
    if [ -f "./deep_windsurf_cleanup.sh" ]; then
        ./deep_windsurf_cleanup.sh
    else
        echo "${RED}deep_windsurf_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 2/6: advanced_windsurf_cleanup.sh${NC}"
    if [ -f "./advanced_windsurf_cleanup.sh" ]; then
        ./advanced_windsurf_cleanup.sh
    else
        echo "${RED}advanced_windsurf_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 3/6: deep_vscode_cleanup.sh${NC}"
    if [ -f "./deep_vscode_cleanup.sh" ]; then
        ./deep_vscode_cleanup.sh
    else
        echo "${RED}deep_vscode_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 4/6: stealth_cleanup.sh (агресивне видалення слідів)${NC}"
    if [ -f "./stealth_cleanup.sh" ]; then
        ./stealth_cleanup.sh
    else
        echo "${YELLOW}stealth_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 5/6: hardware_spoof.sh (підміна апаратних fingerprint-ів)${NC}"
    if [ -f "./hardware_spoof.sh" ]; then
        ./hardware_spoof.sh
    else
        echo "${YELLOW}hardware_spoof.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 6/6: check_identifier_cleanup.sh (фінальна перевірка)${NC}"
    if [ -f "./check_identifier_cleanup.sh" ]; then
        ./check_identifier_cleanup.sh
    else
        echo "${YELLOW}check_identifier_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${GREEN}║${NC}  ${WHITE}✅ WINDSURF FULL ULTIMATE CLEANUP ЗАВЕРШЕНО!${NC}           ${GREEN}║${NC}"
    echo "${GREEN}║${NC}  ${WHITE}Всі сліди видалено. Система повністю очищена.${NC}        ${GREEN}║${NC}"
    echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    pause
}

run_antigravity_full_ultimate() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${RED}🛰  ANTIGRAVITY FULL ULTIMATE CLEANUP${NC}                     ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}ПОВНЕ ВИДАЛЕННЯ ВСІХ СЛІДІВ - БЕЗ ЖОДНИХ ЗАЛИШКІВ${NC}      ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${WHITE}Будуть виконані кроки:${NC}"
    echo "  1. Основне очищення Antigravity (antigraviti_cleanup.sh)"
    echo "  2. Розширене очищення ідентифікаторів (advanced_antigraviti_cleanup.sh)"
    echo "  3. Глибоке очищення VS Code (deep_vscode_cleanup.sh)"
    echo "  4. Агресивне очищення системних слідів (stealth_cleanup.sh)"
    echo "  5. Підміна апаратних fingerprint-ів (hardware_spoof.sh)"
    echo ""
    echo "${YELLOW}⚠️  УВАГА: Це МАКСИМАЛЬНЕ очищення!${NC}"
    echo "${YELLOW}Потребує sudo та може вплинути на роботу системи.${NC}"
    echo ""
    echo -n "${RED}Ви впевнені? Введіть 'ANTIGRAVITY FULL' для підтвердження: ${NC}"
    read confirmation
    if [ "$confirmation" != "ANTIGRAVITY FULL" ]; then
        echo "${RED}Операцію скасовано.${NC}"
        pause
        return
    fi

    echo "\n${BLUE}▶ Крок 1/5: antigraviti_cleanup.sh${NC}"
    if [ -f "./antigraviti_cleanup.sh" ]; then
        ./antigraviti_cleanup.sh
    else
        echo "${RED}antigraviti_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 2/5: advanced_antigraviti_cleanup.sh${NC}"
    if [ -f "./advanced_antigraviti_cleanup.sh" ]; then
        ./advanced_antigraviti_cleanup.sh
    else
        echo "${RED}advanced_antigraviti_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 3/5: deep_vscode_cleanup.sh${NC}"
    if [ -f "./deep_vscode_cleanup.sh" ]; then
        ./deep_vscode_cleanup.sh
    else
        echo "${YELLOW}deep_vscode_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 4/5: stealth_cleanup.sh (агресивне видалення слідів)${NC}"
    if [ -f "./stealth_cleanup.sh" ]; then
        ./stealth_cleanup.sh
    else
        echo "${YELLOW}stealth_cleanup.sh не знайдено.${NC}"
    fi

    echo "\n${BLUE}▶ Крок 5/5: hardware_spoof.sh (підміна апаратних fingerprint-ів)${NC}"
    if [ -f "./hardware_spoof.sh" ]; then
        ./hardware_spoof.sh
    else
        echo "${YELLOW}hardware_spoof.sh не знайдено.${NC}"
    fi

    echo "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${GREEN}║${NC}  ${WHITE}✅ ANTIGRAVITY FULL ULTIMATE CLEANUP ЗАВЕРШЕНО!${NC}"         ${GREEN}║${NC}"
    echo "${GREEN}║${NC}  ${WHITE}Всі сліди видалено. Система повністю очищена.${NC}        ${GREEN}║${NC}"
    echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    pause
}

show_menu() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${GREEN}ULTIMATE CLEANUP - CLI MODE v2.0${NC}                       ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Windsurf + Antigravity Editor | Без веб-інтерфейсу${NC}     ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo "${YELLOW}│${NC}  ${BOLD}🌊 WINDSURF CLEANUP:${NC}                                   ${YELLOW}│${NC}"
    echo "${YELLOW}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[1]${NC} 🌊 Повний цикл очищення Windsurf (3 → 8 + чек)     ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[2]${NC} 🔄 Швидке очищення ідентифікаторів Windsurf       ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[3]${NC} 🚀 Тільки Advanced Windsurf Cleanup               ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[4]${NC} 💻 Deep VS Code Cleanup                           ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[7]${NC} 🔍 Перевірити якість cleanup                     ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[11]${NC} ${RED}🌊 WINDSURF FULL (всё + стелс + спуфинг)${NC}        ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${BOLD}🛰  ANTIGRAVITY EDITOR CLEANUP:${NC}                        ${YELLOW}│${NC}"
    echo "${YELLOW}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[8]${NC} 🛰  Antigravity Editor Cleanup (базовий)          ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[9]${NC} 🚀 Тільки Advanced Antigravity Cleanup            ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[10]${NC} 🛰  Antigravity Full Cycle (повний)              ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[12]${NC} ${RED}🛰  ANTIGRAVITY FULL (всё + стелс + спуфинг)${NC}    ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${BOLD}⚙️  ДОДАТКОВІ ОПЦІЇ:${NC}                                  ${YELLOW}│${NC}"
    echo "${YELLOW}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[5]${NC} 🕵️  Stealth Cleanup (опційно)                     ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[6]${NC} 🧬 Hardware Spoofing (опційно)                   ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[0]${NC} ❌ Вихід                                          ${YELLOW}│${NC}"
    echo "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
}

main() {
    while true; do
        show_menu
        read choice
        case "$choice" in
            1)
                run_full_windsurf_cycle
                ;;
            2)
                run_identifier_reset
                ;;
            3)
                run_advanced_only
                ;;
            4)
                run_vscode_cleanup
                ;;
            5)
                run_stealth_cleanup
                ;;
            6)
                run_hardware_spoof
                ;;
            7)
                run_verification
                ;;
            8)
                run_antigraviti_cleanup
                ;;
            9)
                run_antigraviti_advanced
                ;;
            10)
                run_antigraviti_full_cycle
                ;;
            11)
                run_windsurf_full_ultimate
                ;;
            12)
                run_antigravity_full_ultimate
                ;;
            0)
                clear
                echo "${GREEN}👋 Вихід з Ultimate Cleanup CLI.${NC}"
                exit 0
                ;;
            *)
                echo "${RED}Невірний вибір, спробуйте ще раз.${NC}"
                sleep 1
                ;;
        esac
    done
}

main
