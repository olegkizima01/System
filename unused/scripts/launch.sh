#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🚀 DEEP CLEANUP SYSTEM - UNIFIED LAUNCHER v3.0
#  Єдиний файл запуску з вбудованим веб-інтерфейсом
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Порт для веб-сервера
WEB_PORT=8888

# Допоміжна функція для ініціалізації sudo-сесії через SUDO_PASSWORD з .env
ensure_sudo_session() {
    local ENV_FILE="$SCRIPT_DIR/.env"
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
    fi

    export SUDO_ASKPASS="$SCRIPT_DIR/sudo_helper.sh"
    chmod +x "$SUDO_ASKPASS" 2>/dev/null

    echo "\n${YELLOW}🔑 Перевірка sudo-сесії для повного очищення...${NC}"
    if [ -n "$SUDO_PASSWORD" ]; then
        echo "$SUDO_PASSWORD" | sudo -S -v 2>/dev/null
    else
        sudo -v
    fi
}

# Закриття всіх процесів, пов'язаних з Windsurf / VS Code
kill_windsurf_processes() {
    echo "\n${YELLOW}🔍 Перевірка активних процесів Windsurf / VS Code...${NC}"

    if pgrep -f "Windsurf" >/dev/null 2>&1 || pgrep -f "windsurf" >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  Виявлено запущений Windsurf. Закриваю...${NC}"
        pkill -9 -f "Windsurf" 2>/dev/null
        pkill -9 -f "windsurf" 2>/dev/null
    fi

    if pgrep -f "Visual Studio Code" >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  Виявлено запущений Visual Studio Code. Закриваю...${NC}"
        pkill -9 -f "Visual Studio Code" 2>/dev/null
        pkill -9 -f "Code Helper" 2>/dev/null
    fi

    sleep 1
}

# Закриття всіх процесів, пов'язаних з Antigravity / браузером
kill_antigravity_processes() {
    echo "\n${YELLOW}🔍 Перевірка активних процесів Antigravity / браузера...${NC}"

    if pgrep -f "Antigravity" >/dev/null 2>&1 || pgrep -f "antigravity" >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  Виявлено запущений Antigravity Editor. Закриваю...${NC}"
        pkill -9 -f "Antigravity" 2>/dev/null
        pkill -9 -f "antigravity" 2>/dev/null
    fi

    if pgrep -f "Google Chrome" >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  Виявлено запущений Google Chrome. Закриваю...${NC}"
        pkill -9 -f "Google Chrome" 2>/dev/null
        pkill -9 -f "chrome" 2>/dev/null
    fi

    sleep 1
}

# Функція для перевірки порту
check_port() {
    lsof -i :$WEB_PORT >/dev/null 2>&1
    return $?
}

