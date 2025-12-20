import sys
import os
import time

# Add repo root to sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from system_ai.tools.screenshot import take_screenshot

def test_mss():
    print("Testing mss (via take_screenshot)...")
    path = os.path.expanduser("~/mss_test.png")
    
    # Try to take a full-screen screenshot
    res = take_screenshot()
    print(f"Result: {res}")
    
    # take_screenshot usually returns a dict if successful
    if isinstance(res, dict) and res.get("status") == "success":
        print(f"✅ mss success. Image captured.")
    else:
        print(f"❌ mss failed or returned unexpected result: {res}")

if __name__ == "__main__":
    test_mss()
