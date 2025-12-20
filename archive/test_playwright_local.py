import sys
import os
import json

# Add repo root to sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from system_ai.tools.browser import browser_open_url, browser_screenshot, browser_get_content

def test_browser():
    print("Testing Playwright (Local Tools)...")
    
    # 1. Open Google
    print("Opening Google...")
    res = browser_open_url("https://www.google.com", headless=False)
    print(f"Open URL Result: {res}")
    
    # 2. Get Content
    print("Getting Content...")
    content = browser_get_content()
    print(f"Content length: {len(content)}")
    
    # 3. Take Screenshot
    print("Taking Screenshot...")
    ss_res = browser_screenshot()
    print(f"Screenshot Result: {ss_res}")
    
    data = json.loads(ss_res)
    if data.get("status") == "success":
        path = data.get("path")
        if os.path.exists(path):
            print(f"✅ Playwright test successful. Screenshot saved at: {path}")
        else:
            print(f"❌ Playwright test failed: File not found at {path}")
    else:
        print(f"❌ Playwright test failed: {data.get('error')}")

if __name__ == "__main__":
    test_browser()
