---
description: Authoritative guide for Project Atlas architecture, Cognitive 2.0 meta-planning logic, Active Retrieval, and the continuous learning principles of the Trinity Graph runtime. Updated December 2025.
---

# Project Atlas: Архітектура, Workflow та Основні Принципи  
**Актуальний стан: Грудень 2025 (Cognitive 2.1 + Trinity Improvements v1.0)**

Цей документ є **єдиним джерелом правди** про фундаментальні принципи роботи системи Atlas (Trinity Runtime).

⚠️ **Останнє оновлення:** 20 грудня 2025 - Додано Pydantic валідацію, State Logging, MyPy типізація

---

## 1. Основні принципи роботи (Core Principles)

Atlas — це не просто автоматизатор, а **автономний мультиагентний оператор macOS**, що керується наступними принципами:

1.  **Автономна Навігація (Autonomous Navigation)**  
    Здатність самостійно приймати рішення в умовах невизначеності, використовуючи цикл "Сприйняття → Планування → Дія → Верифікація".
    
2.  **Управління Мисленням (Meta-Planning 2.0)**  
    Агент керує власною стратегією: обирає рівень верифікації, режим відновлення та тип плану. **Новинка**: Pydantic валідація конфігурації.
    
3.  **Візуальне Сприйняття (Vision-First)**  
    Використання скріншотів та Computer Vision як Ground Truth. Підтримка multi-monitor та диференційного аналізу.
    
4.  **Конфіденційність та Стелс-режим (Privacy & Stealth)**  
    Система очищення слідів та підміна ідентифікаторів (`spoofing`).
    
5.  **Постійне Навчання (Continuous Learning 2.0)**  
    Система витягує досвід (як успішний, так і негативний) та зберігає його у **Knowledge Base** з оцінкою впевненості та статусом.
    
6.  **Деталізоване Логування (State Logging)**  
    Система логує весь процес ініціалізації та переходи для простої діагностики. Логи: `logs/trinity_state_*.log`

---

## 2. Архітектура Trinity Runtime (LangGraph)

Центральна нервова система Atlas базується на циклічному графі. Будь-яка успішна чи завершена місія обов'язково проходить через вузол навчання.

```mermaid
graph TD
    START((START)) --> MP[meta_planner<br/>Голова/Стратег/Контролер]
    MP -->|Policy & Strategy| C7[context7<br/>Контекст-Менеджер<br/>+ Sliding Window]
    C7 -->|Normalized Context| A[atlas<br/>Архітектор Плану]
    MP -->|план готовий| T[tetyana<br/>Виконавець]
    MP -->|план готовий| G[grisha<br/>Верифікатор]
    A --> MP
    T --> G
    G --> MP
    MP -->|завершено| K[knowledge<br/>Екстрактор Досвіду]
    K --> END((END))
    
    subgraph Memory Layers
        WM[Working Memory]
        EM[Episodic Memory]
        SM[Semantic Memory]
    end
    
    MP -.-> WM
    WM -.-> EM
    EM -.-> SM
```

### 2.1 Trinity Agents & Layers

-   **Meta-Planner** (`_meta_planner_node`): Головний оркестратор. Виконує **Active Retrieval** та фільтрує спогади.
-   **Context7** (`context7`): **Explicit Context Manager**. Готує контекст, керує бюджетом токенів та ін'єктує стратегічні політики. **Новинка**: Sliding Window з пріоритезацією недавніх кроків.
-   **Atlas** (`_atlas_node`): Архітектор тактичного плану. Отримує *нормалізований* контекст від Context7 для розробки кроків.
-   **Tetyana** (`_tetyana_node`): Виконавець (Native/GUI/Playwright).
-   **Grisha** (`_grisha_node`): Верифікатор. У разі успіху або критичного провалу ініціює перехід до навчання. Використовує `enhanced_vision_analysis` для візуальної верифікації.
-   **Knowledge** (`_knowledge_node`): **Етап рефлексії**. Зберігає досвід (`success`/`failed`).

---

## 3. Ключові Підсистеми (Core Components)

### 3.1 Hierarchical Memory System

Трирівнева система пам'яті (`core/memory.py`):

