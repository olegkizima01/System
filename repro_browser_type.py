
import asyncio
import time
import sys
import os

sys.path.append(os.getcwd())

async def test_browser_interaction():
    print("🚀 Starting Browser Repro...")
    try:
        from mcp_integration.core.mcp_client_manager import get_mcp_client_manager
        
        mgr = get_mcp_client_manager()
        client = mgr.get_client()
        
        print(f"Client: {type(client).__name__}")
        
        # 1. Open YouTube
        print("1. Opening YouTube...")
        res = client.execute("browser_open_url", {"url": "https://www.youtube.com"})
        print(f"   Result: {res}")
        
        # 2. Wait a bit
        time.sleep(5)
        
        # 3. Type text
        print("2. Typing search query...")
        # 'input#search' is a common selector, but let's try the smart one or a generic one
        res = client.execute("browser_type_text", {"selector": "input#search", "text": "popular music video"})
        print(f"   Result: {res}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browser_interaction())
