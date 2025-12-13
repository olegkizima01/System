#!/bin/zsh

echo "💾 STEALTH BACKUP & RESTORE SYSTEM"
echo "=================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_BASE_DIR="$SCRIPT_DIR/fingerprint_backups"

# Завантаження змінних середовища
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

# Функція для створення backup
create_backup() {
    local backup_name="$1"
    if [ -z "$backup_name" ]; then
        backup_name="auto_$(date +%Y%m%d_%H%M%S)"
    fi
    
    local backup_dir="$BACKUP_BASE_DIR/$backup_name"
    mkdir -p "$backup_dir"
    
    echo "\n[1/5] 💾 Створення backup: $backup_name"
    
    # Backup системних ідентифікаторів
    echo "🔄 Збереження системних ідентифікаторів..."
    
    # Hardware UUID
    system_profiler SPHardwareDataType | grep "Hardware UUID" > "$backup_dir/hardware_uuid.txt" 2>/dev/null
    
    # Hostname
    scutil --get HostName > "$backup_dir/hostname.txt" 2>/dev/null
    scutil --get LocalHostName > "$backup_dir/localhostname.txt" 2>/dev/null
    scutil --get ComputerName > "$backup_dir/computername.txt" 2>/dev/null
    
    # MAC адреси
    ifconfig | grep "ether" > "$backup_dir/mac_addresses.txt" 2>/dev/null
    
    # DNS налаштування
    networksetup -getdnsservers "Wi-Fi" > "$backup_dir/dns_wifi.txt" 2>/dev/null
    networksetup -getdnsservers "Ethernet" > "$backup_dir/dns_ethernet.txt" 2>/dev/null
    
    echo "✅ Системні ідентифікатори збережено"
    
    # Backup SSH ключів
    echo "\n[2/5] 🔑 Збереження SSH конфігурації..."
    if [ -d ~/.ssh ]; then
        cp -R ~/.ssh "$backup_dir/ssh_backup" 2>/dev/null
        echo "✅ SSH ключі збережено"
    else
        echo "⚠️  SSH директорія не знайдена"
    fi
    
    # Backup Windsurf конфігурації
    echo "\n[3/5] 🌊 Збереження Windsurf fingerprints..."
    if [ -d ~/Library/Application\ Support/Windsurf ]; then
        mkdir -p "$backup_dir/windsurf_backup"
        
        # Збереження важливих файлів
        cp ~/Library/Application\ Support/Windsurf/machineid "$backup_dir/windsurf_backup/" 2>/dev/null
        cp -R ~/Library/Application\ Support/Windsurf/User "$backup_dir/windsurf_backup/" 2>/dev/null
        cp -R ~/Library/Application\ Support/Windsurf/logs "$backup_dir/windsurf_backup/" 2>/dev/null
        
        echo "✅ Windsurf конфігурація збережена"
    else
        echo "⚠️  Windsurf директорія не знайдена"
    fi
    
    # Backup мережевих налаштувань
    echo "\n[4/5] 🌐 Збереження мережевих налаштувань..."
    
    # Поточні мережеві інтерфейси
    networksetup -listallhardwareports > "$backup_dir/network_ports.txt" 2>/dev/null
    
    # ARP таблиця
    arp -a > "$backup_dir/arp_table.txt" 2>/dev/null
    
    # Routing table
    netstat -rn > "$backup_dir/routing_table.txt" 2>/dev/null
    
    echo "✅ Мережеві налаштування збережено"
    
    # Backup системних налаштувань
    echo "\n[5/5] ⚙️  Збереження системних налаштувань..."
    
    # Timezone
    systemsetup -gettimezone > "$backup_dir/timezone.txt" 2>/dev/null
    
    # Locale
    locale > "$backup_dir/locale.txt" 2>/dev/null
    
    # System version
    sw_vers > "$backup_dir/system_version.txt" 2>/dev/null
    
    # CPU info
    sysctl -n machdep.cpu.brand_string > "$backup_dir/cpu_brand.txt" 2>/dev/null
    sysctl -n hw.ncpu > "$backup_dir/cpu_cores.txt" 2>/dev/null
    
    echo "✅ Системні налаштування збережено"
    
    # Створення metadata файлу
    cat > "$backup_dir/backup_metadata.json" << EOF
{
  "backup_name": "$backup_name",
  "created_at": "$(date -Iseconds)",
  "hostname": "$(scutil --get HostName 2>/dev/null || echo 'unknown')",
  "system_version": "$(sw_vers -productVersion)",
  "backup_type": "full_fingerprint",
  "files_count": $(find "$backup_dir" -type f | wc -l | tr -d ' ')
}
EOF
    
    echo "\n🎉 BACKUP ЗАВЕРШЕНО!"
    echo "📁 Розташування: $backup_dir"
    echo "📊 Файлів збережено: $(find "$backup_dir" -type f | wc -l | tr -d ' ')"
}

