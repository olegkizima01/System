#!/usr/bin/env python3
"""
Native MCP Client - Direct integration using official mcp Python SDK.
Provides high-performance session management for multiple stdio-based servers.
"""

import asyncio
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .mcp_client_manager import BaseMCPClient

logger = logging.getLogger(__name__)

class NativeMCPClient(BaseMCPClient):
    """
    Official MCP Python SDK Client.
    Handles multiple server sessions concurrently within a dedicated event loop thread.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._sessions: Dict[str, ClientSession] = {}
        self._server_params: Dict[str, StdioServerParameters] = {}
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._lock = threading.Lock()
        
    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def connect(self) -> bool:
        """
        Connect is now lazy per-server. 
        This method ensures the background thread is alive.
        """
        if not self._thread.is_alive():
            self._thread.start()
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Shutdown all active sessions."""
        with self._lock:
            for name in list(self._sessions.keys()):
                asyncio.run_coroutine_threadsafe(self._close_session(name), self._loop)
        self._connected = False

    async def _close_session(self, name: str):
        if name in self._sessions:
            # Note: Context manager handling is better, but since we manage 
            # multiple sessions, we use explicit cleanup if needed.
            # Official SDK prefers 'async with stdio_client' which we use in execute.
            pass

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool via the appropriate MCP server session.
        Auto-connects if necessary.
        """
        # Parse server name from tool: "server_name.tool_name"
        parts = name.split(".", 1)
        if len(parts) == 2:
            server_name, tool_name = parts
        else:
            # Fallback if prefix missing
            server_name = self.config.get("default_server", "playwright")
            tool_name = name

        fut = asyncio.run_coroutine_threadsafe(
            self._async_execute_tool(server_name, tool_name, args), 
            self._loop
        )
        return fut.result(timeout=60)

    async def _async_execute_tool(self, server_name: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Internal async implementation of tool execution."""
        try:
            # 1. Get server config
            s_config = self._get_server_config(server_name)
            if not s_config:
                return {"success": False, "error": f"Server '{server_name}' not configured"}

            params = StdioServerParameters(
                command=s_config["command"],
                args=s_config.get("args", []),
                env={**os.environ, **s_config.get("env", {})}
            )

            # 2. Run session for this call (using modern SDK pattern)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    logger.debug(f"Calling MCP Tool: {server_name}.{tool_name}")
                    result = await session.call_tool(tool_name, args)
                    
                    if result.isError:
                        return {
                            "success": False, 
                            "error": "".join([c.text for c in result.content if hasattr(c, 'text')])
                        }
                    
                    # Flatten output
                    output_text = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                    
                    return {
                        "success": True,
                        "data": output_text,
                        "raw": str(result)
                    }

        except Exception as e:
            logger.error(f"Native MCP Error ({server_name}): {e}")
            return {"success": False, "error": str(e)}

    def _get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve server parameters from the global mcp_config.json."""
        config_path = self.config.get("mcp_config_path")
        if not config_path or not os.path.exists(config_path):
            return None
        
        try:
            with open(config_path, 'r') as f:
                full_config = json.load(f)
                return full_config.get("mcpServers", {}).get(name)
        except Exception:
            return None

    def list_tools(self) -> List[Dict[str, str]]:
        """Dynamic listing of all tools across all configured servers."""
        fut = asyncio.run_coroutine_threadsafe(self._async_list_all_tools(), self._loop)
        return fut.result(timeout=30)

    async def _async_list_all_tools(self) -> List[Dict[str, str]]:
        """Gather tools from all servers defined in config."""
        all_tools = []
        config_path = self.config.get("mcp_config_path")
        if not config_path or not os.path.exists(config_path):
            return []

        try:
            with open(config_path, 'r') as f:
                servers = json.load(f).get("mcpServers", {})
            
            for s_name, s_cfg in servers.items():
                if not s_cfg.get("enabled", True): continue
                # We prefix names to ensure registry clarity
                # Note: For efficiency, we might want to cache this instead of connecting to all
                # But for the initial implementation, let's keep it simple.
                try:
                    params = StdioServerParameters(
                        command=s_cfg["command"], 
                        args=s_cfg.get("args", []),
                        env={**os.environ, **s_cfg.get("env", {})}
                    )
                    async with stdio_client(params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            tools = await session.list_tools()
                            for t in tools.tools:
                                all_tools.append({
                                    "name": f"{s_name}.{t.name}",
                                    "description": t.description
                                })
                except Exception as e:
                    logger.warning(f"Could not list tools for {s_name}: {e}")
        except Exception:
            pass
        return all_tools

    def get_status(self) -> Dict[str, Any]:
        return {
            "client": "native_sdk",
            "connected": self._connected,
            "thread_alive": self._thread.is_alive()
        }
