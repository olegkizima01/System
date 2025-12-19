# Project Atlas: Cognitive 2.0 Identity

**Autonomous Multi-Agent macOS Operator built on Trinity Runtime.**

Atlas is not just an automation script. It is a local "neural operator" for macOS that perceives the screen (Vision-First), plans implicitly (Meta-Planning), and executes actions through a strict low-level tool interface (MCP). It is designed to act as a high-level cognitive layer over the OS, capable of complex tasks ranging from system management to web automation and coding.

---

## 🧠 Core Principles (Cognitive 2.0)

1.  **Autonomous Navigation**: Self-correction loop: *Perception → Planning → Action → Verification*.
2.  **Meta-Planning**: The agent manages its own strategy (e.g., "Aggressive" vs "Careful") and budgets its own attention (Context7).
3.  **Vision-First**: Uses screenshots and Computer Vision as the "Ground Truth".
4.  **Privacy & Stealth**: Built-in system for cleaning traces (`cleanup_scripts`) and spoofing identifiers.
5.  **Continuous Learning**: Every mission result (Success/Failure) is analyzed and stored in the **Knowledge Base** to improve future plans.

---

## 🏗 Architecture: The Trinity Graph

The system runs on **Trinity Runtime**, a cyclic graph (LangGraph) of specialized nodes:

| Agent / Layer | Role | Description |
| :--- | :--- | :--- |
| **Meta-Planner** | *Orchestrator* | The "Head". Performs Active Retrieval and filters memories. |
| **Context7** | *Context Manager* | **Explicit Layer**. Budgets tokens, injects policy, and normalizes context. |
| **Atlas** | *Architect* | Generates tactical plans based on normalized context. |
| **Tetyana** | *Executor* | Universal operator. Executes tools (Shell, AppleScript, Browser). |
| **Grisha** | *Verifier* | QA. Verifies actions via visual feedback and logic. |
| **Knowledge** | *Learner* | Reflection phase. Extracts lessons and updates the vector DB. |

---

## 🛠 Tooling (MCP Foundation)

Atlas accesses the world through the **Model Context Protocol (MCP)** registry:

-   **Unified Automation**: Internal module for Shell, AppleScript, Mouse/Keyboard, and Shortcuts.
-   **System Cleanup**: Advanced privacy tools (logs wiping, hardware spoofing).
-   **Recorder Control**: Semantic session recording.
-   **External MCPs**:
    -   **Playwright**: Full browser automation.
    -   **PyAutoGUI**: Fallback input emulation.
-   **Integrations**:
    -   **AI-IDE Support**: Windsurf, Antigravity, Cursor, Continue CLI.

---

## 🚀 Quick Start

### Prerequisites
-   macOS (Silicon recommended)
-   Python 3.12+ (managed by setup)
-   Node.js (for Playwright MCP)

### Installation

```bash
git clone https://github.com/your-repo/system.git
cd system
chmod +x setup.sh
./setup.sh
```

The `setup.sh` script will:
1.  Create a Python 3.12 virtual environment.
2.  Install all Python dependencies (`requirements.txt`).
3.  Install Playwright browsers.
4.  Patch `mcp-pyautogui-server`.
5.  Set execution permissions for cleanup scripts.

### Usage

Run the TUI (Text User Interface):

```bash
./cli.sh
```

**Commands:**
-   `/trinity <task>`: Start a standard agent assignment.
-   `/autopilot <task>`: Run in fully autonomous mode.
-   `/help`: Show all commands.

---

---

## ⚡️ Advanced Capabilities

-   **Self-Healing**: Atlas automaticaly detects failures (via `Grisha`) and triggers replanning to fix errors without user intervention.
-   **Dev Mode**: Capable of editing its own source code, running shell commands, and managing git integration.
-   **Interactive TUI**: Real-time communication via `[VOICE]` messages; users can intervene or guide the agent via the CLI chat.

---

*For deep architectural details, see [docs/atlas.md](docs/atlas.md).*
