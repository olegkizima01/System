#!/bin/zsh
###############################################################################
# MikroTik WiFi & MAC Address Spoofing Cleanup Script (Final v3.0 – Jan 2026)
# Надійно змінює SSID, subnet на MikroTik + авто-підключення на macOS
###############################################################################

PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PATH
set -e
# Ensure xtrace is disabled in case the parent shell exported debugging (prevents lines like: current='')
set +x

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Config
SCRIPT_DIR="$(cd "$(dirname "${0:A}")/.." && pwd)"
REPO_ROOT="$SCRIPT_DIR"
LOG_FILE="/tmp/mikrotik_wifi_spoof_$(date +%Y%m%d_%H%M%S).log"

[ -f "$REPO_ROOT/.env" ] && { set -a; source "$REPO_ROOT/.env"; set +a; }

export SUDO_ASKPASS="$SCRIPT_DIR/sudo_helper.sh"
export SUDO_ASKPASS_REQUIRE=force

MIKROTIK_HOST="${MIKROTIK_HOST:-192.168.88.1}"
MIKROTIK_USER="${MIKROTIK_USER:-admin}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_ed25519}"
GUEST_WIFI_INTERFACES=("wifi3" "wifi4")
GUEST_WIFI_PASSWORD="00000000"
MAX_RETRIES=4
WIFI_INTERFACE=""
# Options
# Set ALLOW_MAC_CHANGE=1 in .env to attempt manual MAC changes (may fail on macOS 13+). Default: disabled (0).
ALLOW_MAC_CHANGE="${ALLOW_MAC_CHANGE:-0}"
# If enabled, treat presence of an IP on the Wi‑Fi interface as successful association when SSID cannot be detected.
IP_FALLBACK_ENABLED="${IP_FALLBACK_ENABLED:-1}"


# Output functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ MikroTik WiFi & MAC Address Spoofing Cleanup Module ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

log() {
    local level="$1"; shift
    echo "$(date +'%Y-%m-%d %H:%M:%S') [$level] $@" >> "$LOG_FILE"
    case "$level" in INFO) print_info "$@" ;; SUCCESS) print_success "$@" ;; WARNING) print_warning "$@" ;; ERROR) print_error "$@" ;; esac
}

# MikroTik connection check
check_mikrotik_connection() {
    log INFO "Перевірка з'єднання з MikroTik..."
    local key_path="${SSH_KEY/#\~/$HOME}"
    local i=1
    while [ $i -le $MAX_RETRIES ]; do
        local out rc
        out=$(timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "${MIKROTIK_USER}@${MIKROTIK_HOST}" "system identity print" 2>&1)
        rc=$?
        if [ $rc -eq 0 ]; then
            log SUCCESS "MikroTik доступний"
            return 0
        fi
        log WARNING "Спроба $i: не вдалось підключитись до ${MIKROTIK_HOST} (rc=$rc). SSH output: $out"
        ((i++))
        sleep 1
    done
    log WARNING "MikroTik недоступний після $MAX_RETRIES спроб"
    log INFO "Спробуйте: ssh -i ${SSH_KEY/#\~/$HOME} ${MIKROTIK_USER}@${MIKROTIK_HOST} ('system identity print') для налагодження"
    return 1
}

generate_ssid() {
    local suffix=$(head -c 8 /dev/urandom | base64 | tr -d '=+/\"' | tr '[:lower:]' '[:upper:]' | cut -c1-8)
    echo "Guest_${suffix}"
}

generate_subnet() {
    echo "10.$((RANDOM % 254 + 1)).$((RANDOM % 254 + 1))"
}

generate_mac() {
    printf '02:%02X:%02X:%02X:%02X:%02X\n' $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256)) $((RANDOM%256))
}

# Окремі безпечні оновлення MikroTik
update_mikrotik_pool() {
    local subnet="$1"
    local range="${subnet}.100-${subnet}.200"
    local key_path="${SSH_KEY/#\~/$HOME}"

    log INFO "Оновлення IP pool → $range"
    local i=1
    while [ $i -le $MAX_RETRIES ]; do
        local out rc
        # Try to update existing pool
        out=$(timeout 15 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "${MIKROTIK_USER}@${MIKROTIK_HOST}" "/ip pool set [find name=\"guest_pool\"] ranges=\"${range}\"" 2>&1)
        rc=$?
        if [ $rc -eq 0 ]; then
            log SUCCESS "IP pool оновлено (set)"
            return 0
        fi
        log INFO "Спроба $i: set не вдалось (rc=$rc). SSH output: $out"

        # Try to create the pool
        out=$(timeout 15 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "${MIKROTIK_USER}@${MIKROTIK_HOST}" "/ip pool add name=\"guest_pool\" ranges=\"${range}\"" 2>&1)
        rc=$?
        if [ $rc -eq 0 ]; then
            log SUCCESS "IP pool створено (add)"
            return 0
        fi
        log WARNING "Спроба $i: add не вдалась (rc=$rc). SSH output: $out"

        ((i++))
        sleep 2
    done
    log ERROR "Не вдалося оновити або створити IP pool після $MAX_RETRIES спроб"
    return 1
}

