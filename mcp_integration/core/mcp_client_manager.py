import subprocess
import json
import os
from typing import Dict, Any, Optional

class MCPClientManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json"
        self.config = self._load_config()
        self.active_client = self.config.get("activeClient", "native")
        self.active_client_name = "Native SDK Client"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from JSON file"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load MCP config: {e}")
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific MCP server"""
        servers = self.config.get("mcpServers", {})
        return servers.get(server_name)
    
    def get_client(self, server_name: str = None, task_type: str = None):
        """Get MCP client for specific server or default"""
        return MockMCPClient()
    
    def execute(self, tool_name: str, args: Dict[str, Any], task_type: str = None):
        """Execute MCP tool"""
        return self.get_client().execute(tool_name, args)
    
    def execute_task(self, task: str, task_type: str = None) -> Dict[str, Any]:
        """
        Execute a high-level task by delegating to appropriate tools.
        This is called via meta.execute_task tool.
        
        For browser-related tasks, delegates to browser_execute.
        For other tasks, returns guidance for the agent to use specific tools.
        """
        task_lower = str(task or "").lower()
        
        # Browser-related keywords
        browser_keywords = ["browser", "google", "search", "open url", "website", "navigate", "фільм", "онлайн", "пошук"]
        is_browser_task = any(kw in task_lower for kw in browser_keywords)
        
        if is_browser_task:
            return self.execute_browser_task(task)
        
        # For non-browser tasks, return guidance
        return {
            "status": "guidance",
            "message": f"Task received: {task}. Use specific tools like run_shell, browser_open_url, etc. instead of meta.execute_task for execution.",
            "task": task,
            "task_type": task_type or "GENERAL"
        }
    
    def start_browser_server(self, browser_name: str = "chromium") -> subprocess.Popen:
        """Start Playwright MCP server with specific browser"""
        server_config = self.get_server_config("playwright")
        if not server_config:
            raise RuntimeError("Playwright server not configured")
        
        command = [server_config["command"]]
        command.extend(server_config.get("args", []))
        
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
        """Execute browser task with specific browser"""
        try:
            proc = self.start_browser_server(browser_name)
            return {
                "status": "success",
                "browser": browser_name,
                "task": task,
                "message": f"Browser {browser_name} started for task: {task}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "browser": browser_name,
                "task": task
            }

class MockMCPClient:
    """Mock MCP client for testing"""
    def __init__(self):
        self.is_connected = True
    
    def connect(self):
        """Mock connect"""
        return True
    
    def list_tools(self):
        """List available tools"""
        return [
            {"name": "playwright.browser_navigate", "description": "Navigate to URL in browser"},
            {"name": "playwright.browser_click", "description": "Click element in browser"},
            {"name": "playwright.browser_type", "description": "Type text in browser"},
            {"name": "playwright.browser_screenshot", "description": "Take screenshot in browser"},
            {"name": "playwright.browser_close", "description": "Close browser"}
        ]
    
    def execute(self, tool_name: str, args: Dict[str, Any]):
        """Execute tool"""
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
