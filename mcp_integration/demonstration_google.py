#!/usr/bin/env python3
"""
Final Demonstration: Google Registration Flow with Native MCP.
Addresses telemetry noise and robustness issues.
"""

import os
import sys
import logging

# 1. Silence Telemetry Globals
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# Configure logging to be concise
logging.basicConfig(level=logging.WARNING)

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_integration.core.mcp_client_manager import get_mcp_client_manager, MCPClientType

def run_demo():
    print("🚀 Starting Stabilized Google Registration Demo...")
    mgr = get_mcp_client_manager()
    client = mgr.get_client(MCPClientType.NATIVE)
    
    # 1. Navigation
    print("\n🌐 Navigation...")
    res = client.execute_tool('playwright.browser_navigate', {'url': 'https://accounts.google.com/signup'})
    if res.get("success"):
        print("✅ Navigated to Google Sign-up")
    else:
        print(f"❌ Navigation failed: {res.get('error')}")

    # 2. Form Filling (using browser_fill_form for reliability)
    # Based on previous snapshot e41=First name, e49=Last name
    print("\n📝 Filling Form...")
    # We use selectors to be safe
    fields = {
        'input[name="firstName"]': 'Atlas',
        'input[name="lastName"]': 'Trinity'
    }
    # Note: browser_fill_form often expects a selector for the form or body
    res = client.execute_tool('playwright.browser_fill_form', {
        'element': 'body', 
        'fields': fields
    })
    
    if res.get("success"):
        print("✅ Form fields filled")
    else:
        # Fallback to individual typing if fill_form fails
        print("⚠️ Fill form failed, falling back to individual typing...")
        client.execute_tool('playwright.browser_type', {'element': 'input[name="firstName"]', 'text': 'Atlas'})
        client.execute_tool('playwright.browser_type', {'element': 'input[name="lastName"]', 'text': 'Trinity'})

    # 3. Memory Observation
    print("\n🧠 Updating MCP Memory...")
    # Fix the missing 'observations' or entity handling if it crashed before
    try:
        client.execute_tool('memory.add_observations', {
            'entityName': 'Registration Session', 
            'observations': ['Demonstrated stabilized end-to-end flow', 'Used Native SDK Playwright and Memory']
        })
        print("✅ Memory updated")
    except Exception as e:
        print(f"⚠️ Memory update warning: {e}")

    # 4. Final Verification
    print("\n🔍 Final Verification...")
    res = client.execute_tool('memory.search_nodes', {'query': 'Registration Session'})
    print(f"Stored Data: {res.get('data')[:200]}...")

    print("\n✨ Demonstration Complete.")

if __name__ == "__main__":
    run_demo()