update_mikrotik_ssid() {
    local ssid="$1"
    local key_path="${SSH_KEY/#\~/$HOME}"
    local cmd=""
    for iface in "${GUEST_WIFI_INTERFACES[@]}"; do
        cmd+="/interface wifi set [find name=\"$iface\"] configuration.ssid=\"$ssid\"; "
    done

    log INFO "Оновлення SSID → $ssid"
    local i=1
    while [ $i -le $MAX_RETRIES ]; do
        local out
        out=$(timeout 15 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "${MIKROTIK_USER}@${MIKROTIK_HOST}" "$cmd" 2>&1)
        local rc=$?
        if [ $rc -eq 0 ]; then
            log SUCCESS "SSID оновлено"
            return 0
        fi
        log WARNING "Спроба $i: не вдалося оновити SSID (rc=$rc). SSH output: $out"
        ((i++))
        sleep 2
    done
    log WARNING "Не вдалося оновити SSID після $MAX_RETRIES спроб (можливо, з'єднання розірвано — це нормально)"
    return 1
}

# Wi-Fi interface detection
detect_wifi_interface() {
    WIFI_INTERFACE=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2; exit}')
    if [ -n "$WIFI_INTERFACE" ] && ifconfig "$WIFI_INTERFACE" &>/dev/null; then
        log INFO "Виявлено Wi-Fi інтерфейс: $WIFI_INTERFACE"
        return 0
    fi
    WIFI_INTERFACE="en1"
    log WARNING "Використовується fallback інтерфейс: en1"
    return 1
}

# Get the user-facing Wi‑Fi service name (e.g., "Wi-Fi") for a given device
get_wifi_service_name() {
    if [ -z "$WIFI_INTERFACE" ]; then
        return 1
    fi

    local svc
    svc=$(networksetup -listallhardwareports 2>/dev/null | awk -v dev="$WIFI_INTERFACE" '
        /Hardware Port:/ { hp = $0; sub(/^Hardware Port: /, "", hp); next }
        /Device:/ { if ($2 == dev) { print hp; exit } }
    ')

    # Trim whitespace
    svc=$(echo "$svc" | xargs)
    if [ -n "$svc" ]; then
        echo "$svc"
        return 0
    fi
    return 1
}

# Get current connected SSID using multiple fallbacks (networksetup -> airport -> ipconfig)
get_current_ssid() {
    local svc out ssid
    svc=$(get_wifi_service_name || true)

    # 1) networksetup (localized output)
    if [ -n "$svc" ]; then
        out=$(networksetup -getairportnetwork "$svc" 2>/dev/null || true)
        ssid=$(echo "$out" | awk -F': ' '{print $NF}' | xargs)
        case "$ssid" in
            ""|"You are not associated with an AirPort network."|*not*|*не*|*немає*) ssid="" ;;
            *) [ -n "$ssid" ] && { echo "$ssid"; return 0; } ;;
        esac
    fi

    # 2) airport binary (private framework)
    local airport_bin="/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    if [ -x "$airport_bin" ]; then
        out=$("$airport_bin" -I 2>/dev/null || true)
        ssid=$(echo "$out" | awk -F': ' '/ SSID:/{print $2; exit}' | xargs)
        [ -n "$ssid" ] && { echo "$ssid"; return 0; }
    fi

    # 3) ipconfig summary (another fallback)
    if [ -n "$WIFI_INTERFACE" ]; then
        out=$(ipconfig getsummary "$WIFI_INTERFACE" 2>/dev/null || true)
        ssid=$(echo "$out" | awk -F': ' '/SSID:/{print $2; exit}' | xargs)
        [ -n "$ssid" ] && { echo "$ssid"; return 0; }
    fi

    return 1
}

