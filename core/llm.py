
"""
core/llm.py

Unified access to LLM providers.
Wraps the specific provider (e.g. Copilot, OpenAI) and exposes a clean get_llm interface.
"""
import os
from typing import Any, List, Optional, Union

# Attempt to import LangChain core messages
try:
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        SystemMessage,
        BaseMessage,
        ToolMessage
    )
except ImportError:
    # Minimal fallback mocks if LangChain is not installed (should not happen in this env)
    class BaseMessage:
        def __init__(self, content): self.content = content
    class AIMessage(BaseMessage): pass
    class HumanMessage(BaseMessage): pass
    class SystemMessage(BaseMessage): pass
    class ToolMessage(BaseMessage): pass

# Export them for consumers
__all__ = ["get_llm", "AIMessage", "HumanMessage", "SystemMessage", "ToolMessage", "BaseMessage"]

def get_llm(model_id: Optional[str] = None):
    """
    Returns a configured ChatModel instance (LangChain compatible).
    
    Args:
        model_id: Optional model identifier (e.g. "anthropic/claude-3-5-sonnet-latest").
                  If None, uses defaults from environment.
    """
    
    # 1. Try Configured Providers
    # For this specific environment, we know 'providers.copilot' is the main one used by CLI.
    try:
        from providers.copilot import CopilotLLM
        
        # Determine model name
        # If model_id provides a specific hint like "anthropic/...", we might need to map it 
        # or just pass it to the provider if it supports it.
        # The CopilotLLM usually takes standard names like "claude-3-5-sonnet".
        
        target_model = model_id
        if not target_model:
            target_model = os.getenv("COPILOT_MODEL") or "claude-3-5-sonnet"
            
        # Clean up common prefixes if needed
        if target_model.startswith("anthropic/"):
            target_model = target_model.replace("anthropic/", "")
            
        # Initialize
        llm = CopilotLLM(model_name=target_model)
        return llm
        
    except ImportError:
        pass

    # 2. Fallback to Azure/OpenAI if Copilot not available
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_id or "gpt-4o")
    except ImportError:
        pass

    raise RuntimeError("No LLM provider found (CopilotLLM or ChatOpenAI). Ensure dependencies are installed.")
