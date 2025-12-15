#!/bin/zsh

echo "=================================================="
echo "🔄 ВІДНОВЛЕННЯ VS CODE З БЕКАПУ"
echo "=================================================="

# Пошук останнього бекапу
LATEST_BACKUP=$(ls -td /tmp/vscode_backup_* 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ Бекапи не знайдено в /tmp"
    echo "💡 Можливо система була перезавантажена?"
    echo "📋 Спробуйте використати збережені конфігурації з configs_vscode/"
    exit 1
fi

echo "📦 Знайдено бекап: $LATEST_BACKUP"
echo "📅 Дата: $(date -r $(echo $LATEST_BACKUP | grep -o '[0-9]*$') +%Y-%m-%d\ %H:%M:%S)"
echo ""

# Відновлення Machine-ID
if [ -f "$LATEST_BACKUP/machineid.bak" ]; then
    echo "🔄 Відновлення machine-id..."
    mkdir -p ~/Library/Application\ Support/Code
    cp "$LATEST_BACKUP/machineid.bak" ~/Library/Application\ Support/Code/machineid
    echo "✅ Machine-ID відновлено"
else
    echo "⚠️  Machine-ID бекап не знайдено"
fi

# Відновлення Storage файлів
for backup_file in "$LATEST_BACKUP"/**/storage.json.bak; do
    if [ -f "$backup_file" ]; then
        # Визначити оригінальний шлях
        if [[ "$backup_file" == *"User_globalStorage"* ]]; then
            RESTORE_PATH=~/Library/Application\ Support/Code/User/globalStorage/storage.json
        else
            RESTORE_PATH=~/Library/Application\ Support/Code/storage.json
        fi
        
        echo "🔄 Відновлення storage: $(basename $RESTORE_PATH)"
        mkdir -p "$(dirname "$RESTORE_PATH")"
        cp "$backup_file" "$RESTORE_PATH"
        echo "✅ Відновлено: $RESTORE_PATH"
    fi
done

# Відновлення hostname з оригінальної конфігурації
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ORIGINAL_CONFIG="$SCRIPT_DIR/configs_vscode/original"

if [ -f "$ORIGINAL_CONFIG/hostname.txt" ]; then
    ORIGINAL_HOSTNAME=$(cat "$ORIGINAL_CONFIG/hostname.txt")
    echo "\n🔄 Відновлення hostname на: $ORIGINAL_HOSTNAME"
    sudo scutil --set HostName "$ORIGINAL_HOSTNAME"
    sudo scutil --set LocalHostName "$ORIGINAL_HOSTNAME"
    sudo scutil --set ComputerName "$ORIGINAL_HOSTNAME"
    sudo dscacheutil -flushcache
    sudo killall -HUP mDNSResponder 2>/dev/null
    echo "✅ Hostname відновлено"
fi

# Відновлення MAC-адреси
if [ -f "$ORIGINAL_CONFIG/mac_address.txt" ]; then
    ORIGINAL_MAC=$(cat "$ORIGINAL_CONFIG/mac_address.txt")
    ACTIVE_INTERFACE=$(route -n get default 2>/dev/null | grep 'interface:' | awk '{print $2}')
    if [ -n "$ACTIVE_INTERFACE" ] && [ -n "$ORIGINAL_MAC" ]; then
        echo "🔄 Відновлення MAC-адреси: $ORIGINAL_MAC"
        sudo ifconfig "$ACTIVE_INTERFACE" ether "$ORIGINAL_MAC"
        echo "✅ MAC-адресу відновлено"
    fi
fi

echo "\n=================================================="
echo "✅ ВІДНОВЛЕННЯ ЗАВЕРШЕНО!"
echo "=================================================="
echo "💡 Рекомендації:"
echo "   • Перезапустіть VS Code для застосування змін"
echo "   • Перевірте що ваш обліковий запис відновлено"
echo "=================================================="
