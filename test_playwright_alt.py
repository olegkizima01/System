import sys
import os
import json
import time

# Add repo root to sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from system_ai.tools.browser import BrowserManager

def test_playwright_new_profile():
    print("Testing Playwright with NEW profile...")
    manager = BrowserManager()
    # Override user_data_dir for test to avoid lock
    manager.user_data_dir = os.path.expanduser("~/.antigravity/browser_session_test")
    os.makedirs(manager.user_data_dir, exist_ok=True)
    
    try:
        page = manager.get_page(headless=False)
        print(f"Browser launched. URL: {page.url}")
        
        print("Navigating to Google...")
        page.goto("https://www.google.com")
        print(f"Title: {page.title()}")
        
        path = os.path.expanduser("~/playwright_test.png")
        page.screenshot(path=path)
        print(f"✅ Playwright success. Screenshot: {path}")
        
        manager.close()
    except Exception as e:
        print(f"❌ Playwright failed: {e}")

if __name__ == "__main__":
    test_playwright_new_profile()
