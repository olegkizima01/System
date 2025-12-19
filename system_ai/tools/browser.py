import os
import time
import json
from typing import Optional, Dict, List, Any
from playwright.sync_api import sync_playwright, Browser, Page

class BrowserManager:
    _instance = None
    
    def __init__(self):
        self.pw = None
        self.browser = None
        self.page: Optional[Page] = None
        self._last_headless = None
        self.user_data_dir = os.path.expanduser("~/.antigravity/browser_session")
        os.makedirs(self.user_data_dir, exist_ok=True)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_page(self, headless: bool = True) -> Page:
        # If already running but in different headless mode, restart
        if self.pw and self.browser and self._last_headless != headless:
            self.close()

        if not self.browser:
            try:
                if not self.pw:
                    self.pw = sync_playwright().start()
                
                self._last_headless = headless
                
                # Try to connect to existing Chrome via CDP first
                cdp_url = os.environ.get("CHROME_CDP_URL", "http://127.0.0.1:9222")
                try:
                    self.browser = self.pw.chromium.connect_over_cdp(cdp_url)
                    # Get the first page or create one
                    pages = self.browser.contexts[0].pages if self.browser.contexts else []
                    if pages:
                        self.page = pages[0]
                    else:
                        self.page = self.browser.contexts[0].new_page() if self.browser.contexts else self.browser.new_context().new_page()
                    self._connected_via_cdp = True
                    return self.page
                except Exception:
                    # CDP connection failed, fall back to launching new browser
                    self._connected_via_cdp = False
                
                # Chromium args
                args = ["--disable-blink-features=AutomationControlled"]
                # Only add sandbox flags if not on macOS (to avoid warning banner)
                import platform
                if platform.system() != "Darwin":
                    args.extend(["--no-sandbox", "--disable-setuid-sandbox"])
                
                self.browser = self.pw.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=headless,
                    args=args,
                    viewport={"width": 1280, "height": 720}
                )
                self.page = self.browser.pages[0]
            except Exception:
                # If launch fails, ensure we cleanup to allow fresh retry
                self.close()
                raise

        return self.page


    def close(self):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()
        self.pw = None
        self.browser = None
        self.page = None

def browser_open_url(url: str, headless: bool = True) -> str:
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page(headless=headless)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2) # Give page some time to settle
        
        content = page.content().lower()
        # Refined detection: avoid false positives on 'robot' or 'sorry' in footer/about pages
        captcha_markers = [
            "g-recaptcha", "hcaptcha", "cloudflare-turnstile",
            "verify you are human", "solving this captcha",
            "unusual traffic from your computer network",
            "check if you are a robot"
        ]
        has_captcha = any(marker in content for marker in captcha_markers)
        
        # If very suspicious but not explicitly matched, log it but don't force 'uncertain' automatically
        if not has_captcha and ("sorry" in content and "unusual traffic" in content):
            has_captcha = True
        
        return json.dumps({
            "status": "success",
            "url": page.url,
            "title": page.title(),
            "has_captcha": has_captcha
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_click_element(selector: str) -> str:
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        page.click(selector, timeout=5000)
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_type_text(selector: str, text: str, press_enter: bool = False) -> str:
    try:
        # Smart Selector Mapping: Google changed input[name="q"] to textarea[name="q"]
        if selector == "input[name='q']" or selector == 'input[name="q"]':
            selector = 'textarea[name="q"]'
            
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        page.fill(selector, text, timeout=10000)
        if press_enter:
            page.press(selector, "Enter")
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_press_key(key: str) -> str:
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        page.keyboard.press(key)
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_execute_script(script: str) -> str:
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        result = page.evaluate(script)
        return json.dumps({"status": "success", "result": str(result)})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_ensure_ready() -> str:
    try:
        manager = BrowserManager.get_instance()
        manager.get_page()
        return json.dumps({"status": "success", "message": "Browser is ready"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_screenshot(path: Optional[str] = None) -> str:
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        if not path:
            # Prioritize project data folder if it exists
            project_dir = os.path.abspath(".agent/workflows/data/screenshots")
            if os.path.isdir(project_dir):
                output_dir = project_dir
            else:
                output_dir = os.path.expanduser("~/.antigravity/vision_cache")
            
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f"browser_{int(time.time())}.png")
        page.screenshot(path=path)
        return json.dumps({"status": "success", "path": path})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_get_content() -> str:
    try:
        manager = BrowserManager.get_instance()
        # Use existing session's headless mode if available
        headless_mode = manager._last_headless if manager._last_headless is not None else True
        page = manager.get_page(headless=headless_mode)
        
        # Extract visible text instead of raw HTML to reduce noise and fit more useful info
        text_content = page.inner_text("body")
        
        return json.dumps({
            "status": "success",
            "content": text_content[:15000],  # Increased limit and switched to text
            "url": page.url,
            "title": page.title()
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_snapshot() -> str:
    """Capture accessibility snapshot of the current page.
    Note: Full A11y tree snapshot was removed in v1.50+. 
    This tool now returns a simplified view with content, url, and title.
    """
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        content = page.content()
        
        content_lower = content.lower()
        # Basic CAPTCHA check
        captcha_markers = [
            "g-recaptcha", "hcaptcha", "cloudflare-turnstile",
            "verify you are human", "solving this captcha",
            "unusual traffic from your computer network",
            "check if you are a robot"
        ]
        has_captcha = any(marker in content_lower for marker in captcha_markers)
        if not has_captcha and ("sorry" in content_lower and "unusual traffic" in content_lower):
            has_captcha = True
        
        return json.dumps({
            "status": "success",
            "url": page.url,
            "title": page.title(),
            "has_captcha": has_captcha,
            "content_preview": content[:30000] # Return much more content for verification
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_navigate(url: str, headless: bool = True) -> str:
    """Alias for browser_open_url."""
    return browser_open_url(url, headless=headless)

def browser_get_links() -> str:
    """Extract all clickable links from the current page."""
    try:
        manager = BrowserManager.get_instance()
        page = manager.get_page()
        
        links = page.evaluate("""
            () => {
                const results = [];
                const anchors = document.querySelectorAll('a[href]');
                anchors.forEach(a => {
                    const text = a.innerText.trim();
                    const href = a.href;
                    if (text && href && !href.startsWith('javascript:')) {
                        results.push({text, href});
                    }
                });
                return results;
            }
        """)
        
        return json.dumps({
            "status": "success",
            "links": links[:50] # Top 50 links
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def browser_close() -> str:
    try:
        BrowserManager.get_instance().close()
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
