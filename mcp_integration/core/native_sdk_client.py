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
import sys
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

# Silence ChromaDB/PostHog noise
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

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
        self._exit_stacks: Dict[str, AsyncExitStack] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._server_params: Dict[str, StdioServerParameters] = {}
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._lock = threading.Lock()
        self._connected = False
        
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
        """Gracefully close a persistent session and its transport."""
        if name in self._exit_stacks:
            stack = self._exit_stacks.pop(name)
            await stack.aclose()
        if name in self._sessions:
            self._sessions.pop(name)
        if name in self._session_locks:
            self._session_locks.pop(name)

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
        try:
            return fut.result(timeout=60)
        except Exception as e:
            return {"success": False, "error": f"Tool execution timeout or error: {str(e)}"}

    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a high-level task via Native SDK by routing it 
        to the most relevant server tool.
        """
        task_lower = task.lower()
        
        # Determine target server
        target_server = "context7" 
        if any(kw in task_lower for kw in ["file", "read", "write", "directory", "folder"]):
            target_server = "filesystem"
        elif any(kw in task_lower for kw in ["browser", "web", "url", "navigate", "search", "google"]):
            target_server = "playwright"
        elif any(kw in task_lower for kw in ["memory", "knowledge", "recall", "learn"]):
            target_server = "memory"
        
        # Instead of just erroring, we try to use a "meta" or "execute" tool if available
        # Or we try to use the most common tool on that server if the task looks like one.
        
        # For Context7, we usually want 'retrieve' or 'store'
        if target_server == "context7":
             if "store" in task_lower:
                 return self.execute_tool("context7.store", {"data": task})
             else:
                 return self.execute_tool("context7.retrieve", {"query": task})
        
        # For Playwright, it might be a search
        if target_server == "playwright" and "search" in task_lower:
             return self.execute_tool("playwright.browser_search_duckduckgo", {"query": task})

        # Fallback to the previous informative error but now it's more helpful
        return {
            "success": False, 
            "error": f"Native SDK Client: High-level delegation to '{target_server}' requires specific tool calls. Please use explicit tools like '{target_server}.browser_navigate' or use 'continue/cline' for autonomous delegation."
        }

    async def _async_execute_tool(self, server_name: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Internal async implementation with persistent session support."""
        if server_name not in self._session_locks:
            self._session_locks[server_name] = asyncio.Lock()
        
        async with self._session_locks[server_name]:
            try:
                session = self._sessions.get(server_name)
                
                if session is None:
                    logger.info(f"🚀 Initializing persistent session for MCP server: {server_name}")
                    s_config = self._get_server_config(server_name)
                    if not s_config:
                        return {"success": False, "error": f"Server '{server_name}' not configured"}

                    import shutil
                    cmd = s_config["command"]
                    if cmd != "npx" and not shutil.which(cmd):
                        return {
                            "success": False, 
                            "error": f"MCP server command '{cmd}' not found in PATH. Please verify installation or use global install."
                        }

                    params = StdioServerParameters(
                        command=cmd,
                        args=s_config.get("args", []),
                        env={**os.environ, **s_config.get("env", {})}
                    )

                    stack = AsyncExitStack()
                    read, write = await stack.enter_async_context(stdio_client(params))
                    session = await stack.enter_async_context(ClientSession(read, write))
                    
                    await session.initialize()
                    
                    self._exit_stacks[server_name] = stack
                    self._sessions[server_name] = session
                    logger.info(f"✅ Persistent session for {server_name} ready.")
                
                # Call tool
                logger.debug(f"Calling MCP Tool (Persistent): {server_name}.{tool_name}")
                result = await session.call_tool(tool_name, args)
                
                if result.isError:
                    error_out = "".join([c.text for c in result.content if hasattr(c, 'text')])
                    return {
                         "success": False, 
                         "error": error_out or "Unknown tool error"
                    }
                
                output_text = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                return {
                    "success": True,
                    "data": output_text,
                    "raw": str(result)
                }

            except Exception as e:
                logger.error(f"Native MCP Error ({server_name}): {e}")
                await self._close_session(server_name)
                return {"success": False, "error": str(e)}

    def _get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve server parameters from the global mcp_config.json."""
        config_path = self.config.get("mcp_config_path")
        if not config_path or not os.path.exists(config_path):
             # Try default path
             config_path = os.path.expanduser("~/.kinotavr/mcp_config.json")
             if not os.path.exists(config_path):
                  return None
        
        try:
            with open(config_path, 'r') as f:
                full_config = json.load(f)
                return full_config.get("mcpServers", {}).get(name)
        except Exception as e:
            logger.debug(f"Error loading server config for {name}: {e}")
            return None

    def list_tools(self) -> List[Dict[str, str]]:
        """Dynamic listing of all tools across all configured servers."""
        fut = asyncio.run_coroutine_threadsafe(self._async_list_all_tools(), self._loop)
        try:
            return fut.result(timeout=15)
        except Exception as e:
            logger.error(f"Global timeout or error in tool listing: {e}")
            return []

    async def _async_list_all_tools(self) -> List[Dict[str, str]]:
        """Gather tools from all defined servers."""
        config_path = self.config.get("mcp_config_path")
        if not config_path or not os.path.exists(config_path):
             config_path = os.path.expanduser("~/.kinotavr/mcp_config.json")
             if not os.path.exists(config_path):
                  return []

        try:
            with open(config_path, 'r') as f:
                servers_config = json.load(f).get("mcpServers", {})
            
            tasks = []
            server_names = []
            for s_name, s_cfg in servers_config.items():
                if not s_cfg.get("enabled", True): continue
                tasks.append(self._get_tools_from_server(s_name, s_cfg))
                server_names.append(s_name)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_tools = []
            for s_name, res in zip(server_names, results):
                if isinstance(res, Exception):
                    logger.warning(f"Could not list tools for {s_name}: {res}")
                else:
                    all_tools.extend(res)
            
            return all_tools
        except Exception as e:
            logger.error(f"Error in _async_list_all_tools: {e}")
            return []

    async def _get_tools_from_server(self, name: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to get tools from a single server."""
        server_tools = []
        try:
            params = StdioServerParameters(
                command=cfg["command"], 
                args=cfg.get("args", []),
                env={**os.environ, **cfg.get("env", {})}
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_resp = await session.list_tools()
                    for t in tools_resp.tools:
                        server_tools.append({
                            "name": f"{name}.{t.name}",
                            "description": t.description
                        })
        except Exception as e:
            raise Exception(f"Server {name} failed: {e}")
        return server_tools

    def get_status(self) -> Dict[str, Any]:
        return {
            "client": "native_sdk",
            "connected": self._connected,
            "thread_alive": self._thread.is_alive(),
            "active_sessions": list(self._sessions.keys())
        }
