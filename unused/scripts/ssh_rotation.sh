#!/bin/zsh

echo "🔑 SSH KEYS ROTATION SYSTEM"
echo "=========================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Завантаження змінних середовища
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
fi

echo "\n[1/4] 🗑️  Очищення старих SSH ключів..."

# Backup існуючих ключів
if [ -d ~/.ssh ]; then
    BACKUP_DIR="$SCRIPT_DIR/ssh_backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -R ~/.ssh/* "$BACKUP_DIR/" 2>/dev/null
    echo "✅ Backup створено: $BACKUP_DIR"
fi

# Очищення SSH директорії
rm -rf ~/.ssh/known_hosts* 2>/dev/null
rm -rf ~/.ssh/id_* 2>/dev/null
rm -rf ~/.ssh/*.pub 2>/dev/null
rm -rf ~/.ssh/authorized_keys 2>/dev/null

echo "✅ Старі SSH ключі видалено"

echo "\n[2/4] 🔐 Генерація нових SSH ключів..."

# Створення SSH директорії
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Генерація різних типів ключів
KEY_TYPES=("ed25519" "rsa" "ecdsa")
SELECTED_TYPE=${KEY_TYPES[$((RANDOM % ${#KEY_TYPES[@]}))]}

# Генерація випадкового email для ключа
FAKE_EMAILS=("user@example.com" "dev@company.org" "admin@domain.net" "test@mail.com")
FAKE_EMAIL=${FAKE_EMAILS[$((RANDOM % ${#FAKE_EMAILS[@]}))]}

echo "🔄 Генерація $SELECTED_TYPE ключа з email: $FAKE_EMAIL"

case $SELECTED_TYPE in
    "ed25519")
        ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "$FAKE_EMAIL"
        ;;
    "rsa")
        KEY_SIZE=$((2048 + RANDOM % 2048)) # 2048-4096 bits
        ssh-keygen -t rsa -b $KEY_SIZE -f ~/.ssh/id_rsa -N "" -C "$FAKE_EMAIL"
        ;;
    "ecdsa")
        CURVE_SIZES=(256 384 521)
        CURVE_SIZE=${CURVE_SIZES[$((RANDOM % ${#CURVE_SIZES[@]}))]}
        ssh-keygen -t ecdsa -b $CURVE_SIZE -f ~/.ssh/id_ecdsa -N "" -C "$FAKE_EMAIL"
        ;;
esac

echo "✅ SSH ключ згенеровано: $SELECTED_TYPE"

echo "\n[3/4] 🛡️  Налаштування SSH конфігурації..."

# Створення SSH config з рандомізованими налаштуваннями
cat > ~/.ssh/config << EOF
# Auto-generated SSH config with randomized settings
Host *
    AddKeysToAgent yes
    UseKeychain yes
    IdentitiesOnly yes
    ServerAliveInterval $((30 + RANDOM % 60))
    ServerAliveCountMax $((3 + RANDOM % 5))
    ConnectTimeout $((10 + RANDOM % 20))
    TCPKeepAlive yes
    Compression yes
    CompressionLevel $((1 + RANDOM % 9))
    Protocol 2
    ForwardAgent no
    ForwardX11 no
    HashKnownHosts yes
    StrictHostKeyChecking ask
    UserKnownHostsFile ~/.ssh/known_hosts
    ControlMaster auto
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlPersist $((300 + RANDOM % 300))
EOF

chmod 600 ~/.ssh/config

echo "✅ SSH конфігурація налаштована"

echo "\n[4/4] 🔄 Рандомізація SSH агента..."

# Перезапуск SSH агента з новими ключами
if pgrep -f ssh-agent > /dev/null; then
    pkill -f ssh-agent
fi

# Запуск нового SSH агента
eval "$(ssh-agent -s)"

# Додавання нового ключа до агента
if [ -f ~/.ssh/id_ed25519 ]; then
    ssh-add ~/.ssh/id_ed25519 2>/dev/null
elif [ -f ~/.ssh/id_rsa ]; then
    ssh-add ~/.ssh/id_rsa 2>/dev/null
elif [ -f ~/.ssh/id_ecdsa ]; then
    ssh-add ~/.ssh/id_ecdsa 2>/dev/null
fi

echo "✅ SSH агент перезапущено з новими ключами"

# Створення фейкового SSH fingerprint для Windsurf
mkdir -p ~/Library/Application\ Support/Windsurf/User/globalStorage
cat > ~/Library/Application\ Support/Windsurf/User/globalStorage/ssh_profile.json << EOF
{
  "key_type": "$SELECTED_TYPE",
  "key_size": "$KEY_SIZE",
  "email": "$FAKE_EMAIL",
  "fingerprint": "$(ssh-keygen -lf ~/.ssh/id_$SELECTED_TYPE.pub 2>/dev/null | awk '{print $2}' || echo 'SHA256:randomfingerprint')",
  "created": "$(date -Iseconds)",
  "agent_pid": "$SSH_AGENT_PID"
}
EOF

echo "\n🎉 SSH ROTATION ЗАВЕРШЕНО!"
echo "================================"
echo "✅ Старі ключі видалено та збережено в backup"
echo "✅ Новий $SELECTED_TYPE ключ згенеровано"
echo "✅ SSH конфігурація рандомізована"
echo "✅ SSH агент перезапущено"
echo ""
echo "📋 Інформація про новий ключ:"
echo "   Тип: $SELECTED_TYPE"
echo "   Email: $FAKE_EMAIL"
if [ -f ~/.ssh/id_$SELECTED_TYPE.pub ]; then
    echo "   Публічний ключ:"
    cat ~/.ssh/id_$SELECTED_TYPE.pub | head -c 50
    echo "..."
fi
echo ""
echo "⚠️  ВАЖЛИВО: Додайте новий публічний ключ до ваших Git сервісів!"
