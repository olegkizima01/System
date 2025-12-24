"""
Base classes and enums for MCP Integration.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class MCPClientType(Enum):
    """Available MCP client types."""
    NATIVE = "native"          # Official MCP Python SDK (Recommended)
    AUTO = "auto"              # Automatic resolution (defaults to Native)


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to MCP client."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from MCP client."""
        pass
    
    @abstractmethod
    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via the MCP client."""
        pass
    
    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a high-level task/prompt via the client's internal agent.
        Defaults to execute_prompt if not overridden.
        """
        return self.execute_prompt(task)

    @abstractmethod
    def list_tools(self) -> List[Dict[str, str]]:
        """List available tools from the MCP client."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get client status information."""
        pass
    
    def execute_prompt(self, prompt: str) -> Dict[str, Any]:
        """Execute a natural language prompt (if supported)."""
        return {
            "success": False,
            "error": "Prompt execution not supported by this client"
        }
