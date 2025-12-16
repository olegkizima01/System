"""macOS Native Commands Module

Provides high-level commands for macOS automation that can be executed
through the Trinity system with recording support.
"""

from typing import Dict, Any, Optional, List
from system_ai.tools.macos_native_automation import MacOSNativeAutomation


class MacOSCommandExecutor:
    """High-level command executor for macOS automation"""
    
    def __init__(self, automation: MacOSNativeAutomation):
        self.automation = automation
    
    def open_app(self, app_name: str) -> Dict[str, Any]:
        """Open an application by name
        
        Args:
            app_name: Name of the application (e.g., "ClearVPN", "Safari")
            
        Returns:
            Dict with status and result
        """
        script = f'open -a "{app_name}"'
        result = self.automation.execute_applescript(
            f'do shell script "{script}"',
            record=True
        )
        return {
            "tool": "open_app",
            "status": result["status"],
            "app": app_name,
            "error": result.get("error")
        }
    
    def activate_app(self, app_name: str) -> Dict[str, Any]:
        """Activate (bring to foreground) an application
        
        Args:
            app_name: Name of the application
            
        Returns:
            Dict with status
        """
        script = f"""
tell application "{app_name}"
    activate
end tell
"""
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "activate_app",
            "status": result["status"],
            "app": app_name,
            "error": result.get("error")
        }
    
    def find_and_click_button(self, app_name: str, button_name: str) -> Dict[str, Any]:
        """Find and click a button in an application
        
        Args:
            app_name: Name of the application
            button_name: Name or text of the button
            
        Returns:
            Dict with status
        """
        script = f"""
tell application "{app_name}"
    activate
    tell application "System Events"
        click button "{button_name}" of window 1
    end tell
end tell
"""
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "find_and_click_button",
            "status": result["status"],
            "app": app_name,
            "button": button_name,
            "error": result.get("error")
        }
    
    def find_and_click_menu_item(self, app_name: str, menu_path: List[str]) -> Dict[str, Any]:
        """Find and click a menu item
        
        Args:
            app_name: Name of the application
            menu_path: Path to menu item (e.g., ["File", "Open"])
            
        Returns:
            Dict with status
        """
        if not menu_path:
            return {"tool": "find_and_click_menu_item", "status": "error", "error": "Empty menu path"}
        
        menu_script = " of ".join([f'menu item "{item}"' for item in reversed(menu_path)])
        
        script = f"""
tell application "{app_name}"
    activate
    tell application "System Events"
        click {menu_script}
    end tell
end tell
"""
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "find_and_click_menu_item",
            "status": result["status"],
            "app": app_name,
            "menu_path": menu_path,
            "error": result.get("error")
        }
    
    def get_ui_element_value(self, app_name: str, element_path: str) -> Dict[str, Any]:
        """Get the value of a UI element
        
        Args:
            app_name: Name of the application
            element_path: Path to the element
            
        Returns:
            Dict with status and value
        """
        script = f"""
tell application "{app_name}"
    tell application "System Events"
        value of {element_path}
    end tell
end tell
"""
        result = self.automation.execute_applescript(script, record=False)
        return {
            "tool": "get_ui_element_value",
            "status": result["status"],
            "app": app_name,
            "value": result.get("output") if result["status"] == "success" else None,
            "error": result.get("error")
        }
    
    def list_ui_elements(self, app_name: str, element_type: str = "button") -> Dict[str, Any]:
        """List UI elements of a specific type in an application
        
        Args:
            app_name: Name of the application
            element_type: Type of element (e.g., "button", "text field")
            
        Returns:
            Dict with status and list of elements
        """
        script = f"""
tell application "{app_name}"
    tell application "System Events"
        name of every {element_type} of window 1
    end tell
end tell
"""
        result = self.automation.execute_applescript(script, record=False)
        
        elements = []
        if result["status"] == "success" and result.get("output"):
            elements = [e.strip() for e in result["output"].split(",")]
        
        return {
            "tool": "list_ui_elements",
            "status": result["status"],
            "app": app_name,
            "element_type": element_type,
            "elements": elements,
            "error": result.get("error")
        }
    
    def take_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot
        
        Args:
            output_path: Optional path to save screenshot
            
        Returns:
            Dict with status and path
        """
        if output_path is None:
            output_path = "/tmp/screenshot.png"
        
        script = f'screencapture -x "{output_path}"'
        result = self.automation.execute_applescript(
            f'do shell script "{script}"',
            record=True
        )
        
        return {
            "tool": "take_screenshot",
            "status": result["status"],
            "path": output_path if result["status"] == "success" else None,
            "error": result.get("error")
        }
    
    def get_mouse_position(self) -> Dict[str, Any]:
        """Get current mouse position
        
        Returns:
            Dict with x, y coordinates
        """
        script = """
tell application "System Events"
    get position of mouse
end tell
"""
        result = self.automation.execute_applescript(script, record=False)
        
        if result["status"] == "success":
            try:
                coords = result["output"].strip().split(", ")
                return {
                    "tool": "get_mouse_position",
                    "status": "success",
                    "x": int(coords[0]),
                    "y": int(coords[1])
                }
            except (ValueError, IndexError):
                pass
        
        return {
            "tool": "get_mouse_position",
            "status": "error",
            "error": result.get("error")
        }
    
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Dict with status
        """
        script = f"""
tell application "System Events"
    set mouse location to {{{x}, {y}}}
end tell
"""
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "move_mouse",
            "status": result["status"],
            "x": x,
            "y": y,
            "error": result.get("error")
        }
    
    def click_mouse(self, x: int = None, y: int = None, button: str = "left") -> Dict[str, Any]:
        """Click mouse at coordinates
        
        Args:
            x: X coordinate (uses current position if None)
            y: Y coordinate (uses current position if None)
            button: Mouse button ("left", "right", "middle")
            
        Returns:
            Dict with status
        """
        if x is not None and y is not None:
            self.move_mouse(x, y)
        
        button_map = {"left": 1, "right": 2, "middle": 3}
        button_code = button_map.get(button.lower(), 1)
        
        script = f"""
tell application "System Events"
    click mouse button {button_code}
end tell
"""
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "click_mouse",
            "status": result["status"],
            "button": button,
            "x": x,
            "y": y,
            "error": result.get("error")
        }
    
    def type_text_with_delay(self, text: str, delay_ms: int = 50) -> Dict[str, Any]:
        """Type text with delay between characters
        
        Args:
            text: Text to type
            delay_ms: Delay between characters in milliseconds
            
        Returns:
            Dict with status
        """
        script = f"""
tell application "System Events"
    set delay_value to {delay_ms / 1000}
"""
        for char in text:
            if char == '"':
                script += f'\n    keystroke "\\""\n'
            else:
                script += f'\n    keystroke "{char}"\n'
                script += f'    delay delay_value\n'
        
        script += "end tell"
        
        result = self.automation.execute_applescript(script, record=True)
        return {
            "tool": "type_text_with_delay",
            "status": result["status"],
            "text_length": len(text),
            "delay_ms": delay_ms,
            "error": result.get("error")
        }


def create_command_executor(automation: MacOSNativeAutomation) -> MacOSCommandExecutor:
    """Factory function to create a command executor
    
    Args:
        automation: MacOSNativeAutomation instance
        
    Returns:
        MacOSCommandExecutor instance
    """
    return MacOSCommandExecutor(automation)
