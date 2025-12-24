
import asyncio
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from mcp_integration.core.mcp_client_manager import get_mcp_client_manager, MCPClientType

async def inspect_playwright_schema():
    manager = get_mcp_client_manager()
    manager.switch_client(MCPClientType.NATIVE)
    client = manager.get_client(MCPClientType.NATIVE)
    
    server_name = "playwright"
    
    # 1. Force session initialization by calling a tool
    print(f"Triggering session for {server_name}...")
    # browser_tabs is usually safe to call
    await client._async_execute_tool(server_name, "browser_tabs", {})
    
    session = client._sessions.get(server_name)
    if not session:
        print(f"Failed to get session for {server_name}")
        return

    tools_resp = await session.list_tools()
    
    print("\nDetailed Tool Schema:")
    for t in tools_resp.tools:
        if t.name in ["browser_type", "browser_click", "browser_navigate", "browser_fill"]:
            print(f"\nTool: {t.name}")
            print(f"Description: {t.description}")
            print(f"Arguments Schema: {json.dumps(t.inputSchema, indent=2)}")

if __name__ == "__main__":
    asyncio.run(inspect_playwright_schema())
