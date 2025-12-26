#!/usr/bin/env python3
"""
Test script for multi-browser support
"""
import sys
import os
sys.path.insert(0, '/Users/dev/Documents/GitHub/System')

from mcp_integration.core.browser_handler import BrowserHandler

def test_browser_support():
    """Test browser detection and support"""
    handler = BrowserHandler()
    
    print("🔍 Browser Support Test")
    print("=" * 50)
    
    # Test available browsers
    available = handler.get_available_browsers()
    print(f"✅ Available browsers: {', '.join(available)}")
    
    # Test browser normalization
    test_cases = [
        ("chromium", "chromium"),
        ("chrome", "chrome"),
        ("google chrome", "chrome"),
        ("firefox", "firefox"),
        ("mozilla", "firefox"),
        ("safari", "webkit"),
        ("safari browser", "webkit"),
        ("unknown browser", "chromium")  # default
    ]
    
    print("\n📋 Browser Name Normalization:")
    for input_name, expected in test_cases:
        normalized = handler.normalize_browser_name(input_name)
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{input_name}' → '{normalized}' (expected: {expected})")
    
    # Test browser paths
    print("\n📁 Browser Executable Paths:")
    for browser in ["chromium", "chrome", "firefox", "webkit"]:
        path = handler.get_browser_path(browser)
        if path:
            print(f"✅ {browser}: {path}")
        else:
            print(f"❌ {browser}: Not found")
    
    # Test server startup (dry run)
    print("\n🚀 Testing Playwright Server Startup:")
    for browser in ["chromium", "chrome"]:
        try:
            print(f"\nTesting {browser}...")
            result = handler.execute_browser_task(f"Test task", browser)
            print(f"Status: {result['status']}")
            if result['status'] == 'success':
                print(f"Message: {result['message']}")
        except Exception as e:
            print(f"Error with {browser}: {e}")

if __name__ == "__main__":
    test_browser_support()
