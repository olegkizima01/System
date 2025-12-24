
import asyncio
import json
import os
import sys

sys.path.append(os.getcwd())
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

async def capture_schemas():
    mgr = get_mcp_client_manager()
    client = mgr.get_client()
    if not client.is_connected:
        client.connect()
    
    await asyncio.sleep(3)
    
    schemas = {}
    with client._lock:
        sessions_copy = dict(client._sessions)
        
    for name, session in sessions_copy.items():
        if name != "playwright": continue
        stools = await session.list_tools()
        for st in stools.tools:
            schemas[st.name] = st.inputSchema
            
    with open("mcp_schemas.json", "w") as f:
        json.dump(schemas, f, indent=2)
    print("Schemas captured to mcp_schemas.json")

if __name__ == "__main__":
    asyncio.run(capture_schemas())
