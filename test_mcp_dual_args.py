
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

async def test_dual_args():
    mgr = get_mcp_client_manager()
    client = mgr.get_client()
    if not client.is_connected:
        client.connect()
    
    await asyncio.sleep(2)
    
    # 1. Open Google
    mgr.execute("playwright.browser_run_code", {"code": "async (page) => { await page.goto('https://www.google.com'); }"})
    
    # 2. Get a Ref
    snap = mgr.execute("playwright.browser_snapshot", {})
    import re
    match = re.search(r"button \".*?\" \[ref=(e\d+)\]", str(snap))
    if not match:
        print("No ref found")
        return
    
    ref_id = match.group(1)
    print(f"Testing ref: {ref_id}")
    
    # 3. Try Dual Args
    print("\nTrying with DUAL ARGS (ref + empty element)...")
    res = mgr.execute("playwright.browser_click", {"ref": ref_id, "element": ""})
    print(f"Dual Args Result: {res}")

if __name__ == "__main__":
    asyncio.run(test_dual_args())
