
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

async def list_all():
    mgr = get_mcp_client_manager()
    client = mgr.get_client()
    if not client.is_connected:
        client.connect()
    
    await asyncio.sleep(2)
    
    tools = await client._async_list_all_tools()
    print("\n--- ALL AVAILABLE MCP TOOLS ---")
    for t in sorted(tools, key=lambda x: x['name']):
        print(f"{t['name']}")

if __name__ == "__main__":
    asyncio.run(list_all())
