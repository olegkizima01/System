# System: повний опис роботи (Atlas / Trinity Runtime)

## 1. Мета цього документа

Цей файл є покроковим описом того, як працює система в цьому репозиторії: від запуску CLI/TUI до виконання задач Trinity Runtime (LangGraph) та інтеграцій (MCP, self-healing, plugins).

Документ буде дописуватися поступово під час аналізу файлів.

## 2. Коротко: що це за система

Проєкт позиціонується як **автономний мультиагентний оператор macOS** (Atlas), який:

- Приймає задачу від користувача через CLI/TUI.
- Формує план (Atlas) та керує політикою виконання (Meta-Planner).
- Виконує кроки (Tetyana) через набір інструментів (MCP Tool Registry, local tools).
- Верифікує результат (Grisha) включно з візуальними перевірками.
- Зберігає “досвід” у Memory (ChromaDB).
- Має self-healing механізм для автоматичного виявлення/ремонту проблем у коді.

Основні директорії:

- `tui/` — інтерфейс користувача (prompt_toolkit), команди, меню, налаштування.
- `core/trinity/` — runtime та граф вузлів (meta_planner/atlas/tetyana/grisha/knowledge/vibe).
- `core/` — конфіг, логування, memory, self-healing, тощо.
- `system_ai/tools/` — інструменти автоматизації (shell/applescript/gui/browser/filesystem/vision).
- `mcp_integration/` — частина інтеграції з MCP та “client manager”.
- `plugins/` — система плагінів і приклади.

## 3. Точки входу (Entry points)

### 3.1 `main.py`

- Файл-обгортка, який просто викликає `cli.main()`.

### 3.2 `cli.py` (кореневий)

- Мінімальний wrapper навколо `tui/cli.py`.
- Ставить env-флаги для вимкнення telemetry (`CHROMA_TELEMETRY_ENABLED`, `ANONYMIZED_TELEMETRY`).
- Додає root репозиторію у `sys.path`.
- Перекодовує `stdin` в UTF-8 (best-effort).
- Має автодетекцію: якщо перший аргумент не є відомою командою — трактує це як `agent-chat`.

Потік:

1. `cli.py:main()`
2. (опційно) перетворює `argv` → `agent-chat --message "..."`
3. `from tui.cli import main as tui_main`
4. `tui_main()`

### 3.3 `tui/cli.py`

Это **основний CLI** з сабкомандами через `argparse`. До рефакторингу це був монолітний файл, тепер він модульний.

Ключові частини:

- `cli_main(argv)`:
  - запускає `setup_global_logging(verbose=...)`
  - парсить сабкоманди
  - вантажить cleanup config (`_load_cleanup_config()`)
  - визначає редактор (`_resolve_editor_arg`)
  - диспатчить команди:
    - `list-editors`, `list-modules`, `run`, `enable`, `install`
    - `smart-plan`, `ask`
    - `agent-chat`
    - допоміжні (self-healing, vibe, eternal-engine)

#### Модульна структура TUI:
- **`tui/cli.py`**: Точка входу в CLI, обробка аргументів, диспетчеризація команд.
- **`tui/scanning.py`**: Сканування встановлених програм (браузери, редактори) та отримання bundle ID.
- **`tui/monitoring.py`**: Логіка роботи з БД моніторингу (`monitor_db_insert`, `monitor_db_read_since_id`).
- **`tui/monitoring_service.py`**: Сервіси обгорток над `fs_usage`, `opensnoop` (`ProcTraceService`).
- **`tui/utils.py`**: Загальні утиліти (наприклад, `safe_abspath`).
- **`tui/agents.py`**: Логіка спілкування з агентом (`agent_send`, `ensure_agent_ready`).

- `main()` у кінці файла просто викликає `cli_main(sys.argv[1:])`.

## 4. Конфігурація

### 4.1 `config/settings.yaml` і `core/config.py`

- `config/settings.yaml` містить налаштування для:
  - `logging`
  - `mcp` (список server-ів: `context7`, `playwright`, `filesystem`)
  - `agents` (timeouts/retries/vision)
  - `paths`

- `core/config.py` містить Pydantic-моделі:
  - `Settings`, `LoggingConfig`, `MCPConfig`, `AgentConfig`, `PathConfig`
  - `ConfigLoader.load(config_path="config/settings.yaml")`

