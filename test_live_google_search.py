
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
    
    # 2. Typing 'The Matrix' using CSS (Bridge)
    print("\n2. Typing 'The Matrix' using CSS (Bridge)...")
    res = reg.execute("browser_type_text", {"selector": "textarea[name='q']", "text": "The Matrix movie", "press_enter": True})
    print(f"Type Result: Success (Returned data length: {len(str(res))})")

    # 3. Taking snapshot to get a REF
    print("\n3. Taking snapshot to get a REF...")
    snap_data = reg.execute("browser_snapshot", {})
    
    import re
    # Find a ref for a link containing 'The Matrix'
    match = re.search(r"link \".*?Matrix.*?\" \[ref=(e\d+)\]", str(snap_data))
    if match:
        ref_id = f"ref={match.group(1)}"
        print(f"Found REF ID for Matrix link: {ref_id}")
        
        # 4. Clicking using REF (Native)
        print(f"\n4. Clicking {ref_id} using REF (Native)...")
        click_res = reg.execute("browser_click_element", {"selector": ref_id})
        print(f"Click Result: Success (Returned data length: {len(str(click_res))})")
    else:
        print("❌ Could not find a Matrix link with ref in snapshot.")

    # 5. Verify results
    print("\n5. Verifying final state...")
    final_snap = reg.execute("browser_snapshot", {})
    if "The Matrix" in str(final_snap):
        print("✅ SUCCESS: Hybrid interaction verified!")
    else:
        print("❌ FAILURE: Matrix not found in final state.")

if __name__ == "__main__":
    asyncio.run(test_search())
