---
description: The Core Architecture and Workflow of Project Atlas (Trinity Runtime).
---

# Project Atlas: Trinity Runtime Specification

This document defines the architecture, logic, and workflow of the **Trinity Runtime** — the core orchestrator of the Atlas system.

## 1. Core Architecture (The Trinity)

The system is built on a **LangGraph StateMachine** with three primary nodes (agents):

### 🌐 **Atlas (The Brain)**
*   **Role:** Strategist, Planner, Orchestrator.
*   **Responsibility:** 
    *   Receives user input via TUI.
    *   **Decomposition (Smart Planning):** Uses `ATLAS_PLANNING_PROMPT` to break down requests into atomic JSON actions.
    *   **Context Management:** Maintains `Summary Memory` (rolling summary every 3 steps) and queries `RAG Memory`.
    *   **Plan Management:** Consumes the plan step-by-step.
*   **Logic:** `_atlas_node` in `core/trinity.py`.

### 💻 **Tetyana (The Hands)**
*   **Role:** Universal Executor.
*   **Responsibility:** 
    *   Executes specific actions defined by Atlas (e.g., `open_app`, `click`, `run_shell`).
    *   Interacts with the OS via **MCP Tools**.
    *   **Safety:** Checks `TrinityPermissions` (Shell, AppleScript) before execution. Pauses if permission is missing.
*   **Logic:** `_tetyana_node` in `core/trinity.py`.

### 👁️ **Grisha (The Eyes)**
*   **Role:** Verifier, Security, QA.
*   **Responsibility:** 
    *   **Visual Verification:** Takes screenshots (`capture_screen`) to verify UI state.
    *   **Data Verification:** Checks file contents (`read_file`) or command outputs.
    *   **Feedback:** Returns `success` or `failure`. If failure, triggers a loop back to Atlas for replanning.
*   **Logic:** `_grisha_node` in `core/trinity.py`.

---

## 2. The Planning Pipeline

The system uses a sophisticated **Decomposition -> Optimization -> Execution** pipeline:

1.  **Input:** User Request (e.g., "Create a file and write hello").
2.  **RAG Lookup:** Atlas searches ChromaDB for similar past strategies.
3.  **Decomposition (Atlas):** 
    *   LLM converts request into a JSON List of Actions.
    *   Example: `["Create file", "Write text"]`.
4.  **Optimization (Verifier):**
    *   **AdaptiveVerifier** (LLM-based) analyzes the plan.
    *   Inserts `VERIFY` steps at critical junctions (e.g., after "Create file").
    *   Result: `["Create file", "VERIFY (Grisha)", "Write text", "VERIFY (Grisha)"]`.
5.  **Execution Loop:**
    *   Atlas dispatches the first step to Tetyana.
    *   Tetyana executes -> Grisha verifies.
    *   Atlas removes the completed step and proceeds to the next.

---

## 4. Safety & Permissions

The system operates under a strict permission model (`TrinityPermissions`):

*   **Restricted Actions:** `run_shell`, `run_applescript` require explicit flags (`allow_shell`, `allow_applescript`).
*   **Pause Protocol:** 
    *   If Tetyana attempts a restricted action without permission, `pause_info` is set in the state.
    *   Atlas halts execution and returns `[PAUSED]`.
    *   TUI displays the warning and waits for user command (`/allow shell` -> `/resume`).
*   **Execution Limits:**
    *   `MAX_STEPS = 30`: Prevents infinite execution.
    *   `MAX_REPLANS = 5`: Prevents infinite retry loops on failure.

---

## 5. Tool Capabilities (MCP)

Tetyana has access to a registry of tools defined in `core/mcp.py`:

*   **System Control:** `run_shell`, `run_applescript`, `get_system_info`.
*   **File System:** `read_file`, `write_file`, `list_files`, `find_by_name`.
*   **Vision:** `take_screenshot` (used by Grisha).
*   **UI Interaction:** `click`, `type`, `scroll`, `hover` (via AppleScript/Python).
*   **Applications:** `open_app`, `close_app`.

---

## 6. Memory Systems

1.  **RAG Memory (ChromaDB):**
    *   Stores successful strategies (`strategies` collection).
    *   Atlas retrieves relevant context before planning.
    *   Successful Tetyana actions are ingested back into memory.
2.  **Summary Memory (Short-term):**
    *   A rolling text summary maintained by Atlas in the state.
    *   Updated every 3 steps to prevent context loss in long-running tasks.

---

## 7. Configuration

*   **Environment:** Requires `.env` file with `COPILOT_API_KEY` or `GITHUB_TOKEN`.
*   **Entry Point:** `./cli.sh` (handles venv and env vars).

---

## 8. File Structure

*   `core/trinity.py` - Main Runtime, Graph definition, Node logic.
*   `core/agents/` - Prompt definitions for Atlas, Tetyana, Grisha.
*   `core/verification.py` - AdaptiveVerifier (Plan Optimization logic).
*   `core/mcp.py` - Tool Registry.
*   `tui/cli.py` - User Interface, Runtime integration.

---

## 9. Development Guidelines

*   **Changes to Logic:** Always update `core/trinity.py` and ensure the Graph topology remains consistent.
*   **New Tools:** Register in `core/mcp.py`.
*   **Verification:** If adding new critical actions, ensure `VERIFIER_PROMPT` in `core/verification.py` covers them.
