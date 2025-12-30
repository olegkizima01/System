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
    
    # Common macOS browser paths
    COMMON_PATHS = {
        "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        "webkit": ["/Applications/Safari.app/Contents/MacOS/Safari"],
        "chromium": []  # Chromium mostly managed by playwright
    }

    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from MCP config"""
        try:
            config_path = os.path.expanduser("~/.agent/mcp_config.json")
            # Fallback to repo path if generic not found
            if not os.path.exists(config_path):
                 config_path = "/Users/dev/Documents/GitHub/System/mcp_integration/config/mcp_config.json"
            
            if os.path.exists(config_path):
                with open(config_path) as f:
                    return json.load(f)
            return {"mcpServers": {}}
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
        """Get path to browser executable using dynamic detection"""
        browser_name = self.normalize_browser_name(browser_name)
        
        # 1. Check environment variable override
        env_var = f"BROWSER_PATH_{browser_name.upper()}"
        if os.environ.get(env_var):
            return os.environ[env_var]

        # 2. Check common paths
        for path in self.COMMON_PATHS.get(browser_name, []):
            if os.path.exists(path):
                return path
        
        # 3. Try shutil.which for command line tools
        import shutil
        if shutil.which(browser_name):
            return shutil.which(browser_name)

        return None
    
    def get_available_browsers(self) -> List[str]:
        """Get list of available browsers"""
        available = []
        for browser in self.COMMON_PATHS.keys():
            if self.get_browser_path(browser):
                available.append(browser)
        # Chromium is usually available via playwright internal
        if "chromium" not in available:
             available.append("chromium")
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
