
import asyncio
import json
import os
import sys
import time

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.mcp_registry import MCPToolRegistry

def test_live_search():
    reg = MCPToolRegistry()
    
    print("Navigating to Google...")
    res_nav = reg.execute("browser_open_url", {"url": "https://www.google.com"})
    print(f"Navigation result: {res_nav}")
    
    time.sleep(5) # Wait for page load
    
    print("Typing search query...")
    # Using the exact same call Tetyana would make
    res_type = reg.execute("browser_type_text", {
        "selector": "textarea[name='q']",
        "text": "The Matrix movie",
        "press_enter": True
    })
    print(f"Typing result: {res_type}")
    
    time.sleep(5) # Wait for results
    
    print("Capturing snapshot for verification...")
    res_snap = reg.execute("browser_snapshot", {})
    print(f"Snapshot result contains 'The Matrix': {'matrix' in str(res_snap).lower()}")

if __name__ == "__main__":
    test_live_search()