| Шар | Тривалість | Призначення |
|:---|:---|:---|
| **Working Memory** | Поточна сесія | Тимчасові дані, активний контекст |
| **Episodic Memory** | Декілька сесій | Конкретні події, взаємодії, результати |
| **Semantic Memory** | Постійно | Консолідовані знання, патерни, стратегії |

```python
memory = HierarchicalMemory()
memory.add_to_working("current_task", {...})
memory.consolidate_to_semantic()  # Promote important knowledge
```

### 3.2 Context7 Sliding Window

Оптимізований менеджер контексту (`core/context7.py`):

- **Token Budget**: Динамічне керування бюджетом токенів
- **Priority Weighting**: Пріоритезація недавніх кроків та критичної інформації
- **ContextMetrics**: Відстеження використання токенів

### 3.3 Agent Message Protocol

Структурована комунікація між агентами (`core/agent_protocol.py`):

- **AgentMessage**: Типізовані повідомлення з метаданими
- **PriorityMessageQueue**: Черга з пріоритетами
- **MessageRouter**: Маршрутизація та доставка

### 3.4 Parallel Tool Executor

Паралельне виконання незалежних кроків (`core/parallel_executor.py`):

- **DependencyAnalyzer**: Аналіз залежностей між кроками
- **Thread Pool**: Паралельне виконання незалежних операцій
- **StepResult**: Відстеження статусу та метрик

---

## 4. Vision Pipeline (Enhanced)

Розширена система візуального аналізу (`system_ai/tools/vision.py`, `core/vision_context.py`):

### 4.1 DifferentialVisionAnalyzer

| Функція | Опис |
|:---|:---|
| `capture_all_monitors()` | Multi-monitor screenshot через Quartz/mss |
| `analyze_frame()` | Диференційний аналіз + OCR |
| `_generate_diff_image()` | Візуалізація змінених регіонів |

### 4.2 VisionContextManager

- **Trend Detection**: Відстеження тренду змін (increasing/decreasing/stable)
- **Active Region Tracking**: Hot zones з частими змінами
- **Frame History**: До 10 кадрів з метаданими
- **Step Verification**: `get_diff_summary_for_step()` для верифікації дій

```python
# Використання агентами
result = EnhancedVisionTools.capture_and_analyze(
    multi_monitor=True,
    generate_diff_image=True
)
context_manager.update_context(result)
```

---

## 5. Мета-планінг та Пам'ять (Meta-planning 2.0)

| Параметр | Значення | Опис |
| :--- | :--- | :--- |
| **Strategy** | `linear`, `rag_heavy`, `aggressive` | Тип побудови плану. |
| **Active Retrieval** | `retrieval_query` | Оптимізований запит, сформований Meta-Planner. |
| **Anti-patterns** | `status: failed` | Система уникає стратегій, які призвели до помилок у минулому. |
| **Confidence Score** | `0.1` ... `1.0` | Оцінка надійності спогаду на основі кількості правок та кроків. |
| **Source Tracking** | `trinity_runtime`, `user` | Відстеження походження знання. |

---

## 6. MCP Фондація (Інструменти)

Центральний реєстр `MCPToolRegistry` надає агентам доступ до:

### Внутрішні Інструменти (Internal)
-   **Automation (Unified)**: Shell, AppleScript, Shortcuts, Mouse/Keyboard
-   **System Cleanup**: Очищення слідів, логів, спуфінг (Stealth Mode)
-   **Recorder Control**: Програмне керування записом сесій
-   **Desktop/Vision**: `enhanced_vision_analysis`, `vision_analysis_with_context`, `compare_images`

### Зовнішні MCP Сервери (External)
-   **Playwright MCP**: Повний контроль браузера (headless/headful)
-   **PyAutoGUI MCP**: Альтернативна емуляція вводу
-   **Context7 MCP**: Доступ до документації бібліотек
-   **SonarQube MCP**: Quality gate та аналіз коду

---

## 7. TUI та Теми

### 7.1 Доступні теми (14 тем)

| Категорія | Теми |
|:---|:---|
| **Classic** | monaco, dracula, nord, gruvbox |
| **Modern** | catppuccin, tokyo-night, one-dark, rose-pine |
| **Vibrant** | cyberpunk, aurora, midnight-blue, solarized-dark |
| **Special** | hacker-vibe (dimmed) |

