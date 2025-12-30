#!/usr/bin/env python3
"""
MCP Server Manager - Integration class for Context7, SonarQube and other MCP servers.
This version bridges legacy calls to the modern Native SDK Client.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod

# Internal imports
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager, MCPClientType

# Set up logging
logger = logging.getLogger(__name__)

# Simple metric for MCP fallbacks (kept for compatibility)
CONTEXT7_FALLBACK_COUNT = 0

def get_mcp_metrics() -> dict:
    return {"context7_fallback_count": CONTEXT7_FALLBACK_COUNT}


class MCPServerClient(ABC):
    """Bridge interface for legacy MCP client calls"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.manager = get_mcp_client_manager()
        
    @abstractmethod
    def connect(self) -> bool:
        pass
    
    @abstractmethod
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass


class UnifiedBridgeClient(MCPServerClient):
    """A client that bridges legacy execute_command calls to official MCP tool calls."""
    
    def connect(self) -> bool:
        client = self.manager.get_client(MCPClientType.NATIVE)
        if client:
            return client.connect()
        return False

    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Map legacy command names to modern tool names.
        Example: execute_command("store", data="...") -> execute_tool("context7.store", {"data": "..."})
        """
        # Map legacy commands to server tools
        # For context7
        if self.name == "context7" or self.name == "context7-docs":
            tool_map = {
                "store": "context7.store",
                "retrieve": "context7.retrieve",
                "status": "context7.status",
                "list": "context7.list_memories"
            }
            tool_name = tool_map.get(command, f"context7.{command}")
            res = self.manager.execute(tool_name, kwargs)
            return res
            
        # For sonarqube
        elif self.name == "sonarqube":
             tool_name = f"sonarqube.{command}"
             return self.manager.execute(tool_name, kwargs)

        return {"success": False, "error": f"Unknown mapping for {self.name}.{command}"}

    def get_status(self) -> Dict[str, Any]:
        return self.execute_command("status")


class Context7Client(UnifiedBridgeClient):
    """Legacy alias for Context7 bridge"""
    pass

class SonarQubeClient(UnifiedBridgeClient):
    """Legacy alias for SonarQube bridge"""
    pass

class MCPManager:
    """Modern MCP Manager that maintains backward compatibility with legacy code."""
    
    def __init__(self):
        self._client_mgr = get_mcp_client_manager()
        self.clients = {}
        self._initialize_legacy_clients()
        
    def _initialize_legacy_clients(self):
        """Create bridge clients for legacy callers."""
        # We manually add bridges for the expected names
        for name in ["context7", "context7-docs", "sonarqube", "copilot"]:
             self.clients[name] = UnifiedBridgeClient(name, {})
        
        logger.info(f"Initialized {len(self.clients)} MCP bridge clients")
    
    def get_client(self, server_name: str) -> Optional[MCPServerClient]:
        return self.clients.get(server_name)
    
    def connect_all(self) -> Dict[str, bool]:
        results = {}
        for name, client in self.clients.items():
            results[name] = client.connect()
        return results
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for name, client in self.clients.items():
            results[name] = client.get_status()
        return results
    
    def execute_on_server(self, server_name: str, command: str, **kwargs) -> Dict[str, Any]:
        client = self.get_client(server_name)
        if client:
            return client.execute_command(command, **kwargs)
        else:
            return {"success": False, "error": f"Server {server_name} not found"}


if __name__ == "__main__":
    manager = MCPManager()
    print("Bridge MCP Manager Initialized")