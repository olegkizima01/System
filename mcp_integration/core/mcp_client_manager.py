import subprocess
import json
import os
import shutil
from typing import Dict, Any, Optional

from core.config import settings

class MCPClientManager:
    def __init__(self):
        self.config = settings.mcp
        self.active_client_name = "Native SDK Client"
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific MCP server from settings"""
        server_config = self.config.servers.get(server_name)
        if server_config:
            return server_config.model_dump()

    def switch_client(self, client_type: str, save: bool = True):
        self.active_client_name = client_type
        if save:
            print(f"Client switched to {client_type} and saved.")
    def resolve_client_type(self, context: str):
        if self.active_client_name == MCPClientType.AUTO:
            if context == "DEV":
                return MCPClientType.CONTINUE
            return MCPClientType.OPEN
        return self.active_client_name
        return None
    
    def get_client(self, server_name: str = None, task_type: str = None):
        """Get MCP client for specific server or default"""
        # TODO: Implement actual Native Client retrieval here
        return MockMCPClient()
    
    def execute(self, tool_name: str, args: Dict[str, Any], task_type: str = None):
        """Execute MCP tool"""
        return self.get_client().execute(tool_name, args)
    
    def execute_task(self, task: str, task_type: str = None) -> Dict[str, Any]:
        """
        Execute a high-level task by delegating to appropriate tools.
        This is called via meta.execute_task tool.
        """
        task_lower = str(task or "").lower()
        
        # Browser-related keywords
        browser_keywords = ["browser", "google", "search", "open url", "website", "navigate", "фільм", "онлайн", "пошук"]
        is_browser_task = any(kw in task_lower for kw in browser_keywords)
        
        if is_browser_task:
            return {
                "status": "error",
                "message": f"Delegation to 'meta.execute_task' for browser operations is not supported by this MCP client. Please use granular tools like 'playwright.browser_navigate', 'playwright.browser_click', etc., or 'browser_open_url' directly.",
                "task": task
            }
        
        return {
            "status": "guidance",
            "message": f"Task received: {task}. Use specific tools like run_shell, browser_open_url, etc. instead of meta.execute_task for high-level execution.",
            "task": task,
            "task_type": task_type or "GENERAL"
        }
    
    def start_browser_server(self, browser_name: str = "chromium") -> subprocess.Popen:
        """Start Playwright MCP server"""
        server_config = self.get_server_config("playwright")
        if not server_config or not server_config.get("enabled"):
            raise RuntimeError("Playwright server not configured or disabled")
        
        # Construct command from settings
        cmd_base = server_config["command"]
        args = server_config.get("args", [])
        
        # If Using npx, ensure we look it up or trust shell if global
        # If command is absolute path, use it. If 'npx', let shell find it.
        
        command = [cmd_base] + args
        
        print(f"🚀 Starting Playwright server...")
        print(f"Command: {' '.join(command)}")
        
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return proc
        except Exception as e:
            raise RuntimeError(f"Failed to start Playwright: {e}")
    
    def execute_browser_task(self, task: str, browser_name: str = "chromium") -> Dict[str, Any]:
        """Deprecated: Use granular playwright tools instead."""
        return {
            "status": "error",
            "message": "Delegated task execution is not supported. Use granular tools.",
            "task": task
        }

class MockMCPClient:
    """Mock MCP client for testing"""
    def __init__(self):
        self.is_connected = True
    
    def connect(self):
        return True
    
    def list_tools(self):
        return [
            {"name": "playwright.browser_navigate", "description": "Navigate to URL in browser"},
            {"name": "playwright.browser_click", "description": "Click element in browser"},
            {"name": "playwright.browser_type", "description": "Type text in browser"},
            {"name": "playwright.browser_screenshot", "description": "Take screenshot in browser"},
            {"name": "playwright.browser_close", "description": "Close browser"}
        ]
    
    def execute(self, tool_name: str, args: Dict[str, Any]):
        return {"success": True, "data": f"Executed {tool_name}"}

# Global instance
_global_manager = None

def get_mcp_client_manager():
    """Get the global MCP client manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = MCPClientManager()
    return _global_manager

class MCPClientType:
    NATIVE = "native"
    OPEN = "open"
    CONTINUE = "continue"
    AUTO = "auto"
