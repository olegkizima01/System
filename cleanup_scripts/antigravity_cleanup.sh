#!/bin/bash

# Antigravity Cleanup Script
# This script cleans up the Antigravity disk image to free up space
# Usage: ./antigravity_cleanup.sh

set -e

echo "Starting Antigravity cleanup..."

# Check if Antigravity is mounted
if mount | grep -q "/Volumes/Antigravity"; then
    echo "Antigravity is mounted. Unmounting..."
    hdiutil detach /Volumes/Antigravity || true
fi

# Path to the Antigravity disk image
ANTIGRAVITY_DMG="/Users/dev/Desktop/Antigravity.dmg"

if [ ! -f "$ANTIGRAVITY_DMG" ]; then
    echo "Error: Antigravity.dmg not found at $ANTIGRAVITY_DMG"
    exit 1
fi

echo "Converting to read-write format..."
hdiutil convert "$ANTIGRAVITY_DMG" -format UDRW -o "/Users/dev/Desktop/Antigravity_rw.dmg"

echo "Mounting read-write image..."
hdiutil attach "/Users/dev/Desktop/Antigravity_rw.dmg" -mountpoint /Volumes/Antigravity_rw

echo "Cleaning up extensions and node_modules..."
rm -rf /Volumes/Antigravity_rw/Antigravity.app/Contents/Resources/app/extensions
rm -rf /Volumes/Antigravity_rw/Antigravity.app/Contents/Resources/app/node_modules

echo "Unmounting read-write image..."
hdiutil detach /Volumes/Antigravity_rw

echo "Creating final read-only image..."
hdiutil convert "/Users/dev/Desktop/Antigravity_rw.dmg" -format UDRO -o "/Users/dev/Desktop/Antigravity_clean.dmg"

echo "Mounting cleaned image..."
hdiutil attach "/Users/dev/Desktop/Antigravity_clean.dmg" -mountpoint /Volumes/Antigravity

echo "Cleanup complete!"
df -h /Volumes/Antigravity

echo "Replacing original image..."
mv "/Users/dev/Desktop/Antigravity.dmg" "/Users/dev/Desktop/Antigravity_backup_$(date +%Y%m%d).dmg"
mv "/Users/dev/Desktop/Antigravity_clean.dmg" "/Users/dev/Desktop/Antigravity.dmg"

echo "Cleanup finished successfully!"
