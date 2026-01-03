#!/bin/zsh

###############################################################################
# MikroTik WiFi & MAC Address Spoofing Cleanup Script
# Randomly changes guest WiFi SSID, IP subnet, and local MAC on macOS
# Last module in cleanup sequence - overrides previous network changes
###############################################################################

# Забезпечуємо базовий PATH для системних утиліт
PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PATH

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${0:A}")/.." && pwd)"
REPO_ROOT="$SCRIPT_DIR"
PYTHON_MODULE="${SCRIPT_DIR}/providers/mikrotik_wifi_spoofing.py"
LOG_FILE="/tmp/mikrotik_wifi_spoof_$(date +%s).log"

# Load environment variables
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
fi

# Setup sudo with password from .env
export SUDO_ASKPASS="$SCRIPT_DIR/sudo_helper.sh"
export SUDO_ASKPASS_REQUIRE=force

MIKROTIK_HOST="${MIKROTIK_HOST:-192.168.88.1}"
MIKROTIK_USER="${MIKROTIK_USER:-admin}"
SSH_KEY="~/.ssh/id_ed25519"

# Guest WiFi interfaces (found via /interface wifi print)
GUEST_WIFI_INTERFACES=("wifi3" "wifi4")
GUEST_WIFI_PASSWORD="00000000"

# Network interface for auto-reconnect
WIFI_INTERFACE="en1"  # Change this to your WiFi interface if needed

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  MikroTik WiFi & MAC Address Spoofing Cleanup Module       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if MikroTik is accessible
check_mikrotik_connection() {
    print_info "Checking MikroTik connection..."
    
    local key_path="${SSH_KEY/#\~/$HOME}"
    
    if timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 \
        "${MIKROTIK_USER}@${MIKROTIK_HOST}" \
        "system identity print" > /dev/null 2>&1; then
        print_success "MikroTik is accessible"
        return 0
    else
        print_warning "Cannot connect to MikroTik at ${MIKROTIK_HOST}"
        print_info "Ensure SSH key is added to MikroTik: ssh ${MIKROTIK_USER}@${MIKROTIK_HOST}"
        # Return 0 to allow script to continue with local cleanup steps
        return 0
    fi
}

# Generate random WiFi SSID
generate_ssid() {
    local prefix="Guest"
    local suffix=$(head -c 6 /dev/urandom | base64 | tr -d '=/' | tr '[:lower:]' '[:upper:]')
    echo "${prefix}_${suffix}"
}

# Generate random subnet
generate_subnet() {
    local second=$((RANDOM % 254 + 1))
    local third=$((RANDOM % 254 + 1))
    echo "10.${second}.${third}"
}

# Generate random MAC address (locally administered)
generate_mac() {
    printf '02:%02X:%02X:%02X:%02X:%02X\n' \
        $((RANDOM % 256)) \
        $((RANDOM % 256)) \
        $((RANDOM % 256)) \
        $((RANDOM % 256)) \
        $((RANDOM % 256))
}

# Update MikroTik guest WiFi SSID
update_mikrotik_ssid() {
    local new_ssid="$1"
    local key_path="${SSH_KEY/#\~/$HOME}"
    print_info "Updating MikroTik WiFi SSID to: ${new_ssid}"
    
    # Update all guest WiFi interfaces
    for iface in "${GUEST_WIFI_INTERFACES[@]}"; do
        timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 \
            "${MIKROTIK_USER}@${MIKROTIK_HOST}" \
            "/interface wifi set [find name=\"${iface}\"] configuration.ssid=\"${new_ssid}\"" \
            2>&1 || return 1
    done
    
    print_success "WiFi SSID updated on all guest interfaces"
    return 0
}

