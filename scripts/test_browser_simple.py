#!/usr/bin/env python3
"""
Simple test for browser support without complex imports
"""
import subprocess
import json
import os

def test_browser_support():
    """Test browser detection and support"""
    
    BROWSER_MAPPING = {
        "chromium": "chromium",
        "chrome": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "mozilla": "firefox",
        "safari": "webkit",
        "webkit": "webkit"
    }
    
    BROWSER_PATHS = {
        "chromium": "/Users/dev/Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
        "webkit": "/Applications/Safari.app/Contents/MacOS/Safari"
    }
    
    print("🔍 Browser Support Test")
    print("=" * 50)
    
    # Test available browsers
    available = []
    for browser, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            available.append(browser)
    
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
        ("unknown browser", "chromium")
    ]
    
    print("\n📋 Browser Name Normalization:")
    for input_name, expected in test_cases:
        # Simple normalization
        input_name = input_name.lower()
        for key, value in BROWSER_MAPPING.items():
            if key in input_name:
                normalized = value
                break
        else:
            normalized = "chromium"
        
        status = "✅" if normalized == expected else "❌"
        print(f"{status} '{input_name}' → '{normalized}' (expected: {expected})")
    
    # Test browser paths
    print("\n📁 Browser Executable Paths:")
    for browser, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            print(f"✅ {browser}: {path}")
        else:
            print(f"❌ {browser}: Not found")
    
    # Test Playwright version
    print("\n📊 Playwright Information:")
    try:
        result = subprocess.run(["playwright", "--version"], capture_output=True, text=True, timeout=5)
        print(f"Playwright version: {result.stdout.strip()}")
    except Exception as e:
        print(f"Playwright check failed: {e}")
    
    # Test Playwright-mcp version
    try:
        result = subprocess.run(["playwright-mcp", "--version"], capture_output=True, text=True, timeout=5)
        print(f"Playwright MCP version: {result.stdout.strip()}")
    except Exception as e:
        print(f"Playwright MCP check failed: {e}")

if __name__ == "__main__":
    test_browser_support()