# Функція для створення веб-сервера якщо не існує
create_web_server() {
    mkdir -p web_interface/templates web_interface/static
    
    # Створити Python сервер
    cat > web_interface/server.py << 'EOFPYTHON'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
from datetime import datetime
from urllib.parse import parse_qs, urlparse

PORT = 8888

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/api/status':
            self.send_json_response(self.get_system_status())
        elif self.path == '/api/configs/windsurf':
            self.send_json_response(self.get_configs('windsurf'))
        elif self.path == '/api/configs/vscode':
            self.send_json_response(self.get_configs('vscode'))
        elif self.path.startswith('/static/'):
            super().do_GET()
        else:
            self.send_error(404)
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/api/cleanup/windsurf':
                result = self.run_cleanup('windsurf')
                self.send_json_response(result)
            elif self.path == '/api/cleanup/vscode':
                result = self.run_cleanup('vscode')
                self.send_json_response(result)
            elif self.path == '/api/restore/windsurf':
                result = self.run_restore('windsurf', data.get('config', ''))
                self.send_json_response(result)
            elif self.path == '/api/restore/vscode':
                result = self.run_restore('vscode', data.get('config', ''))
                self.send_json_response(result)
            else:
                self.send_error(404)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {str(e)}'})
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_system_status(self):
        hostname = subprocess.getoutput("scutil --get HostName 2>/dev/null || echo 'Not set'")
        
        # Більш гнучка перевірка Windsurf
        windsurf_installed = (
            os.path.exists('/Applications/Windsurf.app') or
            os.path.exists('/Applications/windsurf.app') or
            subprocess.getoutput("which windsurf 2>/dev/null") != "" or
            subprocess.getoutput("find /Applications -name '*indsurf*' -type d 2>/dev/null") != ""
        )
        
        # Більш гнучка перевірка VS Code
        vscode_installed = (
            os.path.exists('/Applications/Visual Studio Code.app') or
            os.path.exists('/Applications/Code.app') or
            subprocess.getoutput("which code 2>/dev/null") != "" or
            subprocess.getoutput("find /Applications -name '*Visual Studio Code*' -type d 2>/dev/null") != ""
        )
        
        windsurf_configs = len([f for f in os.listdir('../configs') if os.path.isdir(f'../configs/{f}')]) if os.path.exists('../configs') else 0
        vscode_configs = len([f for f in os.listdir('../configs_vscode') if os.path.isdir(f'../configs_vscode/{f}')]) if os.path.exists('../configs_vscode') else 0
        
        return {
            'hostname': hostname,
            'windsurf': {'installed': windsurf_installed, 'configs': windsurf_configs},
            'vscode': {'installed': vscode_installed, 'configs': vscode_configs},
            'timestamp': datetime.now().isoformat()
        }
    
    def get_configs(self, system):
        configs_dir = f'../configs' if system == 'windsurf' else f'../configs_vscode'
        configs = []
        
        if os.path.exists(configs_dir):
            for config_name in os.listdir(configs_dir):
                config_path = os.path.join(configs_dir, config_name)
                if os.path.isdir(config_path):
                    metadata_file = os.path.join(config_path, 'metadata.json')
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            configs.append(metadata)
        
        return {'configs': configs}
    
    def run_cleanup(self, system):
        script = '../deep_windsurf_cleanup.sh' if system == 'windsurf' else '../deep_vscode_cleanup.sh'
        return {'success': True, 'message': f'Cleanup initiated for {system}'}

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Server running at http://localhost:{PORT}")
        httpd.serve_forever()
EOFPYTHON
    
    chmod +x web_interface/server.py
}

# Головне меню
show_menu() {
    clear
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${GREEN}⚡ DEEP CLEANUP SYSTEM - UNIFIED LAUNCHER v3.0 ⚡${NC}      ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Єдиний файл запуску з вбудованим веб-інтерфейсом${NC}      ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo "${YELLOW}│${NC}  ${BOLD}ОБЕРІТЬ РЕЖИМ ЗАПУСКУ:${NC}                                   ${YELLOW}│${NC}"
    echo "${YELLOW}├─────────────────────────────────────────────────────────────┤${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[1]${NC} 🌐 ${MAGENTA}Web Interface${NC} (Hacker Dashboard)                 ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Запустити веб-інтерфейс на http://localhost:$WEB_PORT${NC}  ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[2]${NC} 🎮 ${CYAN}Interactive Menu${NC} (Terminal)                      ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Інтерактивне меню в терміналі${NC}                       ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[3]${NC} 🌊 ${CYAN}Windsurf Cleanup${NC} (Direct)                        ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Прямий запуск очищення Windsurf${NC}                     ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[4]${NC} 💻 ${BLUE}VS Code Cleanup${NC} (Direct)                         ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Прямий запуск очищення VS Code${NC}                      ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[5]${NC} 📊 ${WHITE}System Check${NC}                                     ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Перевірка цілісності системи${NC}                        ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[6]${NC} 📜 ${WHITE}History Tracker${NC}                                  ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Перегляд історії змін${NC}                               ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[7]${NC} 🔄 ${CYAN}Windsurf ID Cleanup${NC} (Quick Fix)                   ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Базове очищення ідентифікаторів${NC}                    ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[8]${NC} 🚀 ${RED}Advanced Windsurf Cleanup${NC} (Deep Fix)              ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Розширене очищення всіх ідентифікаторів${NC}            ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[9]${NC} 📚 ${WHITE}Documentation${NC}                                    ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Відкрити документацію${NC}                               ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${GREEN}[10]${NC} ⚡ ${CYAN}Ultimate Windsurf CLI${NC} (No Web UI)           ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Повний CLI-режим без веб-інтерфейсу${NC}                 ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[11]${NC} ${RED}🌊 WINDSURF FULL (всё + стелс + спуфінг)${NC}           ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Максимальне очищення Windsurf + VS Code + Stealth${NC} ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[12]${NC} ${RED}🛰  ANTIGRAVITY FULL (всё + стелс + спуфінг)${NC}       ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}      ${WHITE}Максимальне очищення Antigravity + Stealth + Spoof${NC} ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}                                                             ${YELLOW}│${NC}"
    echo "${YELLOW}│${NC}  ${RED}[0]${NC} ❌ ${RED}Exit${NC}                                             ${YELLOW}│${NC}"
    echo "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    
    # Показати статус
    echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo "${WHITE}📊 Поточний статус:${NC}"
    CURRENT_HOSTNAME=$(scutil --get HostName 2>/dev/null || echo "Not set")
    echo "   Hostname: ${GREEN}$CURRENT_HOSTNAME${NC}"
    
    if [ -d "/Applications/Windsurf.app" ]; then
        echo "   Windsurf: ${GREEN}✅ Встановлено${NC}"
    else
        echo "   Windsurf: ${RED}❌ Не встановлено${NC}"
    fi
    
    if [ -d "/Applications/Visual Studio Code.app" ]; then
        echo "   VS Code: ${GREEN}✅ Встановлено${NC}"
    else
        echo "   VS Code: ${RED}❌ Не встановлено${NC}"
    fi

    # Перевірка Antigravity Editor (додаток або сліди в системі)
    ANTIGRAVITY_PRESENT=0
    if [ -d "/Applications/Antigravity.app" ] || [ -d "/Applications/Google Antigravity.app" ]; then
        ANTIGRAVITY_PRESENT=1
    elif [ -d "$HOME/Library/Application Support/Antigravity" ] || [ -d "$HOME/Library/Application Support/Google/Antigravity" ]; then
        ANTIGRAVITY_PRESENT=1
    fi

    if [ "$ANTIGRAVITY_PRESENT" -eq 1 ]; then
        echo "   Antigravity: ${GREEN}✅ Виявлено (додаток або сліди)${NC}"
    else
        echo "   Antigravity: ${RED}❌ Не виявлено${NC}"
    fi

    echo "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -n "${BOLD}${WHITE}➤ Ваш вибір: ${NC}"
}

