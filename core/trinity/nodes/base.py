"""
Base utilities for Trinity graph nodes.

Common functionality shared across all agent nodes.
"""

from typing import Dict, Any, Optional, TypedDict, List
from dataclasses import dataclass
from langchain_core.messages import BaseMessage


@dataclass
class NodeResult:
    """Result from a node execution.
    
    Encapsulates the outcome of a node's processing, including
    which agent to transition to next and any state updates.
    """
    next_agent: str
    state_updates: Dict[str, Any]
    message: Optional[str] = None
    success: bool = True
    
    def to_state_dict(self) -> Dict[str, Any]:
        """Convert to state dictionary for graph transition."""
        updates = dict(self.state_updates)
        updates["current_agent"] = self.next_agent
        return updates


def extract_last_message(messages: List[BaseMessage]) -> str:
    """Extract content from the last message in the list.
    
    Args:
        messages: List of LangChain messages
        
    Returns:
        Content string from last message, or empty string if none
    """
    if not messages:
        return ""
    last = messages[-1]
    if last is None:
        return ""
    content = getattr(last, "content", "")
    return str(content) if content else ""


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dict, handling None dicts.
    
    Args:
        d: Dictionary (may be None)
        key: Key to look up
        default: Default value if key not found or dict is None
        
    Returns:
        Value from dict or default
    """
    if d is None:
        return default
    return d.get(key, default)


def ensure_meta_config(state: Dict[str, Any], last_msg: str = "") -> Dict[str, Any]:
    """Ensure meta_config has all required keys with safe defaults.
    
    This prevents AttributeError when accessing meta_config keys.
    
    Args:
        state: Current Trinity state
        last_msg: Last message content for retrieval_query default
        
    Returns:
        Complete meta_config dict with all required keys
    """
    meta_config = state.get("meta_config")
    
    if not isinstance(meta_config, dict):
        meta_config = {}
    
    # Ensure all required keys have defaults
    meta_config.setdefault("strategy", "hybrid")
    meta_config.setdefault("verification_rigor", "standard")
    meta_config.setdefault("recovery_mode", "local_fix")
    meta_config.setdefault("tool_preference", "hybrid")
    meta_config.setdefault("reasoning", "")
    meta_config.setdefault("retrieval_query", last_msg[:100] if last_msg else "")
    meta_config.setdefault("n_results", 3)
    
    return meta_config


def is_terminal_status(status: Optional[str]) -> bool:
    """Check if a task status indicates termination.
    
    Args:
        status: Task status string
        
    Returns:
        True if status indicates task completion/termination
    """
    if not status:
        return False
    return status.lower() in {
        "completed", "success", "done", 
        "failed", "error", "cancelled", "canceled",
        "terminated", "aborted"
    }


def count_step_failures(state: Dict[str, Any]) -> int:
    """Get the current step failure count from state.
    
    Args:
        state: Trinity state dict
        
    Returns:
        Number of consecutive failures on current step
    """
    try:
        return int(state.get("current_step_fail_count") or 0)
    except (ValueError, TypeError):
        return 0


def count_uncertain_streak(state: Dict[str, Any]) -> int:
    """Get the uncertain decision streak count from state.
    
    Args:
        state: Trinity state dict
        
    Returns:
        Number of consecutive uncertain decisions
    """
    try:
        return int(state.get("uncertain_streak") or 0)
    except (ValueError, TypeError):
        return 0
