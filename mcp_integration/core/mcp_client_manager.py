#!/usr/bin/env python3
"""
MCP Client Manager - Dual Client Architecture

Supports switching between:
1. CopilotKit/open-mcp-client (Python/LangGraph based)
2. Continue MCP Client (@continuedev/cli)
"""

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

# Import Prompt Engine for Dynamic Context
try:
    from mcp_integration.prompt_engine import prompt_engine
    PROMPT_ENGINE_AVAILABLE = True
except ImportError:
    PROMPT_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPClientType(Enum):
    """Available MCP client types."""
    OPEN_MCP = "open_mcp"      # CopilotKit/open-mcp-client
    CONTINUE = "continue"      # @continuedev/cli
    NATIVE = "native"          # Official MCP Python SDK (Recommended)
    CLINE = "cline"            # Cline (Meta-Orchestrator)
    AUTO = "auto"              # Automatic switching based on task


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._connected = False
        self._tools: Dict[str, Any] = {}
    
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


class MCPClientManager:
    """Manager for switching between MCP clients."""
    
    CONFIG_KEY = "activeClient"
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or self._default_config_path()
        self._config = self._load_config()
        self._clients: Dict[MCPClientType, BaseMCPClient] = {}
        self._active_type: MCPClientType = self._get_active_from_config()
        
        # Lazy-load clients
        self._init_clients()
    
    def _default_config_path(self) -> str:
        """Get default config path. Prefers user home directory for permissions."""
        user_config = os.path.expanduser("~/.kinotavr/mcp_config.json")
        if os.path.exists(user_config):
            return user_config
            
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Check mcp_integration/config as well
        alt_config = os.path.join(base, "mcp_integration", "config", "mcp_config.json")
        if os.path.exists(alt_config):
            return alt_config
            
        return os.path.join(base, "config", "mcp_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load MCP config: {e}")
        return {}
    
    def _save_config(self) -> bool:
        """Save configuration to file."""
        try:
            self._config[self.CONFIG_KEY] = self._active_type.value
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save MCP config: {e}")
            return False
    
    def _get_active_from_config(self) -> MCPClientType:
        """Get active client type from config."""
        active_str = str(self._config.get(self.CONFIG_KEY, "open_mcp")).lower()
        try:
            return MCPClientType(active_str)
        except ValueError:
            return MCPClientType.OPEN_MCP
    
    def _init_clients(self) -> None:
        """Initialize client instances (lazy loading)."""
        clients_config = self._config.get("mcpClients", {})
        
        # Import clients dynamically to avoid circular imports
        try:
            from .open_mcp_client import OpenMCPClient
            open_mcp_cfg = clients_config.get("open_mcp", {})
            self._clients[MCPClientType.OPEN_MCP] = OpenMCPClient(open_mcp_cfg)
        except ImportError as e:
            logger.warning(f"OpenMCPClient not available (ImportError): {e}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenMCPClient: {e}")
        
        try:
            from .continue_mcp_client import ContinueMCPClient
            continue_cfg = clients_config.get("continue", {})
            self._clients[MCPClientType.CONTINUE] = ContinueMCPClient(continue_cfg)
        except ImportError as e:
            logger.warning(f"ContinueMCPClient not available (ImportError): {e}")
        except Exception as e:
            logger.error(f"Failed to initialize ContinueMCPClient: {e}")

        try:
            from .native_sdk_client import NativeMCPClient
            native_cfg = clients_config.get("native", {})
            # Ensure native_cfg knows where the main config is for server discovery
            native_cfg["mcp_config_path"] = self._config_path
            self._clients[MCPClientType.NATIVE] = NativeMCPClient(native_cfg)
        except ImportError as e:
            logger.warning(f"NativeMCPClient not available (ImportError): {e}")
        except Exception as e:
            logger.error(f"Failed to initialize NativeMCPClient: {e}")
            
        # Add Cline if implemented
        try:
            from .cline_mcp_client import ClineMCPClient
            cline_cfg = clients_config.get("cline", {})
            self._clients[MCPClientType.CLINE] = ClineMCPClient(cline_cfg)
        except (ImportError, AttributeError):
            pass
    
    @property
    def active_client(self) -> MCPClientType:
        """Get currently active client type."""
        return self._active_type
    
    @property
    def active_client_name(self) -> str:
        """Get human-readable name of active client."""
        names = {
            MCPClientType.OPEN_MCP: "Open-MCP (CopilotKit)",
            MCPClientType.CONTINUE: "Continue CLI",
            MCPClientType.NATIVE: "Native SDK (High-Performance)",
            MCPClientType.CLINE: "Cline",
            MCPClientType.AUTO: "Auto (Task-based)"
        }
        return names.get(self._active_type, "Unknown")

    def resolve_client_by_server(self, server_name: str) -> Optional[MCPClientType]:
        """Find the owner client for a specific server name."""
        server_config = self._config.get("mcpServers", {}).get(server_name)
        if server_config and "ownerClient" in server_config:
            try:
                owner = server_config["ownerClient"]
                return MCPClientType(owner)
            except ValueError:
                pass
        return None

    def resolve_client_type(self, task_type: Optional[str] = None, server_name: Optional[str] = None) -> MCPClientType:
        """Resolve the client type based on context if in AUTO mode."""
        # 0. Check for explicit server ownership first
        if server_name:
            owner = self.resolve_client_by_server(server_name)
            if owner and owner in self._clients:
                return owner

        if self._active_type != MCPClientType.AUTO:
            return self._active_type
            
        # Decision logic for AUTO mode
        if task_type:
            task_type = task_type.lower()
            if task_type in ["dev", "code", "debug"]:
                return MCPClientType.CONTINUE
            if task_type in ["browser", "web", "search", "general"]:
                # Preferred for browser or general high-level tasks via Cline if available, else Native
                return MCPClientType.CLINE if MCPClientType.CLINE in self._clients else MCPClientType.NATIVE
            
        # Default to Native for performance
        return MCPClientType.NATIVE
    
    def get_client(self, client_type: Optional[MCPClientType] = None, task_type: Optional[str] = None, server_name: Optional[str] = None) -> Optional[BaseMCPClient]:
        """Get a client instance. If in AUTO, resolves based on context."""
        ct = client_type or self.resolve_client_type(task_type, server_name)
        return self._clients.get(ct)
    
    def switch_client(self, client_type: MCPClientType, save: bool = True) -> bool:
        """
        Switch to a different MCP client.
        """
        if client_type not in self._clients and client_type != MCPClientType.AUTO:
            logger.error(f"Client type {client_type} not available")
            return False
        
        # Disconnect old client if connected
        old_client = self.get_client()
        if old_client and old_client.is_connected:
            try:
                old_client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting old client: {e}")
        
        self._active_type = client_type
        logger.info(f"Switched to MCP client: {self.active_client_name}")
        
        if save:
            self._save_config()
        
        return True
    
    def toggle_client(self, save: bool = True) -> MCPClientType:
        """Toggle between available clients."""
        if self._active_type == MCPClientType.OPEN_MCP:
            new_type = MCPClientType.CONTINUE
        else:
            new_type = MCPClientType.OPEN_MCP
        
        self.switch_client(new_type, save=save)
        return self._active_type
    
    def execute(self, tool_name: str, args: Dict[str, Any], task_type: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool using the active client (or resolved client in AUTO)."""
        # Parse server name from tool: "server_name.tool_name"
        server_name = tool_name.split(".", 1)[0] if "." in tool_name else None
        
        client = self.get_client(task_type=task_type, server_name=server_name)
        if not client:
            return {
                "success": False,
                "error": f"No active MCP client available"
            }
        
        try:
            if not client.is_connected:
                if not client.connect():
                    return {
                        "success": False,
                        "error": "Failed to connect to MCP client"
                    }
            
            logger.info(f"Executing MCP Tool '{tool_name}' via {self.active_client_name} args={json.dumps(args, default=str)[:100]}")
            result = client.execute_tool(tool_name, args)
            if result.get("success"):
                logger.info(f"MCP Tool '{tool_name}' executed successfully.")
            else:
                logger.error(f"MCP Tool '{tool_name}' failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool via MCP client: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_task(self, task: str, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a high-level task/prompt by routing it to the most capable client.
        This is the core of the Meta-Plan execution.
        """
        client = self.get_client(task_type=task_type)
        if not client:
            return {"success": False, "error": "No client available for task execution"}
            
        try:
            if not client.is_connected:
                client.connect()
                
            # Inject context if available
            final_task = task
            if PROMPT_ENGINE_AVAILABLE:
                try:
                    context = prompt_engine.construct_context(task)
                    if context:
                        final_task = f"{context}\n\nTask: {task}"
                except Exception:
                    pass
                    
            logger.info(f"Routing Meta-Task to {self.active_client_name}: {task[:50]}...")
            return client.execute_task(final_task)
        except Exception as e:
            logger.error(f"Error executing meta-task: {e}")
            return {"success": False, "error": str(e)}

    def execute_prompt(self, prompt: str) -> Dict[str, Any]:
        """Backward compatibility for prompt execution."""
        return self.execute_task(prompt)
    
    def list_available_clients(self) -> List[Dict[str, Any]]:
        """List all available MCP clients with their status."""
        result = []
        for ct in MCPClientType:
            client = self._clients.get(ct)
            result.append({
                "type": ct.value,
                "name": {
                    MCPClientType.OPEN_MCP: "Open-MCP (CopilotKit)",
                    MCPClientType.CONTINUE: "Continue CLI",
                    MCPClientType.NATIVE: "Native SDK",
                    MCPClientType.CLINE: "Cline"
                }.get(ct, ct.value),
                "available": client is not None,
                "connected": client.is_connected if client else False,
                "active": ct == self._active_type,
                "categories": self._config.get("mcpClients", {}).get(ct.value, {}).get("categories", [])
            })
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall manager status."""
        client = self.get_client()
        return {
            "active_client": self._active_type.value,
            "active_client_name": self.active_client_name,
            "client_connected": client.is_connected if client else False,
            "available_clients": [ct.value for ct in self._clients.keys()],
            "client_status": client.get_status() if client else None
        }


# Global singleton instance
_manager_instance: Optional[MCPClientManager] = None


def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MCPClientManager()
    return _manager_instance


def reset_mcp_client_manager() -> None:
    """Reset the global MCP client manager instance."""
    global _manager_instance
    if _manager_instance:
        # Disconnect all clients
        for client in _manager_instance._clients.values():
            if client and client.is_connected:
                try:
                    client.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting client {client}: {e}")
    _manager_instance = None
