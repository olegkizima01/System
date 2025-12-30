import os
import time
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from system_ai.tools.browser import BrowserManager

def test_launch():
    print("Initializing BrowserManager...")
    manager = BrowserManager.get_instance()
    
    print("Launching page (expecting headless=False)...")
    # This should now default to headless=False based on my previous edit
    page = manager.get_page() 
    
    print(f"Browser launched. Context: {page.context}")
    print("Navigating to example.com...")
    page.goto("https://example.com")
    print(f"Title: {page.title()}")
    
    print("Waiting 5 seconds to simulate user viewing...")
    time.sleep(5)
    
    print("Closing browser...")
    manager.close()
    print("Test complete.")

if __name__ == "__main__":
    try:
        test_launch()
    except Exception as e:
        print(f"ERROR: {e}")