# Helper: get IPv4 address for the Wi‑Fi interface (used as a fallback success indicator)
get_interface_ip() {
    local ip
    ip=$(ifconfig "$WIFI_INTERFACE" 2>/dev/null | awk '/inet /{print $2; exit}')
    [ -n "$ip" ] && { echo "$ip"; return 0; }
    return 1
}

# MAC change attempt (with realistic warning)
change_mac_address() {
    local mac="$1"
    detect_wifi_interface

    if [ "${ALLOW_MAC_CHANGE:-0}" != "1" ]; then
        log INFO "Зміна MAC пропущена (ALLOW_MAC_CHANGE != 1). Щоб дозволити, встановіть ALLOW_MAC_CHANGE=1 у .env"
        return 0
    fi

    log INFO "Спроба зміни MAC → $mac на $WIFI_INTERFACE"

    set +e
    echo "$SUDO_PASSWORD" | sudo -S ifconfig "$WIFI_INTERFACE" down >/dev/null 2>&1
    echo "$SUDO_PASSWORD" | sudo -S ifconfig "$WIFI_INTERFACE" ether "$mac" >/dev/null 2>&1
    local rc=$?
    echo "$SUDO_PASSWORD" | sudo -S ifconfig "$WIFI_INTERFACE" up >/dev/null 2>&1
    set -e

    if [ $rc -eq 0 ]; then
        log SUCCESS "MAC успішно змінено"
    else
        log WARNING "Ручна зміна MAC не вдалася (очікувано на macOS 13+)"
        print_warning "Рекомендовано: Налаштування → Мережа → Wi-Fi → Деталі → Використовувати приватну адресу Wi-Fi = Вимкнено"
    fi
}

# Повний перезапуск Wi-Fi адаптера
restart_wifi_adapter() {
    log INFO "Перезапуск Wi-Fi адаптера..."
    set +e

    # Try quick disassociate using airport utility
    /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -z >/dev/null 2>&1 || true

    # Try to find the network service name (e.g., "Wi-Fi") for graceful power toggle
    local wifi_service
    wifi_service=$(networksetup -listallhardwareports 2>/dev/null | awk -v dev="$WIFI_INTERFACE" '/Hardware Port:/{hp=$0; getline; if($0 ~ "Device: "dev){gsub(/Hardware Port: /,"",hp); print hp; exit}}')

    if [ -n "$wifi_service" ]; then
        echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportpower "$wifi_service" off >/dev/null 2>&1 || true
        sleep 3
        echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportpower "$wifi_service" on >/dev/null 2>&1 || true
    else
        # Fallback: use lower-level interface down/up
        echo "$SUDO_PASSWORD" | sudo -S ifconfig "$WIFI_INTERFACE" down >/dev/null 2>&1 || true
        sleep 3
        echo "$SUDO_PASSWORD" | sudo -S ifconfig "$WIFI_INTERFACE" up >/dev/null 2>&1 || true
    fi

    sleep 6
    set -e
    log SUCCESS "Wi-Fi адаптер перезапущено"
}

# Надійне підключення
connect_to_wifi() {
    set +x  # defensive: disable inherited xtrace to avoid printing empty assignments like "current=''"
    local ssid="$1"
    local pass="$2"
    log INFO "Підключення до $ssid..."

    set +e
    echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportnetwork "$WIFI_INTERFACE" "$ssid" "$pass" >/dev/null 2>&1
    local rc=$?
    set -e

    # Poll for association for up to ~20 seconds
    local attempts=10
    local waited=0
    while [ $attempts -gt 0 ]; do
        local current
        current=$(get_current_ssid || true)
        if [ "$current" = "$ssid" ]; then
            local ip=$(ifconfig "$WIFI_INTERFACE" 2>/dev/null | awk '/inet / {print $2}' | head -1)
            log SUCCESS "Успішно підключено до $ssid (IP: ${ip:-невідомо})"
            print_success "✓ Підключено до $ssid"
            return 0
        fi

        # Fallback: SSID lookup can fail on macOS 13+/14+/15+ due to privacy; if enabled, treat presence of an IP as success
        if [ -z "$current" ] && [ "${IP_FALLBACK_ENABLED:-1}" = "1" ]; then
            local ip
            ip=$(get_interface_ip || true)
            if [ -n "$ip" ]; then
                log SUCCESS "SSID не видно, але Wi‑Fi має IP: $ip — вважаємо підключення успішним"
                print_success "✓ Підключено до $ssid (IP: $ip)"
                return 0
            fi
        fi

        sleep 2
        waited=$((waited+2))
        attempts=$((attempts-1))
    done

    log WARNING "Після ${waited}s не вдалося підтвердити підключення до $ssid (очікували: $ssid, маємо: '${current:-<none>}')"
    return 1
}

