# System Architecture

## Overview
The system is designed as an autonomous multi-agent macOS operator ("Atlas"), capable of executing complex tasks via a CLI/TUI interface. It leverages a graph of agents (Trinity Runtime) to plan, execute, and verify actions.

## Modular Component Structure

### 1. Entry Points
- **`cli.sh`**: The primary shell entry point. Securely handles environment setup, Python version checks, and `sudo` permissions.
- **`cli.py`**: A lightweight Python wrapper. Sets up the Python path, global logging, and parses "natural language" arguments (delegating to `tui.cli_helpers`).
- **`main.py`**: A minimal convenience wrapper calling `cli.py`.

### 2. TUI (Terminal User Interface)
The TUI logic, previously monolithic, is now split into focused modules for better maintainability:

- **`tui/cli.py`**:
  - Handles command-line argument parsing and dispatching.
  - Initializes the application state and logging.
  - Manages the high-level flow of CLI commands.
- **`tui/agents.py`**:
  - Manages the agent session (`AgentSession`).
  - Handles communication with the LLM (streaming and non-streaming responses).
  - Initializes agent tools.
- **`tui/monitoring.py`**:
  - Core monitoring logic: database operations (`monitor_db_insert`), settings management, and target resolution.
- **`tui/monitoring_service.py`**:
  - Wrappers for system monitoring tools (`fs_usage`, `opensnoop`) encapsulated in classes like `ProcTraceService`.
- **`tui/scanning.py`**:
  - Utilities for scanning the filesystem for installed applications and browsers to auto-configure monitoring targets.
- **`tui/utils.py`**:
  - General helper functions (e.g., `safe_abspath`).

### 3. Core Runtime (Trinity)
- **`core/trinity`**: Contains the definition of the agent graph and nodes (`Atlas`, `Tetyana`, `Grisha`).
- **`core/mcp_registry.py`**: Manages the registration of tools available to agents, including local system tools and external MCP servers.

### 4. Logging
- **`core/logging_config.py`**: Centralized logging configuration. Supports:
  - Rotating file logs (`cli.log`, `errors.log`).
  - Safe logging to TUI state (`SafeTuiHandler`).
  - Asynchronous logging (planned optimization).

## Data Flow
1. User invokes `cli.sh`.
2. `cli.py` initializes and normalizes arguments.
3. `tui/cli.py` determines the command execution path:
   - **TUI Mode**: Launches the `prompt_toolkit` application.
   - **CLI Mode**: Executes specific subcommands (e.g., `run`, `install`) or sends a message to the agent (`agent-chat`).
4. **Agent Tasks**: Complex tasks triggering the Trinity graph run in a separate thread, emitting events that update the TUI state in real-time.
