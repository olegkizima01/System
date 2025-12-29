"""Desktop Tools Module

Provides tools for inspecting windows, monitors, managing clipboard state, and setting wallpapers using Quartz and AppKit.
"""

import Quartz
import AppKit
import subprocess
import os
from typing import Dict, Any, List, Optional

def get_monitors_info() -> List[Dict[str, Any]]:
    """Get information about connected displays
    
    Returns:
        List of monitor dictionaries with ID, resolution, and position.
    """
    monitors = []
    # Get active display list
    (err, ids, count) = Quartz.CGGetActiveDisplayList(32, None, None)
    if err != 0:
        return [{"error": f"CGGetActiveDisplayList failed with error {err}"}]
        
    ids = list(ids) # tuple to list
    
    for display_id in ids:
        bounds = Quartz.CGDisplayBounds(display_id)
        is_main = Quartz.CGDisplayIsMain(display_id)
        
        monitors.append({
            "id": display_id,
            "is_main": bool(is_main),
            "width": int(bounds.size.width),
            "height": int(bounds.size.height),
            "x": int(bounds.origin.x),
            "y": int(bounds.origin.y),
        })
        
    return monitors

def get_open_windows(on_screen_only: bool = True) -> List[Dict[str, Any]]:
    """Get list of open windows
    
    Args:
        on_screen_only: If True, only returns windows that are currently on screen
        
    Returns:
        List of window info dictionaries
    """
    options = Quartz.kCGWindowListOptionOnScreenOnly if on_screen_only else Quartz.kCGWindowListOptionAll
    options |= Quartz.kCGWindowListExcludeDesktopElements
    
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    
    results = []
    for w in window_list:
        # Filter out system windows or tiny overlays if needed, keeping it raw for now but cleaner
        layer = w.get('kCGWindowLayer', 0)
        if layer != 0: # Usually layer 0 is normal apps
            continue
            
        owner_name = w.get('kCGWindowOwnerName', '')
        name = w.get('kCGWindowName', '')
        bounds = w.get('kCGWindowBounds', {})
        pid = w.get('kCGWindowOwnerPID', 0)
        
        results.append({
            "app": owner_name,
            "title": name,
            "pid": pid,
            "x": int(bounds.get('X', 0)),
            "y": int(bounds.get('Y', 0)),
            "width": int(bounds.get('Width', 0)),
            "height": int(bounds.get('Height', 0)),
            "id": w.get('kCGWindowNumber', 0)
        })
        
    return results

def get_clipboard() -> Dict[str, Any]:
    """Get text content from clipboard
    
    Returns:
        Dict with status and content
    """
    try:
        pb = AppKit.NSPasteboard.generalPasteboard()
        content = pb.stringForType_(AppKit.NSPasteboardTypeString)
        return {
            "tool": "get_clipboard",
            "status": "success",
            "content": str(content) if content else ""
        }
    except Exception as e:
        return {
            "tool": "get_clipboard",
            "status": "error",
            "error": str(e)
        }

def set_clipboard(text: str) -> Dict[str, Any]:
    """Set text content to clipboard
    
    Args:
        text: Content to copy
        
    Returns:
        Dict with status
    """
    try:
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, AppKit.NSPasteboardTypeString)
        return {
            "tool": "set_clipboard",
            "status": "success",
            "length": len(text)
        }
    except Exception as e:
        return {
            "tool": "set_clipboard",
            "status": "error",
            "error": str(e)
        }


def set_wallpaper(image_path: str, monitor_id: Optional[int] = None) -> Dict[str, Any]:
    """Set wallpaper for a specific monitor or all monitors
    
    Args:
        image_path: Path to the image file
        monitor_id: Optional monitor ID (if None, sets for all monitors)
        
    Returns:
        Dict with status and result
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                "tool": "set_wallpaper",
                "status": "error",
                "error": f"Image file not found: {image_path}"
            }
        
        # For macOS, we use AppleScript to set wallpaper
        # Note: AppleScript uses 1-based indexing for desktops, but we need to handle
        # the case where monitor_id might not match AppleScript's desktop numbering
        if monitor_id is None:
            # Set for all monitors
            script = f'''
            tell application "System Events"
                tell every desktop
                    set picture to "{image_path}"
                end tell
            end tell
            '''
        else:
            # For specific monitor, try the direct ID first, then fallback to desktop 1 if it fails
            # AppleScript desktop numbering might not match Quartz display IDs
            script = f'''
            tell application "System Events"
                try
                    tell desktop {monitor_id}
                        set picture to "{image_path}"
                    end tell
                on error
                    -- Fallback to desktop 1 (main monitor) if specific desktop not found
                    try
                        tell desktop 1
                            set picture to "{image_path}"
                        end tell
                    on error errMsg
                        error "Failed to set wallpaper for monitor " & {monitor_id} & ": " & errMsg
                    end try
                end try
            end tell
            '''
        
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                "tool": "set_wallpaper",
                "status": "success",
                "image_path": image_path,
                "monitor_id": monitor_id,
                "message": "Wallpaper set successfully"
            }
        else:
            return {
                "tool": "set_wallpaper",
                "status": "error",
                "error": result.stderr.strip() or "Unknown error setting wallpaper",
                "returncode": result.returncode
            }
            
    except Exception as e:
        return {
            "tool": "set_wallpaper",
            "status": "error",
            "error": str(e),
            "image_path": image_path,
            "monitor_id": monitor_id
        }


def get_current_wallpaper(monitor_id: Optional[int] = None) -> Dict[str, Any]:
    """Get current wallpaper path for a specific monitor or main monitor
    
    Args:
        monitor_id: Optional monitor ID (if None, gets main monitor wallpaper)
        
    Returns:
        Dict with status and wallpaper path
    """
    try:
        if monitor_id is None:
            # Get main monitor wallpaper
            script = '''
            tell application "System Events"
                get picture of desktop 1
            end tell
            '''
        else:
            # Get specific monitor wallpaper
            script = f'''
            tell application "System Events"
                get picture of desktop {monitor_id}
            end tell
            '''
        
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            wallpaper_path = result.stdout.strip()
            if wallpaper_path and wallpaper_path != "missing value":
                return {
                    "tool": "get_current_wallpaper",
                    "status": "success",
                    "wallpaper_path": wallpaper_path,
                    "monitor_id": monitor_id
                }
            else:
                return {
                    "tool": "get_current_wallpaper",
                    "status": "success",
                    "wallpaper_path": None,
                    "monitor_id": monitor_id,
                    "message": "No wallpaper set or default wallpaper"
                }
        else:
            return {
                "tool": "get_current_wallpaper",
                "status": "error",
                "error": result.stderr.strip() or "Unknown error getting wallpaper",
                "returncode": result.returncode
            }
            
    except Exception as e:
        return {
            "tool": "get_current_wallpaper",
            "status": "error",
            "error": str(e),
            "monitor_id": monitor_id
        }
