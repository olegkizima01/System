#!/bin/zsh

# Система відстеження історії змін
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HISTORY_DIR="$SCRIPT_DIR/history"
HISTORY_FILE="$HISTORY_DIR/changes.log"
HISTORY_JSON="$HISTORY_DIR/changes.json"

# Створити директорію якщо не існує
mkdir -p "$HISTORY_DIR"

# Ініціалізувати JSON файл якщо не існує
if [ ! -f "$HISTORY_JSON" ]; then
    echo '{"changes": []}' > "$HISTORY_JSON"
fi

# Функція для додавання запису в історію
add_history_entry() {
    local system=$1      # windsurf або vscode
    local action=$2      # cleanup, restore, switch_profile
    local details=$3     # додаткова інформація
    local timestamp=$(date +%Y-%m-%d\ %H:%M:%S)
    local hostname=$(scutil --get HostName 2>/dev/null || echo "unknown")
    
    # Додати в лог файл
    echo "[$timestamp] [$system] $action - $details (hostname: $hostname)" >> "$HISTORY_FILE"
    
    # Додати в JSON
    local temp_file=$(mktemp)
    jq --arg ts "$timestamp" \
       --arg sys "$system" \
       --arg act "$action" \
       --arg det "$details" \
       --arg host "$hostname" \
       '.changes += [{
           "timestamp": $ts,
           "system": $sys,
           "action": $act,
           "details": $det,
           "hostname": $host
       }]' "$HISTORY_JSON" > "$temp_file"
    
    mv "$temp_file" "$HISTORY_JSON"
    
    echo "✅ Історію оновлено: $action для $system"
}

# Функція для отримання останніх записів
get_recent_history() {
    local count=${1:-10}
    
    if [ -f "$HISTORY_JSON" ]; then
        jq -r ".changes | .[-$count:] | .[] | \"\(.timestamp) | \(.system) | \(.action) | \(.details)\"" "$HISTORY_JSON"
    else
        echo "Історія порожня"
    fi
}

# Функція для отримання історії конкретної системи
get_system_history() {
    local system=$1
    local count=${2:-10}
    
    if [ -f "$HISTORY_JSON" ]; then
        jq -r ".changes | map(select(.system == \"$system\")) | .[-$count:] | .[] | \"\(.timestamp) | \(.action) | \(.details)\"" "$HISTORY_JSON"
    else
        echo "Історія для $system порожня"
    fi
}

# Функція для очищення старої історії (старше 30 днів)
cleanup_old_history() {
    local days_ago=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d "30 days ago" +%Y-%m-%d)
    
    if [ -f "$HISTORY_JSON" ]; then
        local temp_file=$(mktemp)
        jq --arg date "$days_ago" '.changes | map(select(.timestamp >= $date))' "$HISTORY_JSON" > "$temp_file"
        mv "$temp_file" "$HISTORY_JSON"
        echo "✅ Стара історія очищена (старше $days_ago)"
    fi
}

# Функція для експорту історії
export_history() {
    local output_file=${1:-"$SCRIPT_DIR/history_export_$(date +%Y%m%d_%H%M%S).txt"}
    
    if [ -f "$HISTORY_FILE" ]; then
        cp "$HISTORY_FILE" "$output_file"
        echo "✅ Історію експортовано в: $output_file"
    else
        echo "❌ Файл історії не знайдено"
    fi
}

# Функція для відображення статистики
show_statistics() {
    if [ ! -f "$HISTORY_JSON" ]; then
        echo "Історія порожня"
        return
    fi
    
    echo "📊 СТАТИСТИКА ЗМІН"
    echo "===================="
    
    # Загальна кількість змін
    local total=$(jq '.changes | length' "$HISTORY_JSON")
    echo "Всього змін: $total"
    
    # Зміни по системах
    local windsurf_count=$(jq '[.changes[] | select(.system == "windsurf")] | length' "$HISTORY_JSON")
    local vscode_count=$(jq '[.changes[] | select(.system == "vscode")] | length' "$HISTORY_JSON")
    echo "Windsurf: $windsurf_count змін"
    echo "VS Code: $vscode_count змін"
    
    # Зміни по типах дій
    echo "\nДії:"
    jq -r '.changes | group_by(.action) | .[] | "\(.[0].action): \(length)"' "$HISTORY_JSON"
    
    # Останні 5 змін
    echo "\n📜 Останні 5 змін:"
    jq -r '.changes | .[-5:] | .[] | "  • \(.timestamp) - \(.system): \(.action)"' "$HISTORY_JSON"
}

# Інтерактивне меню
interactive_menu() {
    while true; do
        clear
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║           📜 HISTORY TRACKER - УПРАВЛІННЯ ІСТОРІЄЮ          ║"
        echo "╚══════════════════════════════════════════════════════════════╝"
        echo ""
        echo "  [1] 📊 Показати статистику"
        echo "  [2] 📜 Останні 20 записів"
        echo "  [3] 🌊 Історія Windsurf"
        echo "  [4] 💻 Історія VS Code"
        echo "  [5] 💾 Експортувати історію"
        echo "  [6] 🧹 Очистити стару історію (>30 днів)"
        echo "  [0] ❌ Вихід"
        echo ""
        echo -n "➤ Ваш вибір: "
        read choice
        
        case $choice in
            1)
                echo ""
                show_statistics
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            2)
                echo "\n📜 Останні 20 записів:"
                echo "===================="
                get_recent_history 20
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            3)
                echo "\n🌊 Історія Windsurf (останні 20):"
                echo "================================"
                get_system_history "windsurf" 20
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            4)
                echo "\n💻 Історія VS Code (останні 20):"
                echo "==============================="
                get_system_history "vscode" 20
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            5)
                echo ""
                export_history
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            6)
                echo ""
                cleanup_old_history
                echo "\nНатисніть Enter для продовження..."
                read
                ;;
            0)
                echo "👋 До побачення!"
                exit 0
                ;;
            *)
                echo "❌ Невірний вибір!"
                sleep 1
                ;;
        esac
    done
}

# Якщо скрипт викликано без аргументів - показати меню
if [ $# -eq 0 ]; then
    interactive_menu
else
    # Виклик функції з аргументами
    case $1 in
        add)
            add_history_entry "$2" "$3" "$4"
            ;;
        recent)
            get_recent_history "$2"
            ;;
        system)
            get_system_history "$2" "$3"
            ;;
        stats)
            show_statistics
            ;;
        export)
            export_history "$2"
            ;;
        cleanup)
            cleanup_old_history
            ;;
        *)
            echo "Використання:"
            echo "  $0                              - Інтерактивне меню"
            echo "  $0 add <system> <action> <details> - Додати запис"
            echo "  $0 recent [count]               - Останні записи"
            echo "  $0 system <system> [count]      - Історія системи"
            echo "  $0 stats                        - Статистика"
            echo "  $0 export [file]                - Експорт історії"
            echo "  $0 cleanup                      - Очистити стару історію"
            ;;
    esac
fi