# Update MikroTik IP pool
update_mikrotik_ip_pool() {
    local new_subnet="$1"
    local key_path="${SSH_KEY/#\~/$HOME}"
    local pool_range="${new_subnet}.100-${new_subnet}.200"
    
    print_info "Updating MikroTik IP pool to: ${pool_range}"
    
    # Try to update existing pool
    timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 \
        "${MIKROTIK_USER}@${MIKROTIK_HOST}" \
        "/ip pool set [find name=\"guest_pool\"] ranges=\"${pool_range}\"" \
        2>&1 || {
        # Create new pool if it doesn't exist
        print_info "Creating new IP pool..."
        timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 \
            "${MIKROTIK_USER}@${MIKROTIK_HOST}" \
            "/ip pool add name=\"guest_pool\" ranges=\"${pool_range}\"" \
            2>&1 || return 1
    }
    
    print_success "IP pool updated"
    return 0
}

# Change local MAC address
change_mac_address() {
    local new_mac="$1"
    local interface=""
    
    print_info "Detecting network interface..."
    
    # Prefer detected Wi-Fi interface if available
    if [ -n "$WIFI_INTERFACE" ]; then
        interface="$WIFI_INTERFACE"
    else
        # Find a physical en* interface with an ether address (skip virtual ones like utun)
        interface=$(ifconfig -l 2>/dev/null | tr ' ' '\n' | grep -E '^en[0-9]+' | while read -r ifc; do
            if ifconfig "$ifc" 2>/dev/null | grep -q "ether "; then
                echo "$ifc" && break
            fi
        done)
    fi

    if [ -z "$interface" ]; then
        # Try to find any active interface with IP (fallback)
        interface=$(netstat -rn | grep default | awk '{print $NF}' | head -1)
    fi
    
    if [ -z "$interface" ]; then
        print_error "Could not determine network interface"
        return 1
    fi
    
    print_info "Using interface: ${interface}"
    print_info "Changing MAC address to: ${new_mac}"
    
    # Change MAC address using sudo with ASKPASS
    if echo "$SUDO_PASSWORD" | sudo -S ifconfig "$interface" ether "$new_mac" 2>&1; then
        print_success "MAC address changed to ${new_mac}"
        return 0
    else
        print_warning "Standard ifconfig method failed for $interface"
        # If interface appears to be virtual (utun, gif, bridge, lo) do not try further
        if echo "$interface" | grep -qE '^(utun|gif|bridge|lo)'; then
            print_error "Interface $interface is virtual; cannot change MAC"
            return 1
        fi
        # Try a secondary approach (just log the attempt)
        print_info "MAC address spoofing attempted for $new_mac on $interface"
        return 1
    fi
}

# Disconnect from WiFi
disconnect_wifi() {
    print_info "Disconnecting from current WiFi network..."
    
    # Use networksetup to get WiFi interface
    local wifi_service=$(networksetup -listnetworkserviceorder | grep "Wi-Fi" | head -1 | awk '{print $NF}' | tr -d '()')
    
    if [ -z "$wifi_service" ]; then
        wifi_service="Wi-Fi"
    fi
    
    # Get current SSID using airport command
    local current_ssid=$(/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | grep " SSID:" | awk -F': ' '{print $2}')
    
    if [ -n "$current_ssid" ] && [ "$current_ssid" != "Not Associated" ]; then
        print_info "Current network: $current_ssid"
        
        # Turn off WiFi with sudo
        for iface in en0 en1 en2; do
            echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportpower "$iface" off 2>/dev/null && break || true
        done
        sleep 2
        
        print_success "Disconnected from WiFi"
        return 0
    else
        print_info "Already disconnected or no WiFi available"
        return 0
    fi
}

# Detect Wi-Fi hardware interface
detect_wifi_interface() {
    # Prefer the device from networksetup (works on modern macOS)
    local dev
    dev=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2; exit}')
    if [ -n "$dev" ]; then
        WIFI_INTERFACE="$dev"
        print_info "Detected Wi-Fi interface: ${WIFI_INTERFACE}"
        return 0
    fi

    # Fallback: pick a physical en* interface with an ether address
    for iface in en0 en1 en2 en3; do
        if ifconfig "$iface" &>/dev/null && ifconfig "$iface" | grep -q "ether "; then
            WIFI_INTERFACE="$iface"
            print_info "Fallback Wi-Fi interface: ${WIFI_INTERFACE}"
            return 0
        fi
    done

    print_warning "Could not detect Wi-Fi hardware interface; WIFI_INTERFACE remains '${WIFI_INTERFACE:-en1}'"
    return 1
}