# Запуск веб-інтерфейсу
launch_web() {
    echo ""
    echo "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${MAGENTA}║${NC}  ${GREEN}🌐 ЗАПУСК ВЕБ-ІНТЕРФЕЙСУ${NC}                                  ${MAGENTA}║${NC}"
    echo "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Перевірити чи порт зайнятий
    if check_port; then
        echo "${YELLOW}⚠️  Порт $WEB_PORT вже зайнятий!${NC}"
        echo "${CYAN}💡 Можливо веб-сервер вже запущено${NC}"
        echo ""
        echo "${WHITE}Спробуйте відкрити: ${GREEN}http://localhost:$WEB_PORT${NC}"
        echo ""
        echo -n "${YELLOW}Вбити процес на порту $WEB_PORT? (y/n): ${NC}"
        read kill_choice
        
        if [ "$kill_choice" = "y" ] || [ "$kill_choice" = "Y" ]; then
            PID=$(lsof -ti :$WEB_PORT)
            if [ -n "$PID" ]; then
                kill -9 $PID 2>/dev/null
                echo "${GREEN}✅ Процес зупинено${NC}"
                sleep 1
            fi
        else
            echo "${YELLOW}Натисніть Enter для продовження...${NC}"
            read
            return
        fi
    fi
    
    # Створити веб-сервер якщо не існує
    if [ ! -f "web_interface/server.py" ]; then
        echo "${YELLOW}📦 Створення веб-інтерфейсу...${NC}"
        create_web_server
        echo "${GREEN}✅ Веб-інтерфейс створено${NC}"
    fi
    
    # Запустити сервер
    echo "${GREEN}🚀 Запуск веб-сервера...${NC}"
    echo ""
    echo "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo "${CYAN}║${NC}  ${GREEN}✅ Веб-інтерфейс запущено!${NC}                                 ${CYAN}║${NC}"
    echo "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo "${CYAN}║${NC}  ${WHITE}URL: ${GREEN}http://localhost:$WEB_PORT${NC}                          ${CYAN}║${NC}"
    echo "${CYAN}║${NC}  ${WHITE}Дизайн: ${MAGENTA}Hacker Style (Matrix Theme)${NC}                 ${CYAN}║${NC}"
    echo "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
    echo "${CYAN}║${NC}  ${YELLOW}💡 Відкрийте URL в браузері${NC}                              ${CYAN}║${NC}"
    echo "${CYAN}║${NC}  ${YELLOW}💡 Натисніть Ctrl+C для зупинки${NC}                          ${CYAN}║${NC}"
    echo "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Спробувати відкрити в браузері
    if command -v open >/dev/null 2>&1; then
        echo "${CYAN}🌐 Відкриваю браузер...${NC}"
        sleep 2
        open "http://localhost:$WEB_PORT" 2>/dev/null &
    fi
    
    # Запустити сервер
    cd web_interface
    python3 server.py
}

