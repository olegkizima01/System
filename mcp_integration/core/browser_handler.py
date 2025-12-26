"""
Browser Handler Module
Supports multiple browsers: Chromium, Chrome, Firefox, Safari (WebKit)
"""
import subprocess
import json
import os
from typing import Dict, Any, Optional, List

class BrowserHandler:
    """Handles browser automation with multi-browser support"""
    
    BROWSER_MAPPING = {
        "chromium": "chromium",
        "chrome": "chrome",
        "google chrome": "chrome",
        "google-chrome": "chrome",
        "firefox": "firefox",
        "mozilla": "firefox",
        "mozilla firefox": "firefox",
        "ff": "firefox",
        "safari": "webkit",
        "safari browser": "webkit",
        "webkit": "webkit"
    }
    
    BROWSER_PATHS = {
        "chromium": "/Users/dev/Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
        "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
        "webkit": "/Applications/Safari.app/Contents/MacOS/Safari"
    }
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from MCP config"""
        try:
            config_path = "/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json"
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            return {"mcpServers": {}}
    
    def normalize_browser_name(self, browser_name: str) -> str:
        """Normalize browser name to Playwright format"""
        browser_name = browser_name.lower()
        for key, value in self.BROWSER_MAPPING.items():
            if key in browser_name:
                return value
        return "chromium"  # default
    
    def get_browser_path(self, browser_name: str) -> Optional[str]:
        """Get path to browser executable"""
        browser_name = self.normalize_browser_name(browser_name)
        path = self.BROWSER_PATHS.get(browser_name)
        return path if path and os.path.exists(path) else None
    
    def get_available_browsers(self) -> List[str]:
        """Get list of available browsers"""
        available = []
        for browser, path in self.BROWSER_PATHS.items():
            if os.path.exists(path):
                available.append(browser)
        return available
    
    def start_playwright_server(self, browser_name: str = "chromium") -> subprocess.Popen:
        """Start Playwright MCP server with specific browser"""
        browser_name = self.normalize_browser_name(browser_name)
        
        # Build command
        command = ["playwright-mcp", "--browser", browser_name, "--allowed-origins", "*"]
        
        # Add executable path if available
        browser_path = self.get_browser_path(browser_name)
        if browser_path:
            command.extend(["--executable-path", browser_path])
        
        command.extend([
            "--user-data-dir", "/tmp/mcp_playwright_session",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ])
        
        print(f"🚀 Starting Playwright server with {browser_name} browser")
        print(f"Command: {' '.join(command)}")
        
        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return proc
        except Exception as e:
            raise RuntimeError(f"Failed to start Playwright: {e}")
    
    def execute_browser_task(self, task: str, browser_name: str = "chromium") -> Dict[str, Any]:
        """Execute browser task with specific browser"""
        try:
            # Normalize browser name
            browser_name = self.normalize_browser_name(browser_name)
            
            # Start the browser server
            proc = self.start_playwright_server(browser_name)
            
            return {
                "status": "success",
                "browser": browser_name,
                "task": task,
                "message": f"Task '{task}' started in {browser_name}",
                "available_browsers": self.get_available_browsers()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "browser": browser_name,
                "task": task
            }