# Функція для відновлення з backup
restore_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        echo "❌ Помилка: не вказано ім'я backup для відновлення"
        list_backups
        return 1
    fi
    
    local backup_dir="$BACKUP_BASE_DIR/$backup_name"
    
    if [ ! -d "$backup_dir" ]; then
        echo "❌ Помилка: backup '$backup_name' не знайдено"
        list_backups
        return 1
    fi
    
    echo "\n🔄 ВІДНОВЛЕННЯ З BACKUP: $backup_name"
    echo "========================================"
    
    # Підтвердження
    echo "⚠️  УВАГА: Це замінить поточні налаштування!"
    echo "Продовжити? (y/N): "
    read -r confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "❌ Відновлення скасовано"
        return 1
    fi
    
    # Відновлення SSH ключів
    if [ -d "$backup_dir/ssh_backup" ]; then
        echo "\n[1/4] 🔑 Відновлення SSH ключів..."
        rm -rf ~/.ssh 2>/dev/null
        cp -R "$backup_dir/ssh_backup" ~/.ssh 2>/dev/null
        chmod 700 ~/.ssh 2>/dev/null
        chmod 600 ~/.ssh/* 2>/dev/null
        echo "✅ SSH ключі відновлено"
    fi
    
    # Відновлення Windsurf конфігурації
    if [ -d "$backup_dir/windsurf_backup" ]; then
        echo "\n[2/4] 🌊 Відновлення Windsurf конфігурації..."
        
        if [ -f "$backup_dir/windsurf_backup/machineid" ]; then
            mkdir -p ~/Library/Application\ Support/Windsurf
            cp "$backup_dir/windsurf_backup/machineid" ~/Library/Application\ Support/Windsurf/ 2>/dev/null
        fi
        
        if [ -d "$backup_dir/windsurf_backup/User" ]; then
            cp -R "$backup_dir/windsurf_backup/User" ~/Library/Application\ Support/Windsurf/ 2>/dev/null
        fi
        
        echo "✅ Windsurf конфігурація відновлена"
    fi
    
    # Відновлення мережевих налаштувань
    echo "\n[3/4] 🌐 Відновлення мережевих налаштувань..."
    
    if [ -f "$backup_dir/dns_wifi.txt" ]; then
        DNS_SERVERS=$(cat "$backup_dir/dns_wifi.txt")
        if [ "$DNS_SERVERS" != "There aren't any DNS Servers set on Wi-Fi." ]; then
            sudo networksetup -setdnsservers "Wi-Fi" $DNS_SERVERS 2>/dev/null
        fi
    fi
    
    if [ -f "$backup_dir/dns_ethernet.txt" ]; then
        DNS_SERVERS=$(cat "$backup_dir/dns_ethernet.txt")
        if [ "$DNS_SERVERS" != "There aren't any DNS Servers set on Ethernet." ]; then
            sudo networksetup -setdnsservers "Ethernet" $DNS_SERVERS 2>/dev/null
        fi
    fi
    
    echo "✅ Мережеві налаштування відновлено"
    
    # Відновлення системних налаштувань
    echo "\n[4/4] ⚙️  Відновлення системних налаштувань..."
    
    if [ -f "$backup_dir/timezone.txt" ]; then
        TIMEZONE=$(cat "$backup_dir/timezone.txt" | cut -d' ' -f3-)
        sudo systemsetup -settimezone "$TIMEZONE" 2>/dev/null
    fi
    
    if [ -f "$backup_dir/hostname.txt" ]; then
        HOSTNAME=$(cat "$backup_dir/hostname.txt")
        if [ -n "$HOSTNAME" ] && [ "$HOSTNAME" != "HostName: not set" ]; then
            sudo scutil --set HostName "$HOSTNAME" 2>/dev/null
        fi
    fi
    
    echo "✅ Системні налаштування відновлено"
    
    echo "\n🎉 ВІДНОВЛЕННЯ ЗАВЕРШЕНО!"
    echo "🔄 Рекомендується перезавантажити систему для повного застосування змін"
}

# Функція для списку backups
list_backups() {
    echo "\n📋 ДОСТУПНІ BACKUPS:"
    echo "==================="
    
    if [ ! -d "$BACKUP_BASE_DIR" ] || [ -z "$(ls -A "$BACKUP_BASE_DIR" 2>/dev/null)" ]; then
        echo "❌ Backups не знайдено"
        return 1
    fi
    
    for backup_dir in "$BACKUP_BASE_DIR"/*; do
        if [ -d "$backup_dir" ]; then
            backup_name=$(basename "$backup_dir")
            
            if [ -f "$backup_dir/backup_metadata.json" ]; then
                created_at=$(grep '"created_at"' "$backup_dir/backup_metadata.json" | cut -d'"' -f4)
                files_count=$(grep '"files_count"' "$backup_dir/backup_metadata.json" | cut -d':' -f2 | tr -d ' ,')
                echo "📁 $backup_name"
                echo "   Створено: $created_at"
                echo "   Файлів: $files_count"
            else
                echo "📁 $backup_name (без metadata)"
            fi
            echo ""
        fi
    done
}

# Функція для видалення backup
delete_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        echo "❌ Помилка: не вказано ім'я backup для видалення"
        list_backups
        return 1
    fi
    
    local backup_dir="$BACKUP_BASE_DIR/$backup_name"
    
    if [ ! -d "$backup_dir" ]; then
        echo "❌ Помилка: backup '$backup_name' не знайдено"
        return 1
    fi
    
    echo "⚠️  Видалити backup '$backup_name'? (y/N): "
    read -r confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "$backup_dir"
        echo "✅ Backup '$backup_name' видалено"
    else
        echo "❌ Видалення скасовано"
    fi
}

# Головне меню
case "${1:-menu}" in
    "create"|"backup")
        create_backup "$2"
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "list"|"ls")
        list_backups
        ;;
    "delete"|"rm")
        delete_backup "$2"
        ;;
    "menu"|*)
        echo "\n🛠️  STEALTH BACKUP SYSTEM"
        echo "========================"
        echo "Використання:"
        echo "  $0 create [name]     - Створити backup"
        echo "  $0 restore <name>    - Відновити з backup"
        echo "  $0 list              - Показати всі backups"
        echo "  $0 delete <name>     - Видалити backup"
        echo ""
        list_backups
        ;;
esac