# Автоматичне підключення з ретраями
auto_reconnect() {
    set +x  # defensive: disable inherited xtrace while performing retries/polling
    local ssid="$1"
    local pass="$2"
    local mac="$3"

    print_header
    log INFO "Запуск автоматичного підключення до $ssid"

    restart_wifi_adapter
    [ -n "$mac" ] && change_mac_address "$mac"
    sleep 5

    # If already connected, exit early
    local cur
    cur=$(get_current_ssid || true)
    if [ "$cur" = "$ssid" ]; then
        log SUCCESS "Вже підключено до $ssid"
        return 0
    fi

    local i=1
    while [ $i -le $MAX_RETRIES ]; do
        if connect_to_wifi "$ssid" "$pass"; then
            return 0
        fi
        # Re-check: sometimes association completes despite earlier check failing
        cur=$(get_current_ssid || true)
        if [ "$cur" = "$ssid" ]; then
            log SUCCESS "Підключення насправді відбулося до $ssid"
            return 0
        fi
        log WARNING "Спроба підключення $i невдала — повтор через 6 сек"
        sleep 6
        ((i++))
    done

    log ERROR "Не вдалося автоматично підключитися після $MAX_RETRIES спроб"
    print_error "Підключіться вручну до: $ssid (пароль: 00000000)"
    return 1
}

# Основна логіка spoof-auto
main() {
    [ -z "$SUDO_PASSWORD" ] && { print_error "SUDO_PASSWORD не задано в .env!"; exit 1; }

    case "${1:-spoof-auto}" in
        spoof-auto)
            print_header
            detect_wifi_interface

            # Generate new values regardless of remote availability
            local new_ssid=$(generate_ssid)
            local new_subnet=$(generate_subnet)
            local new_mac=$(generate_mac)

            print_info "Згенеровано нову конфігурацію:"
            echo "   WiFi SSID: $new_ssid"
            echo "   IP Subnet: ${new_subnet}.0/24"
            echo "   MAC Address: $new_mac"
            echo

            if check_mikrotik_connection; then
                # Спочатку пул (безпечніше)
                if ! update_mikrotik_pool "$new_subnet"; then
                    log WARNING "Оновлення пулу не вдалося; продовжимо локальне підключення"
                fi
                # Потім SSID (може розірвати з'єднання)
                if ! update_mikrotik_ssid "$new_ssid"; then
                    log WARNING "Оновлення SSID не вдалося; продовжимо локальне підключення"
                fi
            else
                log WARNING "MikroTik недоступний — пропускаємо віддалені зміни"
            fi

            print_header
            print_success "Spoofing завершено (локально)!"
            print_info "Новий SSID: $new_ssid"
            print_info "Новий subnet: ${new_subnet}.0/24"
            print_info "Пароль: 00000000 (без змін)"
            echo

            # Always attempt to reconnect locally even if MikroTik updates failed
            auto_reconnect "$new_ssid" "$GUEST_WIFI_PASSWORD" "$new_mac"
            ;;

        reconnect)
            detect_wifi_interface
            auto_reconnect "${2:-Guest_W97MZ5HT}" "$GUEST_WIFI_PASSWORD" ""
            ;;

        status)
            print_header
            ifconfig | grep -A1 "$WIFI_INTERFACE" || true
            echo
            /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
            ;;

        diagnose)
            # Helpful diagnostics to debug SSID detection and IP fallback
            print_header
            detect_wifi_interface
            echo "Device: $WIFI_INTERFACE"
            echo "Service: $(get_wifi_service_name || true)"
            echo
            echo "networksetup raw:"; networksetup -getairportnetwork "$(get_wifi_service_name || true)" 2>/dev/null || true
            echo
            echo "airport -I:"; /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null || true
            echo
            echo "get_current_ssid: $(get_current_ssid || true)"
            echo "get_interface_ip: $(get_interface_ip || true)"
            ;;

        *)
            print_error "Використовуйте: $0 spoof-auto | reconnect [SSID] | status | diagnose\nДодатково: встановіть ALLOW_MAC_CHANGE=1 у .env щоб дозволити ручну зміну MAC (може не працювати на macOS 13+)."
            ;;
    esac

    log INFO "Скрипт завершено. Лог: $LOG_FILE"
}

main "$@"