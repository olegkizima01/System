import logging
from typing import Dict, Any
from system_ai.tools.executor import run_applescript

logger = logging.getLogger(__name__)

def send_to_windsurf(message: str) -> Dict[str, Any]:
    """
    Focuses Windsurf and types the message into the active window/chat.
    Uses AppleScript to simulate keystrokes.
    WARNING: Requires Accessibility permissions.
    """
    # AppleScript to focus Windsurf and paste content
    # We use clipboard to avoid slow typing of long messages
    script = f"""
    set msg to {repr(message)}
    tell application "System Events"
        set frontmost of application process "Windsurf" to true
        delay 0.5
        keystroke "l" using {{command down}} -- Focus chat/composer usually Cmd+L
        delay 0.2
        set the clipboard to msg
        delay 0.1
        keystroke "v" using {{command down}} -- Paste
        delay 0.5
        keystroke return -- Send
    end tell
    """
    
    # We sanitize the script execution
    try:
        result = run_applescript(script, allow=True)
        if result.get("status") == "success":
             return {"tool": "send_to_windsurf", "status": "success", "message_sent": True}
        return {"tool": "send_to_windsurf", "status": "error", "error": result.get("error")}
    except Exception as e:
        return {"tool": "send_to_windsurf", "status": "error", "error": str(e)}

def open_file_in_windsurf(path: str, line: int = 0) -> Dict[str, Any]:
    """Opens a specific file in Windsurf via 'code' CLI alias or 'open' command."""
    import subprocess
    import shutil
    
    # Try using 'windsurf' command if in path, or just 'open -a Windsurf'
    tool_path = shutil.which("windsurf")
    
    try:
        if tool_path:
            cmd = [tool_path, path]
            if line > 0:
                cmd.extend(["--goto", f"{path}:{line}"])
            subprocess.run(cmd, check=True)
        else:
            # Fallback to generic open
            subprocess.run(["open", "-a", "Windsurf", path], check=True)
            
        return {"tool": "open_file_in_windsurf", "status": "success", "path": path}
    except Exception as e:
         return {"tool": "open_file_in_windsurf", "status": "error", "error": str(e)}
