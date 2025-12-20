# Shell Integration Configuration Reference

## 📋 Конфігурація в `.vscode/settings.json`

Всі поточні налаштування Shell Integration для цього workspace:

### Активація & Декорації
```json
{
  // Основна активація Shell Integration
  "terminal.integrated.shellIntegration.enabled": true,
  
  // Показувати успіх ✓ / помилка ✗ декорації
  "terminal.integrated.shellIntegration.decorationsEnabled": true,
  
  // Стрічка-гід біля кожної команди (hover для деталей)
  "terminal.integrated.shellIntegration.showCommandGuide": true,
  
  // Максимум команд для збереження в історії
  "terminal.integrated.shellIntegration.history": 1000
}
```

### Навігація & Scroll
```json
{
  // Липка прокрутка: команда залишається на вершині
  "terminal.integrated.stickyScroll.enabled": true
}
```

### IntelliSense у терміналі
```json
{
  // Основна активація автодоповнення
  "terminal.integrated.suggest.enabled": true,
  
  // Виконати команду при Enter (замість вставки)
  "terminal.integrated.suggest.runOnEnter": true,
  
  // Показувати пропозиції автоматично поч типу
  "terminal.integrated.suggest.quickSuggestions": true,
  
  // Показувати при символах: -, /, etc
  "terminal.integrated.suggest.suggestOnTriggerCharacters": true,
  
  // Показувати статус бар в IntelliSense попап
  "terminal.integrated.suggest.showStatusBar": true,
  
  // Up/Down для історії замість листання по пропозиціях
  "terminal.integrated.suggest.upArrowNavigatesHistory": true,
  
  // Inline ghost text для пропозицій
  "terminal.integrated.suggest.inlineSuggestion": "auto",
  
  // Інтеграція з $CDPATH (для cd команди)
  "terminal.integrated.suggest.cdPath": true
}
```

---

## 🛠️ Конфігурація в `~/.zshrc`

```bash
# VS Code Shell Integration
[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"
```

**Пояснення:**
- `[[ "$TERM_PROGRAM" == "vscode" ]]` - перевіряє чи виконується в VS Code
- `code --locate-shell-integration-path zsh` - знаходить скрипт інтеграції
- `. "..."` - sources (завантажує) скрипт в поточну сесію

---

## 🎯 Можливості Shell Integration

### ✅ Що активується:

| Функція | Клавіша | Опис |
|---------|---------|------|
| **Команди Навігація** | `Cmd+Up` / `Cmd+Down` | Переміщення між командами |
| **Вибір Output** | `Shift+Cmd+Up/Down` | Вибір виводу команди |
| **Run Recent Command** | `Ctrl+Alt+R` | Пошук в історії |
| **Go Recent Directory** | `Cmd+G` | Перейти в папку |
| **IntelliSense** | `Ctrl+Space` | Автозаповнення |
| **Command Decorations** | - | Значки успіху/помилки |
| **Quick Fixes** | 💡 | Пропозиції виправлень |
| **Sticky Scroll** | - | Команда видима при прокрутці |
| **CWD Detection** | - | Виявлення поточної папки |

### ❌ Чого НЕ потрібно робити:

Не потрібно:
- ✅ Встановлювати додаткові модулі
- ✅ Змінювати PROMPT в zsh
- ✅ Робити особливу конфігурацію для кожного shell
- ✅ Вручну активувати в кожному терміналі

Всі правильно налаштовано автоматично!

---

## 🐛 Діагностика

### Перевірити стан інтеграції:

```bash
# Поточні змінні
echo $TERM_PROGRAM           # повинен бути: vscode
echo $VSCODE_SHELL_INTEGRATION  # повинен бути: 1

# Перевірити скрипт доступний
code --locate-shell-integration-path zsh
# Повинен вивести шлях до скрипту

# Перевірити в .zshrc
grep "VSCODE_SHELL_INTEGRATION" ~/.zshrc
# Повинен знайти нашу строку
```

### Яка якість інтеграції?

```
1. Наведіть мишу на вкладку терміналу
2. Побачите: "Shell integration quality: Rich"
3. Натисніть "Show Details" для більше інформації
```

Рівні якості:
- **Rich** ✅ - Ідеальна функціональність
- **Basic** ⚠️ - Обмежене детектування
- **None** ❌ - Інтеграція неактивна

---

## 📚 Ресурси

- **Налаштування**: [SHELL_INTEGRATION_SETUP.md](./SHELL_INTEGRATION_SETUP.md)
- **Приклади**: [SHELL_INTEGRATION_EXAMPLES.md](./SHELL_INTEGRATION_EXAMPLES.md)
- **VS Code Docs**: https://code.visualstudio.com/docs/terminal/shell-integration
- **Escape Sequences**: https://code.visualstudio.com/docs/terminal/shell-integration#_supported-escape-sequences

---

## 🎬 Швидкий старт

1. **Перезагрузіть VS Code** терміналь (закрийте/відкройте вкладку)
2. **Виконайте команду**:
   ```bash
   echo "Hello from Shell Integration!"
   ```
3. **Спробуйте функції**:
   - `Cmd+Up` - до попередньої команди
   - `Ctrl+Alt+R` - Run Recent Command
   - `ls` + `Ctrl+Space` - IntelliSense
   - Помилкова команда + клік на 🔴 - Quick Fix

Готово! 🚀

---

**Останнє оновлення:** 20 грудня 2025  
**Статус:** ✅ Повністю налаштовано і активно
