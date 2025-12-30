#!/usr/bin/env python3
"""
Test script for Native MCP Client integration.
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

def test_native_mcp():
    print("🚀 Starting Native MCP Verification...")
    registry = MCPToolRegistry()
    
    # 1. Switch to Native client
    print("\n🔄 Switching to Native client...")
    success = registry.set_mcp_client("native")
    if success:
        print(f"✅ Successfully switched to: {registry.get_active_mcp_client_name()}")
    else:
        print("❌ Failed to switch to Native client")
        return

    # 2. List tools
    print("\n--- Tools from Native SDK ---")
    tools_list = registry.list_tools()
    print(f"Found tools section: {'--- Tools from Native SDK' in tools_list}")
    
    # Let's count how many native tools we found
    native_tools = [line for line in tools_list.split('\n') if ':' in line and not line.startswith('---')]
    print(f"Total tools discovered: {len(native_tools)}")
    
    if len(native_tools) > 0:
        print("✅ Tools discovered successfully.")
    else:
        print("⚠️ No tools found. Check if servers are installed and mcp_config.json is correct.")

    # 3. Test execution (Playwright navigate as basic test)
    # We use a tool that we know exists in mcp_config.json
    print("\n⚡ Testing tool execution (playwright.playwright_navigate)...")
    try:
        # We use a non-existent URL just to see if the tool responds (should be fast)
        # Note: We need a real server installed for this to truly "pass"
        res = registry.execute("playwright.playwright_navigate", {"url": "about:blank"})
        print(f"Result: {res[:200]}...")
    except Exception as e:
        print(f"Caught expected error or failure: {e}")

    print("\n✨ Verification complete.")

if __name__ == "__main__":
    test_native_mcp()
