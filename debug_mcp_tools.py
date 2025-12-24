
import asyncio
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from mcp_integration.core.mcp_client_manager import get_mcp_client_manager, MCPClientType

async def list_playwright_tools():
    manager = get_mcp_client_manager()
    # Ensure native client is active
    manager.switch_client(MCPClientType.NATIVE)
    client = manager.get_client(MCPClientType.NATIVE)
    
    print("Connecting to Native MCP Client...")
    if not client.connect():
        print("Failed to connect to Native Client")
        return

    print("Fetching server tools...")
    tools = await client._async_list_all_tools()
    
    print("\nAvailable Playwright Tools:")
    for t in tools:
        if t['name'].startswith("playwright."):
            print(f"- {t['name']}: {t['description'][:100]}...")

if __name__ == "__main__":
    asyncio.run(list_playwright_tools())
