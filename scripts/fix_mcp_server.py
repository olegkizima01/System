import os
import site
import sys
from pathlib import Path

def fix_mcp_server():
    """Patches mcp-pyautogui-server to fix Image import error."""
    print("🔧 Applying patch to mcp-pyautogui-server...")
    
    # Find site-packages
    site_packages = site.getsitepackages()
    target_file = None
    
    for sp in site_packages:
        possible_path = Path(sp) / "mcp_pyautogui_server" / "server.py"
        if possible_path.exists():
            target_file = possible_path
            break
            
    # Fallback for venv
    if not target_file:
        # Try to guess based on current python executable
        venv_path = Path(sys.executable).parent.parent
        possible_path = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "mcp_pyautogui_server" / "server.py"
        if possible_path.exists():
            target_file = possible_path

    if not target_file:
        print("❌ Could not find mcp_pyautogui_server/server.py")
        return False

    print(f"📄 Found server file at: {target_file}")
    
    # Read content
    try:
        content = target_file.read_text(encoding="utf-8")
        
        # Check if already patched
        if "from fastmcp import FastMCP, Image" not in content and "import io" in content and "base64" in content:
            print("✅ File seems already patched or compatible.")
            return True

        # Valid imports check
        if "from fastmcp import FastMCP, Image" in content:
            print("📝 Removing broken Image import...")
            content = content.replace("from fastmcp import FastMCP, Image", "from fastmcp import FastMCP")
            
        if "import base64" not in content:
            content = content.replace("import pyautogui", "import pyautogui\nimport base64\nimport io")
            
        # Replace screenshot function
        old_signature = "def screenshot() -> Image | Dict[str, str]:"
        if old_signature in content:
             # We need to replace the whole function body or use a regex. 
             # Simpler approach: Rewrite the specific known problematic block if it matches the exact old version.
             pass
        
        # To be robust, let's just write the known good content if we detect it's the standard file
        new_content = """\"\"\"
MCP Pyautogui Server

This is a simple server that allows you to control the mouse and keyboard using MCP.

It is a simple wrapper around the pyautogui library.

It is designed to be used with the FastMCP library.

\"\"\"
from fastmcp import FastMCP
import pyautogui
import base64
import io
from typing import List, Dict, Union, Optional
from pydantic import Field


mcp = FastMCP("MCP Pyautogui Server")


@mcp.tool()
def screenshot() -> Dict[str, str]:
    \"\"\"Take a screenshot of the current screen.\"\"\"
    try:
        buffer = io.BytesIO()
        screenshot = pyautogui.screenshot()
        screenshot.convert("RGB").save(buffer, format="JPEG", quality=60, optimize=True)
        return {
            "status": "success", 
            "format": "jpeg", 
            "data": base64.b64encode(buffer.getvalue()).decode()
        } 
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to take screenshot: {str(e)}"}


@mcp.tool()
def get_screen_size() -> Dict[str, str]:
    \"\"\"Get the size of the screen.\"\"\"
    return {"status": "success", "message": f"Screen size: {pyautogui.size()}"}


@mcp.tool()
def get_mouse_position() -> Dict[str, str]:
    \"\"\"Get the current position of the mouse.\"\"\"
    return {"status": "success", "message": f"Mouse position: {pyautogui.position()}"}


@mcp.tool()
def move_mouse(
    x: int = Field(
        description="The x-coordinate on the screen to move the mouse to"
    ),
    y: int = Field(
        description="The y-coordinate on the screen to move the mouse to"
    )
) -> Dict[str, str]:
    \"\"\"Move the mouse to the given coordinates.\"\"\"
    try:
        pyautogui.moveTo(x, y)
        return {"status": "success", "message": f"Mouse moved to coordinates ({x}, {y})"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse moved to screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move mouse: {str(e)}"}


@mcp.tool()
def click_mouse() -> Dict[str, str]:
    \"\"\"Click the mouse at its current position.\"\"\"
    try:
        pyautogui.click()
        return {"status": "success", "message": "Mouse clicked at current position"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to click mouse: {str(e)}"}


@mcp.tool()
def double_click_mouse() -> Dict[str, str]:
    \"\"\"Double click the mouse at its current position.\"\"\"
    try:
        pyautogui.doubleClick()
        return {"status": "success", "message": "Mouse double-clicked at current position"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to double-click mouse: {str(e)}"}


@mcp.tool()
def hotkey(
    keys: List[str] = Field(
        description="List of key names to press together (e.g. ['command', 'c'] for copy)"
    )
) -> Dict[str, str]:
    \"\"\"Press a sequence of keys simultaneously.\"\"\"
    try:
        pyautogui.hotkey(*keys)
        return {"status": "success", "message": f"Pressed hotkey combination: {' + '.join(keys)}"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to press hotkey: {str(e)}"}


@mcp.tool()
def press_key(
    key: str = Field(
        description="Name of the key to press (e.g. 'enter', 'tab', 'a', etc.)"
    )
) -> Dict[str, str]:
    \"\"\"Press a single key.\"\"\"
    try:
        pyautogui.press(key)
        return {"status": "success", "message": f"Pressed key: {key}"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to press key: {str(e)}"}


@mcp.tool()
def typewrite(
    message: str = Field(
        description="The text string to type out"
    )
) -> Dict[str, str]:
    \"\"\"Type a string of characters.\"\"\"
    try:
        pyautogui.typewrite(message)
        return {"status": "success", "message": f"Typed string of length {len(message)} characters"}
    except pyautogui.FailSafeException:
        return {"status": "error", "message": "Operation cancelled - mouse in screen corner (failsafe)"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to type string: {str(e)}"}


@mcp.tool()
def scroll_up() -> Dict[str, str]:
    \"\"\"Scroll up.\"\"\"
    try:
        pyautogui.scroll(-10)
        return {"status": "success", "message": "Scrolled up"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to scroll up: {str(e)}"}


@mcp.tool()
def scroll_down() -> Dict[str, str]:
    \"\"\"Scroll down.\"\"\"
    try:
        pyautogui.scroll(10)
        return {"status": "success", "message": "Scrolled down"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to scroll down: {str(e)}"}
"""
        target_file.write_text(new_content, encoding="utf-8")
        print("✅ Successfully patched mcp_pyautogui_server/server.py")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch: {e}")
        return False

if __name__ == "__main__":
    fix_mcp_server()
