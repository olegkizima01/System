
import asyncio
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

async def inspect():
    mgr = get_mcp_client_manager()
    client = mgr.get_client()
    if not client.is_connected:
        client.connect()
    
    # Wait a bit for background thread to connect
    await asyncio.sleep(2)
    
    target = sys.argv[1] if len(sys.argv) > 1 else "playwright"
    
    # Access the sessions directly from the client's internal dict
    with client._lock: # It's a threading.Lock
        sessions_copy = dict(client._sessions)
        
    for name, session in sessions_copy.items():
            if target and target.split('.')[0] != name: continue
            print(f"\n--- Server: {name} ---")
            stools = await session.list_tools()
            for st in stools.tools:
                if target and target.split('.')[-1] not in st.name: continue
                print(f"\nTool: {st.name}")
                print(f"Desc: {st.description}")
                print(f"Schema: {json.dumps(st.inputSchema, indent=2)}")

if __name__ == "__main__":
    asyncio.run(inspect())
