# Shell Integration - Примери використання

## 1️⃣ Навігація між командами

```bash
# Натисніть Cmd+Up щоб перейти до попередньої команди
# Натисніть Cmd+Down щоб перейти до наступної команди
npm install

# Тепер натисніть Cmd+Up щоб повернутися до npm install
python -m pytest tests/

# Натисніть Cmd+Up знову...
git status
```

### Практичний приклад: Навігація по помилці

```bash
# Цикл розробки:
npm install    # Команда 1
npm run build  # Команда 2 (помилка - 🔴)
npm run build  # Команда 3 (повтор)

# Натисніть Cmd+Up щоб повернутися до команди з помилкою
# Натисніть на 🔴 іконку → "Rerun Command"
```

## 2️⃣ Використання Recent Commands

```bash
# Натисніть Ctrl+Alt+R (або у Mac Cmd+Ctrl+R)
# Побачите список недавних команд

# Приклад:
# Recent commands:
#   › git commit -m "fix: shell integration"
#   › npm test
#   › python -m pytest tests/core/
#   › git push origin main

# Введіть фільтр: pytest
# Тільки pytest команди залишаться
# Натисніть Enter щоб виконати
```

## 3️⃣ Quick Fixes (лампочка 💡)

### Приклад 1: Git branch upstream

```bash
$ git push
fatal: The current branch feature is not tracking a remote branch.

# 💡 Лампочка з'являється
# Click → "Push with --set-upstream"
# Команда виконується автоматично!
```

### Приклад 2: Port already in use

```bash
$ npm start
Error: EADDRINUSE: address already in use :::3000

# 💡 Лампочка з'являється
# Click → "Kill process on port 3000 and rerun"
# Процес вбивається, команда виконується!
```

### Приклад 3: Git suggestions

```bash
$ git chekout main
git: 'chekout' is not a git command. Did you mean one of these?
        checkout

# 💡 Лампочка з'являється
# Click → "Run: git checkout"
```

## 4️⃣ IntelliSense у терміналі

### Автозаповнення файлів

```bash
$ cd /Users/dev/Documents/Git
# Натисніть Tab або Ctrl+Space
# Побачите:
#   ▶ GitHub/
#   ▶ System/
#   ▶ Projects/

$ cat SHELL_
# Натисніть Tab → SHELL_INTEGRATION_SETUP.md
```

### Аргументи команд

```bash
$ npm run -
# Натисніть Tab або Ctrl+Space
# Побачите доступні скрипти:
#   ▶ build
#   ▶ dev
#   ▶ test

$ python -m 
# Натисніть Tab → модулі
#   ▶ venv
#   ▶ pytest
#   ▶ pip
```

### Git branch completions

```bash
$ git checkout 
# Натисніть Tab → список гілок
#   ▶ main
#   ▶ develop
#   ▶ feature/shell-integration
```

## 5️⃣ Sticky Scroll для довгих виводів

```bash
# Виконайте команду з великим виводом
$ npm run build

# Результат:
# ┌─────────────────────────────────────────┐
# │ npm run build                           │  ← Sticky scroll
# ├─────────────────────────────────────────┤
# │ Building project...
# │ Compiling 1234 files...
# │ Processing assets...
# │ [████████████████░░░░] 75%
# │ ... (більш текст внизу)
# │
# │ (прокручуйте вниз)
# │
# │ Build complete! ✓

# Натисніть на sticky scroll → перейдіть до команди
```

## 6️⃣ Go to Recent Directory

```bash
# Натисніть Cmd+G
# Побачите недавні каталоги:
#   ▶ /Users/dev/Documents/GitHub/System
#   ▶ /Users/dev/Documents/GitHub/Projects
#   ▶ /opt/homebrew/bin
#   ▶ /Users/dev/.venv/lib/python3.11

# Введіть фільтр: System
# Натисніть Enter → cd /Users/dev/Documents/GitHub/System

# Або Alt+Enter → не виконує cd, просто вставляє в терміналь
```

## 7️⃣ Command Decorations (декорації успіху/помилок)

