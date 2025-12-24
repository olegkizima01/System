
import asyncio
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.mcp_registry import MCPToolRegistry

async def test_search():
    reg = MCPToolRegistry()
    
    print("\n1. Opening Google...")
    res1 = reg.execute("browser_open_url", {"url": "https://www.google.com"})
    print(f"Result: {res1}")
    
    await asyncio.sleep(2)
    
    print("\n2. Typing 'The Matrix'...")
    # Use standard selector
    res2 = reg.execute("browser_type_text", {
        "selector": "textarea[name='q']",
        "text": "The Matrix movie",
        "press_enter": True
    })
    print(f"Result: {res2}")
    
    await asyncio.sleep(5)
    
    print("\n3. Taking snapshot...")
    res3 = reg.execute("browser_snapshot", {})
    # print(f"Snapshot data length: {len(str(res3))}")
    if "The Matrix" in str(res3):
        print("✅ SUCCESS: 'The Matrix' found in snapshot!")
    else:
        print("❌ FAILURE: 'The Matrix' NOT found in search results.")

if __name__ == "__main__":
    asyncio.run(test_search())