### 7.2 Навігація TUI
- **Ctrl+T**: Швидка зміна теми
- **Settings → Appearance**: Вибір теми з превʼю
- **Custom themes**: `~/.system_cli/themes/*.json`

---

## 8. Trinity Improvements v1.0 (Грудень 2025)

**Нові можливості для якості та надійності:**

### 8.1 Pydantic State Validation
```python
from core.trinity_models import TrinityStateModel, MetaConfig

# Автоматична валідація всіх полів
state = TrinityStateModel(
    current_agent="meta_planner",
    task_type="DEV",
    meta_config=MetaConfig(strategy="linear")
)
state.validate_state()  # ✅ Все перевірено
```

### 8.2 MyPy Type Checking
```bash
# Перевірка типів на рівні Python 3.11+
mypy core/trinity.py --config-file=setup.cfg
```

### 8.3 State Initialization Logging
- Деталізовані логи всіх переходів агентів
- Тра́сування конфігурацій та помилок
- Місце: `logs/trinity_state_*.log`

### 8.4 Unit Testing
- 16 комплексних тестів для Pydantic моделей
- 100% coverage критичних функцій
- Запуск: `pytest tests/test_trinity_models.py -v`

---

## 9. Швидкий старт

```bash
# Вимоги: Python 3.11 (рекомендовано) або 3.12
./setup.sh                  # Встановлення залежностей
./cli.sh                    # Запуск TUI
/trinity <завдання>         # Запуск Trinity
/autopilot <завдання>       # Режим повної автономії

# Перевірка якості коду
pytest tests/test_trinity_models.py -v
mypy core/ --config-file=setup.cfg
```

---

## 10. FAQ & Advanced Capabilities

### 9.1 Режим Розробника (Dev Mode)
Atlas може працювати в розширеному режимі:
-   **Direct Code Editing**: Через `multi_replace_file_content`
-   **Shell Execution**: `git`, `npm`, `python` та інші
-   **Unsafe Tools**: AppleScript, Mouse Control (з підтвердженням)

### 9.2 Self-Healing
1.  **Detection**: Grisha аналізує результат кожного кроку
2.  **Correction**: Replanning Loop при помилках
3.  **Strategy Shift**: Перехід Native → GUI при необхідності
4.  **Limits**: `MAX_REPLANS` для уникнення нескінченних циклів

### 9.3 Інтерактивність
-   **User → Agent**: Команди/уточнення через TUI
-   **Agent → User**: Тег `[VOICE]` для повідомлень
-   **Feedback Loop**: Прийом даних під час пауз

---

## 9. Файлова структура ключових компонентів