Примітка: файл `settings.yaml` має верхній ключ `settings:`, який не відповідає структурі `Settings` (потрібні поля `app_name/version/env` на верхньому рівні). Це виглядає як потенційна логічна проблема: фактичні значення можуть не застосовуватися (див. розділ проблем).

### 4.2 Cleanup конфіг: `config/cleanup_modules.json`

- Використовується як джерело редакторів/модулів/скриптів для очистки.
- `tui/cleanup.py` читає/пише цей файл напряму.

### 4.3 MCP конфіг

Є декілька конфігів:

- `config/mcp_config.json`
- `mcp_integration/config/mcp_config.json`
- а також user-level конфіг у `~/.kinotavr/mcp_config.json` (якщо існує)

## 5. Логування

### 5.1 `core/logging_config.py`

Центральний модуль логування.

Ключове:

- Логи зберігаються в `~/.system_cli/logs/`:
  - `cli.log`
  - `errors.log`
  - `debug.log`
  - `atlas_analysis.jsonl`

- Є `SafeTuiHandler`, який може писати логи в TUI-стан через callback (`tui_state_callback`).

### 5.2 `tui/logger.py`

Це legacy shim, який реекспортує функції з `core/logging_config.py`.

## 6. Cleanup підсистема (редактори/модулі/скрипти)

Основний модуль: `tui/cleanup.py`.

Потік `run_cleanup(cfg, editor, dry_run)`:

1. Валідує що `editor` існує у `cfg["editors"]`.
2. Обирає активні модулі `enabled == true`.
3. Для кожного модулю викликає `run_script(script)`.
4. `run_script`:
   - робить `chmod +x`.
   - запускає subprocess (stdout+stderr разом).
   - стрімить output построково.
   - має timeout і kill процеса.

## 7. TUI: стан, рендер, меню, команди

### 7.1 Стан: `tui/state.py`

`AppState` містить:

- лог-буфер `logs` + `logs_lock`
- поточний рівень меню `menu_level`
- налаштування UI (тема, мова, streaming, gui_mode, execution_mode)
- прапорці агента (`agent_processing`, `agent_paused`, ...)
- налаштування monitoring
- selection state для виділення тексту в панелях

### 7.2 Рендер: `tui/render.py`

- Має кеші для швидкого рендерингу (`_render_log_cache`, `_render_agents_cache`).
- `get_render_log_snapshot()` і `get_render_agents_snapshot()` будують форматований текст + позицію курсора.
- Є trimming логів (щоб не роздувалась памʼять) при перевищенні лімітів.

### 7.3 Меню: `tui/menu.py`

- `build_menu(...)` отримує контекст з великою кількістю callbacks.
- В залежності від `state.menu_level` викликає відповідний renderer.

### 7.4 Команди: `tui/commands.py`

- `handle_input()`:
  - якщо введення починається з `/` → `handle_command()`
  - інакше дефолт: `handle_command(f"/task {text}")`

- `handle_command()` диспатчить slash-команди:
  - `/task`, `/trinity`, `/autopilot` → запуск Trinity через `run_graph_agent_task` у окремому thread.
  - `/chat` → чат без виконання.
  - `/resume` → відновлення паузи.
  - `/memory*`, `/open-privacy`, тощо.

#### 7.4.1 Потік виконання `/task` (через TUI)

1. Користувач вводить текст у нижній input панелі.
2. `tui/commands.py:handle_input()`
   - якщо текст не slash-команда → викликає `handle_command(f"/task {text}")`.
3. `tui/commands.py:handle_command()`
   - диспатчить `/task` → `_cmd_trinity_task()`.
4. `_cmd_trinity_task()` створює thread і викликає `tui/agents.py:run_graph_agent_task(...)`.
5. `run_graph_agent_task()`:
   - формує `TrinityPermissions` (allow_shell/applescript/gui/write/shortcuts).
   - створює `TrinityRuntime(... on_stream=callback, preferred_language=state.chat_lang, enable_self_healing=state.ui_self_healing, learning_mode=state.learning_mode)`.
   - реєструє TUI tools як Trinity tools (через `runtime.registry.register_tool`).
   - читає `state.ui_execution_mode` (`native`/`gui`).
   - запускає `runtime.run(...)` і обробляє події у `_process_graph_events()`.
