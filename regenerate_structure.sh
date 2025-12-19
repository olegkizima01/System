#!/bin/bash

# Define output file
OUTPUT_FILE="project_structure_final.txt"

# Write Header
echo "## Metadata" > "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Program Execution Logs" >> "$OUTPUT_FILE"
# Optional: Include tail of logs if needed, for now just a placeholder or empty
echo "(See logs/cli.log for details)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Project Structure" >> "$OUTPUT_FILE"

# Generate tree structure
if command -v tree &> /dev/null; then
    # Exclude common ignores to keep it clean
    tree -I '__pycache__|*.pyc|.git|.venv|.DS_Store|.agent|.gemini|node_modules|dist|build|coverage' >> "$OUTPUT_FILE"
else
    # Fallback if tree is not installed
    find . -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g' >> "$OUTPUT_FILE"
fi

echo "✓ Project structure regenerated in $OUTPUT_FILE"
