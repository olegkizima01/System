#!/bin/bash

# check_identifier_cleanup.sh - Checks current platform identifiers
echo "🔍 Checking system identifiers..."

echo "-----------------------------------"
echo "Hostname: $(hostname)"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "MAC (en0): $(ifconfig en0 | grep ether | awk '{print $2}' || echo 'N/A')"
    echo "Model: $(sysctl -n hw.model || echo 'N/A')"
fi
echo "OS: $OSTYPE"
echo "User: $USER"
echo "-----------------------------------"

echo "✅ Identifier check completed."
