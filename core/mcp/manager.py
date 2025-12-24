"""
Manager for switching between MCP clients.
Currently standardized on the Native SDK.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

from core.logging_config import get_logger
from .base import MCPClientType, BaseMCPClient
from .client import NativeMCPClient

logger = get_logger("mcp.manager")

class MCPClientManager:
    """Manager for MCP clients. Singleton."""
    
    CONFIG_KEY = "activeClient"
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path or self._default_config_path()
        self._config = self._load_config()
        self._clients: Dict[MCPClientType, BaseMCPClient] = {}
        self._active_type: MCPClientType = self._get_active_from_config()
        
        # Lazy-load clients
        self._init_clients()
    
    def _default_config_path(self) -> str:
        """Get default config path. Prefers user home directory."""
        user_config = os.path.expanduser("~/.kinotavr/mcp_config.json")
        if os.path.exists(user_config):
            return user_config
            
        # Fallback to internal config
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # System/
        return os.path.join(base, "mcp_integration", "config", "mcp_config.json")
    
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
        active_str = str(self._config.get(self.CONFIG_KEY, "native")).lower()
        try:
            return MCPClientType(active_str)
        except ValueError:
            return MCPClientType.NATIVE
    
    def _init_clients(self) -> None:
        """Initialize client instances (lazy loading)."""
        clients_config = self._config.get("mcpClients", {})
        
        try:
            native_cfg = clients_config.get("native", {})
            native_cfg["mcp_config_path"] = self._config_path
            self._clients[MCPClientType.NATIVE] = NativeMCPClient(native_cfg)
        except Exception as e:
            logger.error(f"Failed to initialize NativeMCPClient: {e}")
    
    @property
    def active_client(self) -> MCPClientType:
        """Get currently active client type."""
        return self._active_type
    
    def get_client(self) -> Optional[BaseMCPClient]:
        """Get the active client instance."""
        # Always return Native for now
        return self._clients.get(MCPClientType.NATIVE)
    
    def execute(self, tool_name: str, args: Dict[str, Any], task_type: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool using the active client."""
        client = self.get_client()
        if not client:
            return {"success": False, "error": "No active MCP client available"}
        
        try:
            if not client.is_connected:
                if not client.connect():
                    return {"success": False, "error": "Failed to connect to MCP client"}
            
            logger.info(f"Executing MCP Tool '{tool_name}' args={json.dumps(args, default=str)[:100]}...")
            result = client.execute_tool(tool_name, args)
            
            if result.get("success"):
                logger.info(f"MCP Tool '{tool_name}' executed successfully.")
            else:
                logger.error(f"MCP Tool '{tool_name}' failed: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool via MCP client: {e}")
            return {"success": False, "error": str(e)}

    def list_available_clients(self) -> List[Dict[str, Any]]:
        """List all available MCP clients."""
        return [{
            "type": "native",
            "name": "Native SDK",
            "available": True,
            "connected": self._clients.get(MCPClientType.NATIVE).is_connected if MCPClientType.NATIVE in self._clients else False,
            "active": True
        }]

# Global singleton instance
_manager_instance: Optional[MCPClientManager] = None

def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MCPClientManager()
    return _manager_instance
