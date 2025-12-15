import time
from typing import Dict, Any, Optional
import subprocess

# Try to import pyautogui, but don't fail if missing (use fallback or error)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # Fail-safe
    pyautogui.FAILSAFE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


def move_mouse(x: int, y: int) -> Dict[str, Any]:
    if not PYAUTOGUI_AVAILABLE:
        return {"tool": "move_mouse", "status": "error", "error": "pyautogui not installed"}
    try:
        pyautogui.moveTo(x=x, y=y)
        return {"tool": "move_mouse", "status": "success", "x": x, "y": y}
    except Exception as e:
        return {"tool": "move_mouse", "status": "error", "error": str(e)}


def click_mouse(button: str = "left", x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
    if not PYAUTOGUI_AVAILABLE:
        return {"tool": "click_mouse", "status": "error", "error": "pyautogui not installed"}

    btn = str(button or "left").strip().lower()
    if btn not in {"left", "right", "double"}:
        return {"tool": "click_mouse", "status": "error", "error": "Invalid button"}

    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x=x, y=y)

        if btn == "double":
            pyautogui.click(button="left", clicks=2)
        else:
            pyautogui.click(button=btn)

        return {"tool": "click_mouse", "status": "success", "button": btn, "x": x, "y": y}
    except Exception as e:
        return {"tool": "click_mouse", "status": "error", "error": str(e)}

def click(x: int, y: int) -> Dict[str, Any]:
    """Clicks at the specified coordinates (x, y)."""
    if not PYAUTOGUI_AVAILABLE:
        # Fallback to cliclick if installed, or AppleScript (limited)
        # For now, return error if no pyautogui
        return {"tool": "click", "status": "error", "error": "pyautogui not installed"}
    
    try:
        pyautogui.click(x=x, y=y)
        return {"tool": "click", "status": "success", "x": x, "y": y}
    except Exception as e:
        return {"tool": "click", "status": "error", "error": str(e)}

def type_text(text: str) -> Dict[str, Any]:
    """Types text using keyboard simulation."""
    if not text:
        return {"tool": "type_text", "status": "error", "error": "No text provided"}

    # Use AppleScript for typing as it's often more reliable for large chunks on macOS 
    # and handles keyboard layouts slightly better for standard English
    safe_text = text.replace('"', '\\"').replace('\\', '\\\\')
    script = f'tell application "System Events" to keystroke "{safe_text}"'
    
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if proc.returncode == 0:
            return {"tool": "type_text", "status": "success", "text_length": len(text)}
        
        # Fallback to pyautogui if AppleScript fails
        if PYAUTOGUI_AVAILABLE:
            pyautogui.write(text)
            return {"tool": "type_text", "status": "success", "text_length": len(text), "method": "pyautogui"}
            
        return {"tool": "type_text", "status": "error", "error": proc.stderr}
    except Exception as e:
        return {"tool": "type_text", "status": "error", "error": str(e)}

def press_key(key: str, command: bool = False, shift: bool = False, option: bool = False, control: bool = False) -> Dict[str, Any]:
    """Presses a specific key with optional modifiers."""
    modifiers = []
    if command: modifiers.append("command down")
    if shift: modifiers.append("shift down")
    if option: modifiers.append("option down")
    if control: modifiers.append("control down")
    
    mod_str = ""
    if modifiers:
        mod_str = " using {" + ", ".join(modifiers) + "}"
        
    script = f'tell application "System Events" to keystroke "{key}"{mod_str}'
    
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if proc.returncode == 0:
            return {"tool": "press_key", "status": "success", "key": key, "modifiers": modifiers}
        return {"tool": "press_key", "status": "error", "error": proc.stderr}
    except Exception as e:
        return {"tool": "press_key", "status": "error", "error": str(e)}