6. `_process_graph_events()`:
   - проходить по `event` з `runtime.run()` (LangGraph stream).
   - для кожного `node_name` бере останній меседж зі `state_update["messages"]`.
   - оновлює:
     - ліву панель логів (`tui/render.py:log_replace_at/log_reserve_line`).
     - праву панель “AGENTS” (`tui/render.py:log_agent_message/log_agent_final`).
   - якщо `state_update` містить `pause_info` → ставить паузу через `set_agent_pause(...)`.

## 8. Trinity Runtime (LangGraph)

Основні файли:

- `core/trinity/runtime.py` — клас `TrinityRuntime` (композиція mixin-ів).
- `core/trinity/execution.py` — побудова LangGraph.
- `core/trinity/state.py` — schema стану `TrinityState` + permissions.
- `core/trinity/nodes/*` — вузли (meta_planner, atlas, tetyana, grisha, knowledge, vibe).

### 8.1 Побудова графа

`core/trinity/execution.py`:

- Entry point: `meta_planner`
- Flow:
  - `meta_planner` → (conditional) `atlas` або `knowledge`
  - `atlas` → `tetyana`
  - `tetyana` → `grisha`
  - `grisha` → (conditional) `meta_planner` або `knowledge`
  - `knowledge` → `vibe` → END

### 8.2 Ролі вузлів

- **Meta-Planner** (`core/trinity/nodes/meta_planner.py`)
  - керує політикою, лімітами (steps/replans), умовами replanning/repair.
  - підтримує `meta_config`, summary, anti-loop.

- **Atlas** (`core/trinity/nodes/atlas.py`)
  - генерує план кроків.
  - може робити selective RAG через memory.
  - має “repair mode” (генерує 1 альтернативний крок).

- **Tetyana** (`core/trinity/nodes/tetyana.py`)
  - виконує крок через tool-calls.
  - є permission-gating (shell/applescript/gui/write/shortcuts).
  - має спеціальний режим Doctor Vibe для DEV-редагувань.

- **Grisha** (`core/trinity/nodes/grisha.py`)
  - верифікує результат (LLM+tools+vision).
  - може запускати pytest при зміні критичних директорій.
  - має anti-loop heuristics.

- **Knowledge** (`core/trinity/nodes/knowledge.py`)
  - записує досвід у memory (`knowledge_base`).

- **Vibe**
  - вузол-аналітик `core/trinity/nodes/vibe.py:vibe_analyst_node`.
  - читає останні логи (`~/.system_cli/logs/cli.log` + останній `trinity_state_*.log`) та генерує пост-мортем/аналіз.
  - результат зберігає в `state["last_vibe_analysis"]`.

## 9. MCP Tool Registry та інструменти

Основний реєстр: `core/mcp_registry.py`.

- Реєструє “foundation tools”:
  - shell/applescript/shortcuts
  - filesystem
  - browser automation
  - screenshots/vision
  - memory tools

- Підтримує зовнішні MCP сервери через stdio (`ExternalMCPProvider`).

- Має мапінг `BROWSER_TOOL_ROUTING` для маршрутизації browser-інструментів у Playwright MCP.

## 10. Self-healing та Doctor Vibe

- `core/self_healing.py`: CodeSelfHealer
  - читає структуру/логи
  - детектить помилки regex-патернами
  - генерує repair plan через LLM
  - може виконувати edits/commands

- `core/trinity/integration/integration_self_healing.py`
  - вмикає self-healing
  - запускає background monitoring
  - підʼєднує self-healer до `VibeCLIAssistant` для auto-repair

- `core/vibe_assistant.py`: VibeCLIAssistant
  - human-in-the-loop паузи, історія інтервенцій, /continue /cancel /help
  - може робити auto-repair якщо self-healer підʼєднаний

## 11. Plugins

- `plugins/__init__.py`:
  - discovery: шукає піддиректорії з `plugin.py`
  - `PLUGIN_META` має бути `PluginMeta`
  - `register(registry)` — точка реєстрації tool-ів

