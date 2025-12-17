"""Agent session and LLM interaction for TUI.

Provides:
- AgentTool and AgentSession dataclasses
- Agent initialization and LLM setup
- Streaming and non-streaming agent responses
- Task complexity detection
- Greeting detection
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from system_cli.state import state
from i18n import lang_name

# Optional imports
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
    from providers.copilot import CopilotLLM
except Exception:
    CopilotLLM = None
    HumanMessage = SystemMessage = AIMessage = ToolMessage = None


@dataclass
class AgentTool:
    """A tool available to the agent."""
    name: str
    description: str
    handler: Any


@dataclass
class AgentSession:
    """Session state for the agent."""
    enabled: bool = True
    messages: List[Any] = field(default_factory=list)
    tools: List[AgentTool] = field(default_factory=list)
    llm: Any = None
    llm_signature: str = ""

    def reset(self) -> None:
        """Reset the message history."""
        self.messages = []


# Global agent session instance
agent_session = AgentSession()

# Chat mode flag
agent_chat_mode: bool = True


def load_env() -> None:
    """Load environment variables from .env file."""
    from tui.cli_paths import SCRIPT_DIR
    
    if load_dotenv is not None:
        load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
    else:
        # Fallback: load .env file manually
        env_path = os.path.join(SCRIPT_DIR, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            os.environ[key] = value
            except Exception:
                pass
    os.environ["SYSTEM_RAG_ENABLED"] = "1"


def get_llm_signature() -> str:
    """Get a signature string for current LLM settings."""
    provider = str(os.getenv("LLM_PROVIDER") or "copilot").strip().lower()
    model = str(os.getenv("COPILOT_MODEL") or "").strip()
    vision = str(os.getenv("COPILOT_VISION_MODEL") or "").strip()
    return f"{provider}:{model}:{vision}"


def ensure_agent_ready() -> Tuple[bool, str]:
    """Ensure the agent LLM is initialized and ready."""
    if CopilotLLM is None or SystemMessage is None or HumanMessage is None:
        return False, "LLM недоступний (нема langchain_core або providers/copilot.py)"

    load_env()
    
    # Import and load LLM settings
    try:
        from tui.cli import _load_llm_settings
        _load_llm_settings()
    except Exception:
        pass
    
    sig = get_llm_signature()

    provider = str(os.getenv("LLM_PROVIDER") or "copilot").strip().lower() or "copilot"
    if provider != "copilot":
        return False, f"Unsupported LLM provider: {provider}"

    if agent_session.llm is None or agent_session.llm_signature != sig:
        agent_session.llm = CopilotLLM(
            model_name=os.getenv("COPILOT_MODEL"), 
            vision_model_name=os.getenv("COPILOT_VISION_MODEL")
        )
        agent_session.llm_signature = sig
    return True, "OK"


def is_complex_task(text: str) -> bool:
    """Detect if text represents a complex multi-step task."""
    t = str(text or "").strip()
    if not t:
        return False
    if t.startswith("/"):
        return False
    # Heuristics: long, multi-sentence, multi-line, or multi-step language.
    if "\n" in t:
        return True
    if len(t) >= 240:
        return True
    if t.count(".") + t.count("!") + t.count("?") >= 3:
        return True
    lower = t.lower()
    keywords = [
        "потім",
        "далі",
        "крок",
        "steps",
        "step",
        "і потім",
        "спочатку",
        "зроби",
        "налаштуй",
        "автоматиз",
        "перевір",
    ]
    return sum(1 for k in keywords if k in lower) >= 2


def is_greeting(text: str) -> bool:
    """Detect if text is a simple greeting."""
    t = str(text or "").strip().lower()
    if not t:
        return False
    t = re.sub(r"[\s\t\n\r\.,!\?;:]+", " ", t).strip()
    greetings = {
        "привіт",
        "привiт",
        "вітаю",
        "доброго дня",
        "добрий день",
        "добрий вечір",
        "доброго вечора",
        "добрий ранок",
        "доброго ранку",
        "hello",
        "hi",
        "hey",
    }
    return t in greetings


def reset_agent_llm() -> None:
    """Reset the agent LLM (forces re-initialization on next use)."""
    agent_session.llm = None
    agent_session.llm_signature = ""


# Backward compatibility aliases
_load_env = load_env
_get_llm_signature = get_llm_signature
_ensure_agent_ready = ensure_agent_ready
_is_complex_task = is_complex_task
_is_greeting = is_greeting
_reset_agent_llm = reset_agent_llm