# Connect to WiFi (uses sudo and handles failures without aborting whole script)
connect_to_wifi() {
    local ssid="$1"
    local password="$2"

    print_info "Connecting to: $ssid with password: $password"

    detect_wifi_interface || print_warning "Proceeding with WIFI_INTERFACE=${WIFI_INTERFACE:-en1}"

    # Turn on WiFi first with sudo (allow failures)
    set +e
    for iface in "${WIFI_INTERFACE}" en0 en1 en2; do
        if [ -n "$iface" ]; then
            echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportpower "$iface" on 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Turned on Wi-Fi on $iface"
                break
            fi
        fi
    done

    # Try to connect using networksetup with sudo
    echo "$SUDO_PASSWORD" | sudo -S networksetup -setairportnetwork "${WIFI_INTERFACE}" "$ssid" "$password" 2>/dev/null
    local status=$?
    set -e

    if [ $status -eq 0 ]; then
        print_success "Connection command sent to: $ssid"
        sleep 5

        # Verify connection
        local current=$(/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | grep " SSID:" | awk -F': ' '{print $2}')

        if [ "$current" == "$ssid" ]; then
            print_success "✓ Successfully connected to: $current"
            return 0
        else
            print_warning "⚠ Connection initiated but not yet confirmed (may take a few seconds)"
            print_info "Expected: $ssid"
            print_info "Current: $current"
            return 0
        fi
    else
        print_warning "Connection attempt failed (exit $status); this may require manual intervention"
        return 1
    fi
}

# Duplicate connect_to_wifi removed: consolidated into the sudo-enabled implementation above to ensure correct permissions and error handling.
# (Removing duplicates prevents unexpected function overwrites.)

# Auto-reconnect to new WiFi after spoofing
auto_reconnect() {
    local new_ssid="$1"
    local password="$2"
    
    print_header
    print_info "Starting auto-reconnect sequence..."
    echo
    
    # Disconnect from current network
    if ! disconnect_wifi; then
        print_warning "Failed to disconnect"
    fi
    
    # Wait a moment
    print_info "Waiting for network changes to propagate..."
    sleep 3
    
    # Connect to new network
    if connect_to_wifi "$new_ssid" "$password"; then
        print_success "Auto-reconnect completed!"
        
        # Verify connection
        sleep 2
        local current=$(airport -I 2>/dev/null | grep " SSID:" | awk -F': ' '{print $2}')
        if [ "$current" == "$new_ssid" ]; then
            print_success "✓ Successfully connected to: $current"
        else
            print_warning "⚠ Connection may not be established yet"
            print_info "Current SSID: $current"
        fi
        
        return 0
    else
        print_error "Failed to connect to new network"
        return 1
    fi
}

# Main spoofing function
spoof_all() {
    print_header
    
    # Check connection first
    if ! check_mikrotik_connection; then
        print_error "Aborting: Cannot connect to MikroTik"
        return 1
    fi
    
    # Generate new values
    local new_ssid=$(generate_ssid)
    local new_subnet=$(generate_subnet)
    local new_mac=$(generate_mac)
    
    print_info "Generated new configuration:"
    echo "  WiFi SSID:    ${new_ssid}"
    echo "  IP Subnet:    ${new_subnet}.0/24"
    echo "  MAC Address:  ${new_mac}"
    echo
    
    # Update MikroTik
    print_info "Updating MikroTik configuration..."
    if ! update_mikrotik_ssid "$new_ssid"; then
        print_warning "Failed to update WiFi SSID"
    fi
    
    if ! update_mikrotik_ip_pool "$new_subnet"; then
        print_warning "Failed to update IP pool"
    fi
    
    # Change MAC address
    print_info "Updating local MAC address..."
    if ! change_mac_address "$new_mac"; then
        print_warning "Failed to change MAC address"
    fi
    
    print_header
    print_success "Spoofing completed!"
    print_info "New WiFi SSID: ${new_ssid}"
    print_info "New Subnet:    ${new_subnet}.0/24"
    print_info "New MAC:       ${new_mac}"
    print_info "Password:      00000000 (unchanged)"
    echo
    
    return 0
}

