from typing import Any, Dict


def is_langgraph_available() -> bool:
    try:
        import langgraph  # noqa: F401

        return True
    except Exception:
        return False


def build_placeholder_graph() -> Dict[str, Any]:
    """Placeholder to keep folder structure stable.

    Later we will replace with a real LangGraph state machine.
    """
    return {"ok": True, "type": "placeholder", "langgraph": is_langgraph_available()}