```
System/ (корінь проекту)
├── README.md                          # Основна документація
├── requirements.txt                   # Залежності проекту
├── setup.sh                          # Встановлення
├── setup.cfg                         # MyPy конфігурація (НОВИНКА)
├── pytest.ini                        # Pytest конфігурація
│
├── cli.sh                            # Entry point
├── cli.py                            # CLI обгортка
├── main.py                           # Основна програма
│
├── logs/                             # 📝 Логи (НОВИНКА - централізовано)
│   └── trinity_state_*.log          # State initialization логи
│   └── cli.log                       # CLI логи
│
├── docs/                             # Документація
│   ├── atlas.md                      # ТА цей файл (Project Atlas)
│   ├── analize.md                    # Аналіз системи
│   ├── sonar.md                      # SonarQube документація
│   └── vision.md                     # Vision система
│
├── core/                             # 🧠 Основне ядро
│   ├── trinity.py                    # Trinity Runtime (LangGraph) - 2671 рядків
│   ├── trinity_models.py             # Pydantic моделі валідації (НОВИНКА)
│   ├── state_logger.py               # State логування система (НОВИНКА)
│   ├── context7.py                   # Context Manager + Sliding Window
│   ├── memory.py                     # Hierarchical Memory
│   ├── agent_protocol.py             # Agent Message Protocol
│   ├── parallel_executor.py          # Parallel Tool Execution
│   ├── vision_context.py             # Vision Context Manager
│   ├── mcp.py                        # MCP Tool Registry
│   ├── self_healing.py               # Self-healing система
│   ├── verification.py               # Adaptive Verifier
│   ├── vibe_assistant.py             # Doctor Vibe (Intervention Assistant)
│   └── agents/                       # Агенти
│       ├── atlas.py                  # Atlas агент (плануванн)
│       ├── tetyana.py                # Tetyana агент (виконання)
│       └── grisha.py                 # Grisha агент (верифікація)
│
├── system_ai/                        # 🤖 AI та інструменти
│   ├── tools/
│   │   ├── vision.py                 # Enhanced Vision Analysis + OCR
│   │   ├── screenshot.py             # Multi-monitor screenshots
│   │   ├── automation.py             # Shell/AppleScript/Shortcuts
│   │   ├── browser.py                # Playwright інтеграція
│   │   ├── filesystem.py             # FS операції
│   │   ├── system.py                 # System операції
│   │   └── mcp_integration.py        # MCP інтеграція
│   ├── memory/
│   │   ├── chroma_store.py           # ChromaDB вектор-сховище
│   │   └── summary_memory.py         # Резюме та консолідація
│   └── recorder.py                   # Session Recording
│
├── tui/                              # 🖥️ Terminal UI
│   ├── cli.py                        # Основна TUI програма
│   ├── app.py                        # TUI Runtime
│   ├── menu.py                       # Меню система
│   ├── themes.py                     # 14 color schemes
│   ├── layout.py                     # Layout конструктор
│   ├── keybindings.py                # Keyboard shortcuts
│   ├── permissions.py                # Permission wizard
│   ├── commands.py                   # Команди TUI
│   ├── logger.py                     # TUI логування
│   └── cli_localization.py           # i18n підтримка
│
├── tests/                            # 🧪 Тести
│   ├── test_trinity_models.py        # Unit тести Pydantic моделей (НОВИНКА - 16/16 PASSED)
│   ├── test_vision_system.py         # Vision tests
│   ├── test_agent_protocol.py        # Agent communication tests
│   ├── test_parallel_executor.py     # Executor tests
│   ├── test_trinity_autocommit.py    # Autocommit tests
│   ├── test_context7_sliding_window.py # Context7 tests
│   ├── conftest.py                   # Pytest конфігурація
│   └── ... (інші тести)
│
├── providers/                        # 🔌 LLM Providers
│   └── copilot.py                    # GitHub Copilot інтеграція
│
├── mcp_integration/                  # 🔗 MCP Сервери
│   ├── core/
│   │   └── mcp_manager.py            # MCP Менеджер
│   ├── modes/
│   │   ├── dev_project_mode.py       # Dev режим
│   │   └── atlas_healing_mode.py     # Self-healing режим
│   └── config/
│       └── mcp_config.json           # MCP конфігурація
│
├── configs/                          # 🗂️ Конфігурації IDE
│   ├── original/                     # Оригінальні конфіги
│   └── [30+ машин]/                  # Конфіги для різних систем
│
├── projects/                         # 📦 Генеровані проекти
│   └── dev_*/                        # Dev проекти (автоґенерація)
│
└── cleanup_scripts/                  # 🧹 Утиліти очистки
    └── ... (різні cleanup скрипти)
```

### Логи та Діагностика

**Централізована папка логів (НОВИНКА):**
```
logs/
├── trinity_state_20251220.log        # State initialization логи
├── cli.log                           # CLI операції
└── ...
```

**Як переглянути логи:**
```bash
# Реальний час
tail -f logs/trinity_state_*.log

# Останні 50 рядків
tail -50 logs/trinity_state_*.log

# Пошук по помилкам
grep ERROR logs/trinity_state_*.log
```

**State Logger інформація:**
- 📍 Логує ініціалізацію стану з таймстампом
- 🔄 Логує переходи між агентами
- 🔧 Логує зміни конфігурації
- ❌ Логує помилки зі снімком стану
- 📈 Логує метрики перформансу

Використання:
```python
from core.state_logger import log_initial_state, log_state_transition

log_initial_state(input_text, initial_state)
log_state_transition("atlas", "tetyana", 5, "success")
```

---

*Останнє оновлення: 20 грудня 2025 р. - Trinity Improvements v1.0 інтегровано*
