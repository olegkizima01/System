
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

async def debug_refs():
    mgr = get_mcp_client_manager()
    client = mgr.get_client()
    if not client.is_connected:
        client.connect()
    
    await asyncio.sleep(2)
    
    # 1. Open Google
    mgr.execute("playwright.browser_run_code", {"code": "async (page) => { await page.goto('https://www.google.com'); await page.waitForLoadState('networkidle'); }"})
    
    # 2. Take Snapshot
    print("Taking snapshot...")
    snap = mgr.execute("playwright.browser_snapshot", {})
    print(f"Snapshot received (first 500 chars): {str(snap)[:500]}...")
    
    # 3. Check DOM for attributes
    print("\nChecking DOM for data-mcp-ref...")
    check_code = """async (page) => {
        const elements = await page.evaluate(() => {
            const all = document.querySelectorAll('*');
            const withRefs = [];
            for (const el of all) {
                const attrs = el.attributes;
                for (let i = 0; i < attrs.length; i++) {
                    if (attrs[i].name.includes('mcp') || attrs[i].name === 'ref') {
                        withRefs.push({tag: el.tagName, attr: attrs[i].name, value: attrs[i].value});
                    }
                }
            }
            return withRefs.slice(0, 50);
        });
        return JSON.stringify(elements);
    }"""
    res = mgr.execute("playwright.browser_run_code", {"code": check_code})
    print(f"DOM Check Result: {res}")

if __name__ == "__main__":
    asyncio.run(debug_refs())