- `plugins/plugin_creator.py`:
  - scaffolding нового плагіну (plugin.py/README/tests)

## 12. Розділ проблем (буде поповнюватись)

Нижче буде окрема рубрика, де я додам:

- проблеми з логіки виконання
- проблеми в коді/архітектурі
- проблеми з конфігами/логами

Після аналізу актуальних логів (`~/.system_cli/logs/*`) цей розділ буде заповнено.

### 12.1 Проблеми з логів (runtime / TUI / MCP)

#### 12.1.1 Критичний баг TUI (історичний)

- У `~/.system_cli/logs/errors.log` є повторюваний краш:
  - `TypeError: Window.__init__() got an unexpected keyword argument 'name'`
  - стек: `tui/layout.py` → `Window(name=...)`.
- Поточна версія `tui/layout.py` вже не передає `name=` у `Window(...)`, а проставляє `name` через `setattr(window, "name", ...)`, тому цей баг має бути усунений.

#### 12.1.2 Баг з `/resume` (логіка паузи)

- У `tui/commands.py` функція `resume_paused_agent()` була порожня, а логіка “resume” випадково була вставлена в кінець `start_eternal_engine_mode()`.
- Це означало, що `/resume` не міг реально відновити виконання, а eternal-engine потенційно виконував сторонню логіку.
- Виправлено:
  - `resume_paused_agent()` тепер запускає `run_graph_agent_task()` з `state.agent_pause_pending_text`.
  - stray-block з `start_eternal_engine_mode()` видалено.

#### 12.1.3 Дуже часті повідомлення self-healing "Starting self-healing monitoring loop"

- У `~/.system_cli/logs/cli.log` видно багаторазове:
  - `Starting self-healing monitoring loop`
  - `Started background monitoring with 60.0s interval`
- Це часто виглядає як багаторазове створення `TrinityRuntime` (наприклад, тести або повторні старти), але якщо таке трапляється у “реальному” запуску TUI — це ознака що background-потік не singleton і може множитись.

Рекомендація:
- Додати guard (наприклад, singleton thread / перевірка `is_alive()`) перед стартом нового background monitoring.

#### 12.1.4 MCP provider: "Connection closed" / шумні помилки

- У `cli.log` є помилки `MCP Connection Error (echo-test): Connection closed`.
- Це може бути:
  - тестовий/неіснуючий MCP сервер;
  - проблема з командою запуску MCP;
  - або нестача macOS permissions (хоч тут саме `Connection closed`, не timeout).

Рекомендація:
- Для dev/test провайдерів зробити режим “optional” без ERROR-level spam.

### 12.2 Проблеми конфігів/узгодженості

#### 12.2.1 `config/settings.yaml` не відповідає `core/config.py:Settings`

- `core/config.py` очікує, що `Settings(**data)` матиме поля `app_name/version/env` на верхньому рівні.
- `config/settings.yaml` має вкладений ключ `settings:`.

Наслідок:
- Налаштування можуть завантажуватись частково або fallback-итись до дефолтів.

Рекомендація:
- Або змінити YAML структуру (підняти `app_name/version/env` на top-level),
- або адаптувати `ConfigLoader.load()` щоб читати `data.get("settings")`.

#### 12.2.2 Дублювання MCP конфігів і менеджерів

- Є кілька конфігів MCP (`config/mcp_config.json`, `mcp_integration/config/mcp_config.json`, `~/.kinotavr/mcp_config.json`).
- Є два різні рівні інтеграції:
  - `core/mcp/manager.py`
  - `mcp_integration/core/mcp_client_manager.py` (використовується у `core/mcp_registry.py`).

Ризик:
- різні частини системи можуть “думати”, що активний MCP клієнт/сервер інший.

### 12.3 Проблеми коду, які було виправлено під час цього завдання

- `tui/commands.py`: виправлено реалізацію `/resume` (див. 12.1.2).
- `core/trinity/nodes/vibe.py`:
  - виправлено некоректний виклик `trace(...)` (тепер `trace(logger, event, data)`),
  - додано читання state logs з `~/.system_cli/logs/trinity_state_*.log` (з fallback на локальні `logs/`),
  - додано fallback: якщо LLM не підтримує `ainvoke`, використовувати `invoke`.

