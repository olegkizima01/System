#!/bin/zsh

# ═══════════════════════════════════════════════════════════════
#  🔧 WINDSURF MANUAL CLEANUP GUIDE
#  Інструкції для ручного очищення Windsurf (оскільки він активний)
# ═══════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔧 WINDSURF MANUAL CLEANUP GUIDE"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "⚠️  Windsurf зараз активний, тому автоматичне очищення не виконується."
echo ""
echo "📋 Для повного очищення Windsurf виконайте наступні кроки:"
echo ""

echo "1️⃣  Закрийте Windsurf повністю"
echo "   - Закрийте всі вікна Windsurf"
echo "   - Перевірте в Activity Monitor, що процеси Windsurf не запущені"
echo ""

echo "2️⃣  Запустіть повне очищення:"
echo "   ./scripts/cleanup/independent_editor_cleanup.sh windsurf"
echo ""

echo "3️⃣  Або виконайте ручне очищення проблемних файлів:"
echo ""

WINDSURF_BASE="$HOME/Library/Application Support/Windsurf"

# Перевірка проблемних файлів
echo "🔍 Перевірка проблемних файлів:"

# state.vscdb
if [ -f "$WINDSURF_BASE/User/globalStorage/state.vscdb" ]; then
    echo "❌ Знайдено: state.vscdb (потрібно видалити)"
    echo "   rm -f \"$WINDSURF_BASE/User/globalStorage/state.vscdb\""
else
    echo "✅ state.vscdb відсутній - добре"
fi

# Local Storage
if [ -d "$WINDSURF_BASE/Local Storage" ]; then
    echo "❌ Знайдено: Local Storage (потрібно видалити)"
    echo "   rm -rf \"$WINDSURF_BASE/Local Storage\""
else
    echo "✅ Local Storage відсутній - добре"
fi

# Browser IndexedDB
BROWSER_WINDSURF=$(find ~/Library/Application\ Support/Google/Chrome -path "*/IndexedDB/*windsurf*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$BROWSER_WINDSURF" -gt 0 ]; then
    echo "❌ Знайдено: $BROWSER_WINDSURF файлів в Chrome IndexedDB"
    echo "   find ~/Library/Application\\ Support/Google/Chrome -path \"*/IndexedDB/*windsurf*\" -exec rm -rf {} + 2>/dev/null"
else
    echo "✅ Chrome IndexedDB очищено - добре"
fi

echo ""
echo "4️⃣  Після очищення запустіть перевірку:"
echo "   ./scripts/cleanup/check_identifier_cleanup.sh"
echo ""

echo "💡 Рекомендації:"
echo "   - Перезавантажте систему після очищення"
echo "   - Очищення github.com файлів не обов'язкове (це нормальні дані)"
echo "   - Machine-ID файли вже створені правильно"
echo ""

echo "════════════════════════════════════════════════════════════"
