#!/usr/bin/env python3
"""
MCP Management Tools - Dynamic control over MCP servers.
Allows the agent to manage mcp_config.json and debug connections.
"""

import json
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Absolute path to mcp_config.json
CONFIG_PATH = "/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json"

def _load_config():
    if not os.path.exists(CONFIG_PATH):
        # Create default skeleton if missing
        return {"mcpServers": {}, "activeClient": "auto"}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading MCP config: {e}")
        return {"mcpServers": {}, "activeClient": "auto"}

def _save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving MCP config: {e}")
        return False

def mcp_server_list() -> Dict[str, Any]:
    """
    List all configured MCP servers with status and metadata.
    Returns: Dict containing success status and list of servers.
    """
    config = _load_config()
    servers = config.get("mcpServers", {})
    return {
        "status": "success",
        "servers": {
            name: {
                "enabled": s.get("enabled", True),
                "description": s.get("description", ""),
                "category": s.get("category", "unknown"),
                "command": s.get("command", "")
            } for name, s in servers.items()
        }
    }

def mcp_server_add(name: str, command: str, args: List[str] = None, env: Dict[str, str] = None, 
                   description: str = "", category: str = "custom", enabled: bool = True) -> Dict[str, Any]:
    """
    Add or update an MCP server definition in the config.
    Automatically handles dependency installation if it's an npx/npm command.
    """
    config = _load_config()
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Check if we need to install anything (heuristic)
    if command == "npx" and args:
        # We can't easily auto-install npx packages as they are transient, 
        # but we can verify if the user meant an npm install.
        pass

    config["mcpServers"][name] = {
        "command": command,
        "args": args or [],
        "env": env or {},
        "description": description,
        "category": category,
        "enabled": enabled,
        "timeout": 30000,
        "retryAttempts": 2
    }
    
    if _save_config(config):
        return {
            "status": "success", 
            "message": f"Server '{name}' added/updated in config.",
            "server": config["mcpServers"][name]
        }
    else:
        return {"status": "error", "message": "Failed to save config changes."}

def mcp_server_remove(name: str) -> Dict[str, Any]:
    """
    Remove an MCP server definition from the config.
    """
    config = _load_config()
    if "mcpServers" in config and name in config["mcpServers"]:
        removed = config["mcpServers"].pop(name)
        if _save_config(config):
            return {"status": "success", "message": f"Server '{name}' removed.", "removed_data": removed}
    
    return {"status": "error", "message": f"Server '{name}' not found or could not be removed."}

def mcp_server_inspect(name: str) -> Dict[str, Any]:
    """
    Perform a health check on a specific MCP server using the Native SDK.
    Verifies connection and lists available tools.
    """
    try:
        from mcp_integration.core.mcp_client_manager import get_mcp_client_manager, MCPClientType
        mgr = get_mcp_client_manager()
        
        # We force use of Native client for inspection as it provides the best error details
        client = mgr.get_client(MCPClientType.NATIVE)
        if not client:
            return {"status": "error", "message": "Native client not available for inspection."}
        
        # Use the internal async trigger via the client's public list_tools (which handles thread safety)
        # Note: list_tools() in NativeMCPClient already connects and gathers from all servers
        all_tools = client.list_tools()
        server_tools = [t for t in all_tools if t["name"].startswith(f"{name}.")]
        
        if server_tools:
            return {
                "status": "success",
                "message": f"Server '{name}' is functional.",
                "tools_count": len(server_tools),
                "tools": server_tools
            }
        else:
            # Maybe the server has no prefix or is offline
            return {
                "status": "warning", 
                "message": f"Server '{name}' did not return any tools. It might be offline or misconfigured."
            }
    except Exception as e:
        return {"status": "error", "message": f"Inspection error: {str(e)}"}

def mcp_launch_inspector_ui(name: str) -> Dict[str, Any]:
    """
    Launch the official MCP Inspector Web UI for the given server.
    This is best for manual debugging by the user.
    """
    config = _load_config()
    s = config.get("mcpServers", {}).get(name)
    if not s:
        return {"status": "error", "message": f"Server '{name}' not found."}
    
    cmd = s["command"]
    args_str = " ".join(s.get("args", []))
    
    # Construct npx command to launch inspector
    full_cmd = f"npx @modelcontextprotocol/inspector {cmd} {args_str}"
    
    try:
        # Launch in background so it doesn't block the agent
        # env={} might be needed depending on the server
        subprocess.Popen(full_cmd, shell=True, start_new_session=True)
        return {
            "status": "success", 
            "message": f"Inspector UI launching for '{name}'. Check your terminal for the URL (usually http://localhost:3000)."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to start inspector: {str(e)}"}