# Show current status
show_status() {
    print_header
    
    if check_mikrotik_connection; then
        print_info "Retrieving MikroTik WiFi status..."
        local key_path="${SSH_KEY/#\~/$HOME}"
        timeout 10 ssh -i "$key_path" -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 \
            "${MIKROTIK_USER}@${MIKROTIK_HOST}" \
            "/interface wifi print" || true
    fi
    
    echo
    print_info "Local MAC addresses:"
    ifconfig | grep ether || true
    echo
}

# Main
main() {
    # Load sudo password from environment if not already set
    if [ -z "$SUDO_PASSWORD" ]; then
        print_error "⚠️  SUDO_PASSWORD not found in .env"
        print_info "Please add SUDO_PASSWORD to your .env file"
        print_info "Example: SUDO_PASSWORD=your_password"
        return 1
    fi
    
    case "${1:-spoof-auto}" in
        spoof)
            spoof_all
            ;;
        spoof-auto)
            # Generate once and use for both spoofing and reconnecting
            print_header
            
            # Check connection first
            if ! check_mikrotik_connection; then
                print_error "Aborting: Cannot connect to MikroTik"
                return 1
            fi
            
            # Generate new values
            local new_ssid=$(generate_ssid)
            local new_subnet=$(generate_subnet)
            local new_mac=$(generate_mac)
            
            print_info "Generated new configuration:"
            echo "  WiFi SSID:    ${new_ssid}"
            echo "  IP Subnet:    ${new_subnet}.0/24"
            echo "  MAC Address:  ${new_mac}"
            echo
            
            # Update MikroTik
            print_info "Updating MikroTik configuration..."
            if ! update_mikrotik_ssid "$new_ssid"; then
                print_warning "Failed to update WiFi SSID"
            fi
            
            if ! update_mikrotik_ip_pool "$new_subnet"; then
                print_warning "Failed to update IP pool"
            fi
            
            # Change MAC address
            print_info "Updating local MAC address..."
            if ! change_mac_address "$new_mac"; then
                print_warning "Failed to change MAC address"
            fi
            
            print_header
            print_success "Spoofing completed!"
            print_info "New WiFi SSID: ${new_ssid}"
            print_info "New Subnet:    ${new_subnet}.0/24"
            print_info "New MAC:       ${new_mac}"
            print_info "Password:      00000000 (unchanged)"
            echo
            
            # Now auto-reconnect using the SAME SSID
            auto_reconnect "$new_ssid" "$GUEST_WIFI_PASSWORD"
            ;;
        status)
            show_status
            ;;
        reconnect)
            local ssid="${2:-Guest}"
            local password="${3:-$GUEST_WIFI_PASSWORD}"
            auto_reconnect "$ssid" "$password"
            ;;
        disconnect)
            disconnect_wifi
            ;;
        help|--help|-h)
            echo "Usage: $0 [COMMAND]"
            echo
            echo "Commands:"
            echo "  spoof           Execute WiFi and MAC spoofing only"
            echo "  spoof-auto      Execute spoofing and auto-reconnect to new network (default)"
            echo "  reconnect SSID  Reconnect to specific WiFi network (default: Guest, pwd: 00000000)"
            echo "  disconnect      Disconnect from current WiFi"
            echo "  status          Show current WiFi and MAC status"
            echo "  help            Show this help message"
            echo
            echo "Examples:"
            echo "  $0 spoof-auto                  # Spoof and reconnect"
            echo "  $0 reconnect Guest_ABC123      # Connect to specific network"
            echo "  $0 status                      # Check current status"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for more information"
            return 1
            ;;
    esac
}

main "$@"
