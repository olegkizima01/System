#!/bin/zsh

# Enhanced Stealth Monitor - Real-time fingerprint randomization
echo "🕵️  ENHANCED STEALTH MONITOR - Real-time Protection"
echo "=================================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Перевірка активності Windsurf
check_windsurf_activity() {
    pgrep -f "Windsurf" > /dev/null
}

# Розширена функція для рандомізації fingerprints
randomize_fingerprints() {
    local interval=300  # 5 хвилин замість 30
    
    while true; do
        echo "[$(date)] 🔄 Розширена рандомізація fingerprints..."
        
        # Перевірка активності Windsurf
        if check_windsurf_activity; then
            echo "[$(date)] 🌊 Windsurf активний - застосовуємо агресивну рандомізацію"
            interval=180  # 3 хвилини при активності
        else
            interval=600  # 10 хвилин при неактивності
        fi
        
        # Зміна User-Agent для WebView (більш реалістичні)
        OS_VERSIONS=("10_15_7" "11_6_8" "12_6_1" "13_0_1")
        CHROME_VERSIONS=("108" "109" "110" "111" "112")
        SAFARI_VERSIONS=("605.1.15" "537.36")
        
        SELECTED_OS=${OS_VERSIONS[$((RANDOM % ${#OS_VERSIONS[@]}))]}
        SELECTED_CHROME=${CHROME_VERSIONS[$((RANDOM % ${#CHROME_VERSIONS[@]}))]}
        SELECTED_SAFARI=${SAFARI_VERSIONS[$((RANDOM % ${#SAFARI_VERSIONS[@]}))]}
        
        RANDOM_UA="Mozilla/5.0 (Macintosh; Intel Mac OS X $SELECTED_OS) AppleWebKit/$SELECTED_SAFARI (KHTML, like Gecko) Chrome/$SELECTED_CHROME.0.$((4000 + RANDOM % 1000)).$((100 + RANDOM % 200)) Safari/$SELECTED_SAFARI"
        
        # Оновлення WebView налаштувань
        if [ -d ~/Library/Application\ Support/Windsurf ]; then
            mkdir -p ~/Library/Application\ Support/Windsurf/User
            
            # Розширений fingerprint spoofing
            cat > ~/Library/Application\ Support/Windsurf/User/runtime_protection.js << EOF
// Real-time fingerprint randomization
(function() {
    // Dynamic User-Agent
    Object.defineProperty(navigator, 'userAgent', {
        get: () => '$RANDOM_UA',
        configurable: true
    });
    
    // Random screen dimensions
    Object.defineProperty(screen, 'width', {
        get: () => $((1920 + RANDOM % 100)),
        configurable: true
    });
    Object.defineProperty(screen, 'height', {
        get: () => $((1080 + RANDOM % 100)),
        configurable: true
    });
    
    // Random timezone offset
    Date.prototype.getTimezoneOffset = () => $((RANDOM % 720 - 360));
    
    // Random canvas noise
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(...args) {
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, args);
    };
    
    console.log('[$(date)] 🕵️ Runtime protection updated');
})();
EOF
        fi
        
        # Рандомізація MAC адреси (якщо можливо)
        ACTIVE_INTERFACE=\$(route -n get default 2>/dev/null | grep 'interface:' | awk '{print \$2}')
        if [ -n "\$ACTIVE_INTERFACE" ] && [ \$((RANDOM % 10)) -eq 0 ]; then
            NEW_MAC=\$(printf '02:%02x:%02x:%02x:%02x:%02x' \$((RANDOM%256)) \$((RANDOM%256)) \$((RANDOM%256)) \$((RANDOM%256)) \$((RANDOM%256)))
            sudo ifconfig "\$ACTIVE_INTERFACE" down 2>/dev/null
            sudo ifconfig "\$ACTIVE_INTERFACE" ether "\$NEW_MAC" 2>/dev/null
            sudo ifconfig "\$ACTIVE_INTERFACE" up 2>/dev/null
            echo "[$(date)] 🔄 MAC адреса оновлена: \$NEW_MAC"
        fi
        
        # Рандомізація системного часу (мікро-зміни)
        sudo date -u $(date -u -v+$((RANDOM % 10))S +%m%d%H%M%y) 2>/dev/null
        
        # Очищення тимчасових кешів
        rm -rf /tmp/com.apple.* 2>/dev/null
        rm -rf /tmp/windsurf_* 2>/dev/null
        
        # Очищення DNS кешу періодично
        if [ $((RANDOM % 5)) -eq 0 ]; then
            sudo dscacheutil -flushcache 2>/dev/null
            echo "[$(date)] 🔄 DNS кеш очищено"
        fi
        
        # Рандомізація процесів (зміна пріоритетів)
        if check_windsurf_activity; then
            WINDSURF_PID=$(pgrep -f "Windsurf" | head -1)
            if [ -n "$WINDSURF_PID" ]; then
                sudo renice $((RANDOM % 10 - 5)) $WINDSURF_PID 2>/dev/null
            fi
        fi
        
        echo "[$(date)] ✅ Fingerprints оновлено (наступне оновлення через ${interval}s)"
        
        # Динамічний інтервал
        sleep $interval
    done
}

# Запуск у фоні
randomize_fingerprints &
MONITOR_PID=$!

echo "✅ Stealth Monitor запущено (PID: $MONITOR_PID)"
echo "🔄 Fingerprints будуть оновлюватися кожні 30 хвилин"

# Збереження PID для можливості зупинки
echo $MONITOR_PID > /tmp/stealth_monitor.pid
