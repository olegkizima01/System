#!/usr/bin/env python3
"""
Verification script for MCP Management Tools.
"""

import sys
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.mcp_registry import MCPToolRegistry

def test_mcp_management():
    print("🚀 Starting MCP Management Verification...")
    registry = MCPToolRegistry()
    
    # 1. List current servers
    print("\n📋 Listing current servers...")
    res = registry.execute("mcp_server_list", {})
    # mcp_server_list returns a dict, registry.execute returns a string (serialized) or object
    # Actually, in mcp_registry.py, execute() returns a string for most tools
    print(f"Servers found: {res}")

    # 2. Add a temporary test server
    # We use a simple echo server as a test
    print("\n➕ Adding test server 'echo-test'...")
    add_args = {
        "name": "echo-test",
        "command": "python3",
        "args": ["-c", "import sys; print('{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"tools\":[]}}');"],
        "description": "A temporary echo server for testing management tools."
    }
    # Note: the command above won't actually work as a real MCP server but we want to see if it adds to config
    res_add = registry.execute("mcp_server_add", add_args)
    print(f"Add result: {res_add}")

    # Verify transition in config
    with open("/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json", "r") as f:
        cfg = json.load(f)
        if "echo-test" in cfg.get("mcpServers", {}):
            print("✅ 'echo-test' successfully added to mcp_config.json")
        else:
            print("❌ 'echo-test' NOT found in config")

    # 3. Inspect (this might fail if the server isn't a real MCP server, but we check the call)
    print("\n🔍 Inspecting 'echo-test'...")
    res_inspect = registry.execute("mcp_server_inspect", {"name": "echo-test"})
    print(f"Inspect result: {res_inspect}")

    # 4. Remove the test server
    print("\n➖ Removing 'echo-test'...")
    res_remove = registry.execute("mcp_server_remove", {"name": "echo-test"})
    print(f"Remove result: {res_remove}")

    # Verify removal
    with open("/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json", "r") as f:
        cfg = json.load(f)
        if "echo-test" not in cfg.get("mcpServers", {}):
            print("✅ 'echo-test' successfully removed from mcp_config.json")
        else:
            print("❌ 'echo-test' STILL in config")

    print("\n✨ Management verification complete.")

if __name__ == "__main__":
    test_mcp_management()