```bash
# Успішна команда:
✅ $ echo "Hello"
   Hello

# Помилка команди:
❌ $ npm invalid-command
   npm: error: unknown command

# Натисніть на іконку:
# ✅ → Copy Output, Copy as HTML, Rerun
# ❌ → Copy Output, Copy as HTML, Rerun (або Quick Fix)
```

## 8️⃣ Accessibility Mode

```bash
# Якщо увімкнено accessibility режим:
# Ctrl+R        → Run Recent Command (замість надсилання Ctrl+R в shell)
# Ctrl+Alt+R    → Надіслати Ctrl+R в shell (для зворотного пошуку)

# Звуковий сигнал 🔔 коли команда помиляється
# Навігація через Cmd+F2 для accessibility buffer
```

## 9️⃣ Command History Integration

Система збирає історію з кількох джерел:

```bash
# Поточний сеанс
~/.zsh_history (VS Code відслідковує)

# Попередні сеанси (збережено VS Code)
Ctrl+Alt+R → Previous session section

# Shell history file
~/.zsh_history інтегрується з поточною сесією
```

## 🔟 Поточна директорія в VS Code

```bash
# Shell integration повідомляє VS Code про поточну папку
# Це дозволяє:
$ ls package.json

# Натисніть на посилання → відкривається саме package.json
# (замість пошуку по всьому workspace)

# Приклад:
$ find . -name "*.py" | head -3
./core/trinity.py
./core/context7.py
./core/vibe_assistant.py

# Натисніть на кожне посилання → відкривається у VS Code
# Автоматично знає де шукати завдяки CWD!
```

## 🎯 Поради та хитрощі

### Tip 1: Копіювання виводу з Recent Commands

```bash
Ctrl+Alt+R → Виберіть команду → 📋 Icon → Копіює вивід
```

### Tip 2: Фіксування важливих команд

```bash
Ctrl+Alt+R → Виберіть команду → 📌 Pin icon
# Команда залишається на вершині списку!
```

### Tip 3: Запис без виконання

```bash
Ctrl+Alt+R → Виберіть команду → Alt+Enter
# Команда вставляється в терміналь, але НЕ виконується
# Потім можете відредагувати та натиснути Enter
```

### Tip 4: Fuzzy search в Recent Commands

```bash
Ctrl+Alt+R → Натисніть 🔍 button в пошуку
# Переходить з точного пошуку на fuzzy
pytest → (fuzzy) → знаходить "pytests", "test_pytest", etc
```

### Tip 5: Clear Cached Globals

```bash
# Якщо додали нові команди в PATH але не з'являються в IntelliSense:
Command Palette (Cmd+Shift+P) → "Terminal: Clear Suggest Cached Globals"
```

## ⚙️ Налаштування для цього workspace

Вкл. в `.vscode/settings.json`:

```json
{
  "terminal.integrated.shellIntegration.enabled": true,
  "terminal.integrated.shellIntegration.decorationsEnabled": true,
  "terminal.integrated.shellIntegration.showCommandGuide": true,
  "terminal.integrated.stickyScroll.enabled": true,
  "terminal.integrated.suggest.enabled": true,
  "terminal.integrated.suggest.upArrowNavigatesHistory": true
}
```

Означає що для вас:
- ✅ Декорації показуються завжди
- ✅ Стрічка-гід видима біля команд
- ✅ Sticky scroll для довгих виводів
- ✅ IntelliSense активна в терміналі
- ✅ Up/Down для історії замість листання в IntelliSense

## 🚀 Готово до використання!

Shell Integration вже інтегрована і активна. Спробуйте:

```bash
# 1. Виконайте кілька команд
git status
npm test
python -m pytest

# 2. Натисніть Cmd+Up кілька разів (навігація між командами)

# 3. Натисніть Ctrl+Alt+R (Run Recent Command)

# 4. Натисніть Cmd+G (Go to Recent Directory)

# 5. Введіть ls та натисніть Ctrl+Space (IntelliSense)

# 6. Спробуйте помилкову команду та клікніть на 🔴 для Quick Fix
```

Наслідуйтесь потужністю Shell Integration! 🎉