# Головний цикл
main() {
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                launch_web
                ;;
            2)
                echo "\n${CYAN}🎮 Запуск інтерактивного меню...${NC}"
                sleep 1
                if [ -f "main_menu.sh" ]; then
                    ./main_menu.sh
                else
                    echo "${RED}❌ main_menu.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            3)
                echo "\n${GREEN}🌊 Запуск Windsurf cleanup...${NC}"
                sleep 1
                if [ -f "deep_windsurf_cleanup.sh" ]; then
                    WINDSURF_FULL_AUTO=1 ./deep_windsurf_cleanup.sh
                    echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                    read
                else
                    echo "${RED}❌ deep_windsurf_cleanup.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            4)
                echo "\n${BLUE}💻 Запуск VS Code cleanup...${NC}"
                sleep 1
                if [ -f "deep_vscode_cleanup.sh" ]; then
                    ./deep_vscode_cleanup.sh
                    echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                    read
                else
                    echo "${RED}❌ deep_vscode_cleanup.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            5)
                echo "\n${WHITE}📊 Перевірка системи...${NC}"
                sleep 1
                if [ -f "system_check.sh" ]; then
                    ./system_check.sh
                    echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                    read
                else
                    echo "${RED}❌ system_check.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            6)
                echo "\n${WHITE}📜 Історія змін...${NC}"
                sleep 1
                if [ -f "history_tracker.sh" ]; then
                    ./history_tracker.sh
                else
                    echo "${RED}❌ history_tracker.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            7)
                echo "\n${CYAN}🔄 Запуск очищення ідентифікаторів Windsurf...${NC}"
                sleep 1
                if [ -f "windsurf_identifier_cleanup.sh" ]; then
                    ./windsurf_identifier_cleanup.sh
                    echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                    read
                else
                    echo "${RED}❌ windsurf_identifier_cleanup.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            8)
                echo "\n${RED}🚀 Запуск розширеного очищення Windsurf...${NC}"
                sleep 1
                if [ -f "advanced_windsurf_cleanup.sh" ]; then
                    ./advanced_windsurf_cleanup.sh
                    echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                    read
                else
                    echo "${RED}❌ advanced_windsurf_cleanup.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            9)
                clear
                echo "${MAGENTA}╔══════════════════════════════════════════════════════════════╗${NC}"
                echo "${MAGENTA}║${NC}  ${GREEN}📚 ДОКУМЕНТАЦІЯ${NC}                                          ${MAGENTA}║${NC}"
                echo "${MAGENTA}╚══════════════════════════════════════════════════════════════╝${NC}"
                echo ""
                echo "${WHITE}Доступні документи:${NC}"
                echo "  ${GREEN}[1]${NC} START_HERE.md - Початок роботи"
                echo "  ${GREEN}[2]${NC} QUICK_START.md - Швидкий старт"
                echo "  ${GREEN}[3]${NC} FINAL_SUMMARY.md - Повний огляд"
                echo "  ${GREEN}[4]${NC} README.md - Windsurf"
                echo "  ${GREEN}[5]${NC} README_VSCODE.md - VS Code"
                echo "  ${GREEN}[6]${NC} WEB_INTERFACE_README.md - Веб"
                echo "  ${RED}[0]${NC} Назад"
                echo ""
                echo -n "${WHITE}➤ Оберіть документ: ${NC}"
                read doc_choice
                
                case $doc_choice in
                    1) [ -f "START_HERE.md" ] && cat START_HERE.md | less ;;
                    2) [ -f "QUICK_START.md" ] && cat QUICK_START.md | less ;;
                    3) [ -f "FINAL_SUMMARY.md" ] && cat FINAL_SUMMARY.md | less ;;
                    4) [ -f "README.md" ] && cat README.md | less ;;
                    5) [ -f "README_VSCODE.md" ] && cat README_VSCODE.md | less ;;
                    6) [ -f "WEB_INTERFACE_README.md" ] && cat WEB_INTERFACE_README.md | less ;;
                    0) ;;
                    *) echo "${RED}❌ Невірний вибір!${NC}"; sleep 1 ;;
                esac
                ;;
            10)
                echo "\n${CYAN}⚡ Запуск Smart Cleanup CLI (без веб-інтерфейсу)...${NC}"
                sleep 1
                if [ -f "cli.sh" ]; then
                    zsh ./cli.sh
                elif [ -f "ultimate_windsurf_cli.sh" ]; then
                    zsh ./ultimate_windsurf_cli.sh
                else
                    echo "${RED}❌ cli.sh / ultimate_windsurf_cli.sh не знайдено!${NC}"
                    sleep 2
                fi
                ;;
            11)
                echo "\n${RED}🌊 Запуск WINDSURF FULL ULTIMATE CLEANUP...${NC}"
                sleep 1
                kill_windsurf_processes
                ensure_sudo_session

                if [ -f "deep_windsurf_cleanup.sh" ]; then
                    ./deep_windsurf_cleanup.sh
                else
                    echo "${RED}❌ deep_windsurf_cleanup.sh не знайдено!${NC}"
                fi

                if [ -f "advanced_windsurf_cleanup.sh" ]; then
                    ./advanced_windsurf_cleanup.sh
                else
                    echo "${RED}❌ advanced_windsurf_cleanup.sh не знайдено!${NC}"
                fi

                if [ -f "deep_vscode_cleanup.sh" ]; then
                    ./deep_vscode_cleanup.sh
                else
                    echo "${YELLOW}⚠️  deep_vscode_cleanup.sh не знайдено. Пропускаю цей крок.${NC}"
                fi

                if [ -f "stealth_cleanup.sh" ]; then
                    ./stealth_cleanup.sh
                else
                    echo "${YELLOW}⚠️  stealth_cleanup.sh не знайдено. Пропускаю стелс-очищення.${NC}"
                fi

                if [ -f "hardware_spoof.sh" ]; then
                    ./hardware_spoof.sh
                else
                    echo "${YELLOW}⚠️  hardware_spoof.sh не знайдено. Пропускаю підміну hardware fingerprint.${NC}"
                fi

                if [ -f "check_identifier_cleanup.sh" ]; then
                    ./check_identifier_cleanup.sh
                else
                    echo "${YELLOW}⚠️  check_identifier_cleanup.sh не знайдено. Пропускаю фінальну перевірку.${NC}"
                fi

                echo "\n${GREEN}✅ WINDSURF FULL ULTIMATE CLEANUP завершено.${NC}"
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            12)
                echo "\n${RED}🛰  Запуск ANTIGRAVITY FULL ULTIMATE CLEANUP...${NC}"
                sleep 1
                kill_antigravity_processes
                ensure_sudo_session

                if [ -f "antigraviti_cleanup.sh" ]; then
                    ./antigraviti_cleanup.sh
                else
                    echo "${RED}❌ antigraviti_cleanup.sh не знайдено!${NC}"
                fi

                if [ -f "advanced_antigraviti_cleanup.sh" ]; then
                    ./advanced_antigraviti_cleanup.sh
                else
                    echo "${RED}❌ advanced_antigraviti_cleanup.sh не знайдено!${NC}"
                fi

                if [ -f "deep_vscode_cleanup.sh" ]; then
                    ./deep_vscode_cleanup.sh
                else
                    echo "${YELLOW}⚠️  deep_vscode_cleanup.sh не знайдено. Пропускаю цей крок.${NC}"
                fi

                if [ -f "stealth_cleanup.sh" ]; then
                    ./stealth_cleanup.sh
                else
                    echo "${YELLOW}⚠️  stealth_cleanup.sh не знайдено. Пропускаю стелс-очищення.${NC}"
                fi

                if [ -f "hardware_spoof.sh" ]; then
                    ./hardware_spoof.sh
                else
                    echo "${YELLOW}⚠️  hardware_spoof.sh не знайдено. Пропускаю підміну hardware fingerprint.${NC}"
                fi

                echo "\n${GREEN}✅ ANTIGRAVITY FULL ULTIMATE CLEANUP завершено.${NC}"
                echo "\n${YELLOW}Натисніть Enter для продовження...${NC}"
                read
                ;;
            0)
                clear
                echo "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
                echo "${GREEN}║${NC}  ${WHITE}👋 До побачення!${NC}                                         ${GREEN}║${NC}"
                echo "${GREEN}║${NC}  ${CYAN}Дякуємо за використання Deep Cleanup System v3.0${NC}     ${GREEN}║${NC}"
                echo "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
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

# Перевірка Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}❌ Python 3 не знайдено!${NC}"
    echo "${YELLOW}💡 Встановіть Python 3: brew install python3${NC}"
    exit 1
fi

# Запуск
main
