#!/bin/bash

# Script to regenerate project structure with last response
# Usage: ./regenerate_structure.sh "Last response text here"

RESPONSE="${1:-}"
RESPONSE_FILE=".last_response.txt"
OUTPUT_FILE="CODEMAP.md"

# Save last response if provided
if [ -n "$RESPONSE" ]; then
    echo "$RESPONSE" > "$RESPONSE_FILE"
fi

# Remove old output file
if [ -f "$OUTPUT_FILE" ]; then
    rm "$OUTPUT_FILE"
fi

# Generate new structure
python3 generate_structure.py
