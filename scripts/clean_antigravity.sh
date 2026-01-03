#!/bin/bash

# Скрипт для 100% очищення диска Antigravity з збереженням можливості роботи
# Запускати ТІЛЬКИ коли Antigravity змонтовано як /Volumes/Antigravity

echo "=== Очищення Antigravity (VSCode OSS) ==="
echo "Поточний стан диска:"
df -h /Volumes/Antigravity

ANTIGRAVITY="/Volumes/Antigravity"

if [ ! -d "$ANTIGRAVITY" ]; then
    echo "ПОМИЛКА: Antigravity не змонтовано за шляхом $ANTIGRAVITY"
    echo "Перевірте, чи відкрито редактор Antigravity."
    exit 1
fi

echo
echo "Видаляємо накопичені дані (логи, кеші, тимчасові файли)..."

# 1. Логи VSCode та розширень
rm -rf "$ANTIGRAVITY"/.vscode-oss/logs/*
rm -rf "$ANTIGRAVITY"/.vscode-oss/CachedExtensions/*
rm -rf "$ANTIGRAVITY"/.vscode-oss/CachedExtensionVSIXs/*
rm -rf "$ANTIGRAVITY"/.vscode-oss/cache/*
rm -rf "$ANTIGRAVITY"/.vscode-oss/Code\ Cache/*

# 2. Тимчасові файли та снапшоти
rm -rf "$ANTIGRAVITY"/.tmp/*
rm -rf "$ANTIGRAVITY"/tmp/*
rm -rf "$ANTIGRAVITY"/*.tmp
find "$ANTIGRAVITY" -name "*.bak" -delete
find "$ANTIGRAVITY" -name "~*" -delete

# 3. Кеш Node.js, npm, yarn (якщо використовується)
rm -rf "$ANTIGRAVITY"/.npm/_cacache/*
rm -rf "$ANTIGRAVITY"/.cache/yarn/*
rm -rf "$ANTIGRAVITY"/.node-gyp/*

# 4. Старі логи та дампи (якщо є)
rm -rf "$ANTIGRAVITY"/logs/*
rm -rf "$ANTIGRAVITY"/crashpad/*
rm -rf "$ANTIGRAVITY"/dumps/*

# 5. Кеш шрифтів, іконок, GPU
rm -rf "$ANTIGRAVITY"/GPUCache/*
rm -rf "$ANTIGRAVITY"/Code\ Cache/*
rm -rf "$ANTIGRAVITY"/CachedData/*

# 6. Інші відомі великі теки, що безпечно чистити
rm -rf "$ANTIGRAVITY"/.vscode-oss/user/workspaceStorage/*/state.vscdb*
rm -rf "$ANTIGRAVITY"/.vscode-oss/user/workspaceStorage/*/backups/*

echo
echo "Очищення завершено!"
echo "Стан диска після очищення:"
df -h /Volumes/Antigravity

echo
echo "Тепер можна продовжувати роботу в Antigravity."
echo "Редактор автоматично відтворить необхідні кеші при наступному запуску."
echo "Якщо помилка 'Agent terminated' повториться — запустіть скрипт ще раз."