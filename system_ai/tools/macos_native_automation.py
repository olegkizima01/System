"""macOS Native Automation Module

Provides native AppleScript and shell-based automation for macOS with recording support.
Integrates with the Recorder to capture automation actions.
"""

import subprocess
import json
import time
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AutomationAction:
    """Represents a single automation action"""
    action_type: str
    target: str
    parameters: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MacOSNativeAutomation:
    """Native macOS automation executor with recording support"""
    
    def __init__(self, recorder_service=None):
        self.recorder = recorder_service
        self.actions_log: List[AutomationAction] = []
    
    def execute_applescript(self, script: str, record: bool = True) -> Dict[str, Any]:
        """Execute AppleScript with optional recording
        
        Args:
            script: AppleScript code to execute
            record: Whether to record this action
            
        Returns:
            Dict with status, output, and error info
        """
        action = AutomationAction(
            action_type="applescript",
            target="system_events",
            parameters={"script": script[:200]}
        )
        
        try:
            result = subprocess.run(
                ["/usr/bin/osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = {
                "tool": "execute_applescript",
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout.strip(),
                "error": result.stderr.strip() if result.returncode != 0 else None,
                "returncode": result.returncode,
            }
            
            if record and self.recorder:
                self._record_action(action, output)
            
            self.actions_log.append(action)
            return output
            
        except subprocess.TimeoutExpired:
            output = {
                "tool": "execute_applescript",
                "status": "error",
                "error": "Script execution timeout (10s)",
                "returncode": -1,
            }
            if record and self.recorder:
                self._record_action(action, output)
            return output
        except Exception as e:
            output = {
                "tool": "execute_applescript",
                "status": "error",
                "error": str(e),
                "returncode": -1,
            }
            if record and self.recorder:
                self._record_action(action, output)
            return output
    
    def click_ui_element(self, app_name: str, ui_path: str, record: bool = True) -> Dict[str, Any]:
        """Click a UI element using AppleScript
        
        Args:
            app_name: Name of the application (e.g., "ClearVPN")
            ui_path: Path to UI element (e.g., "window 1 > button 1")
            record: Whether to record this action
            
        Returns:
            Dict with status and result
        """
        script = f"""
tell application "{app_name}"
    activate
    tell application "System Events"
        click {ui_path}
    end tell
end tell
"""
        action = AutomationAction(
            action_type="click_ui",
            target=app_name,
            parameters={"ui_path": ui_path}
        )
        
        result = self.execute_applescript(script, record=False)
        
        if record and self.recorder:
            self._record_action(action, result)
        
        self.actions_log.append(action)
        return result
    
    def type_text(self, text: str, record: bool = True) -> Dict[str, Any]:
        """Type text using keyboard simulation
        
        Args:
            text: Text to type
            record: Whether to record this action
            
        Returns:
            Dict with status
        """
        script = f"""
tell application "System Events"
    keystroke "{text}"
end tell
"""
        action = AutomationAction(
            action_type="type_text",
            target="keyboard",
            parameters={"text": text[:100]}
        )
        
        result = self.execute_applescript(script, record=False)
        
        if record and self.recorder:
            self._record_action(action, result)
        
        self.actions_log.append(action)
        return result
    
    def press_key(self, key: str, modifiers: List[str] = None, record: bool = True) -> Dict[str, Any]:
        """Press a keyboard key with optional modifiers
        
        Args:
            key: Key to press (e.g., "return", "space", "tab")
            modifiers: List of modifiers (e.g., ["shift", "command"])
            record: Whether to record this action
            
        Returns:
            Dict with status
        """
        modifiers = modifiers or []
        modifier_str = " ".join(modifiers) + " " if modifiers else ""
        
        script = f"""
tell application "System Events"
    key code (key code "{key}") using {{{modifier_str}}}
end tell
"""
        action = AutomationAction(
            action_type="press_key",
            target="keyboard",
            parameters={"key": key, "modifiers": modifiers}
        )
        
        result = self.execute_applescript(script, record=False)
        
        if record and self.recorder:
            self._record_action(action, result)
        
        self.actions_log.append(action)
        return result
    
    def get_frontmost_app(self) -> Dict[str, Any]:
        """Get the name of the frontmost application
        
        Returns:
            Dict with app name
        """
        script = """
tell application "System Events"
    name of first application process whose frontmost is true
end tell
"""
        result = self.execute_applescript(script, record=False)
        
        if result["status"] == "success":
            return {
                "tool": "get_frontmost_app",
                "status": "success",
                "app_name": result["output"]
            }
        return {
            "tool": "get_frontmost_app",
            "status": "error",
            "error": result.get("error")
        }
    
    def wait(self, seconds: float, record: bool = True) -> Dict[str, Any]:
        """Wait for specified duration
        
        Args:
            seconds: Duration to wait
            record: Whether to record this action
            
        Returns:
            Dict with status
        """
        action = AutomationAction(
            action_type="wait",
            target="system",
            parameters={"duration": seconds}
        )
        
        time.sleep(seconds)
        
        output = {
            "tool": "wait",
            "status": "success",
            "waited_seconds": seconds
        }
        
        if record and self.recorder:
            self._record_action(action, output)
        
        self.actions_log.append(action)
        return output
    
    def _record_action(self, action: AutomationAction, result: Dict[str, Any]) -> None:
        """Record an automation action to the recorder service
        
        Args:
            action: The automation action
            result: The result of executing the action
        """
        if not self.recorder:
            return
        
        try:
            event = {
                "type": "automation",
                "ts": action.timestamp,
                "action_type": action.action_type,
                "target": action.target,
                "parameters": action.parameters,
                "result": result,
            }
            
            if hasattr(self.recorder, "_enqueue"):
                self.recorder._enqueue(event)
        except Exception:
            pass
    
    def get_actions_log(self) -> List[Dict[str, Any]]:
        """Get log of all recorded actions
        
        Returns:
            List of action dictionaries
        """
        return [
            {
                "action_type": a.action_type,
                "target": a.target,
                "parameters": a.parameters,
                "timestamp": a.timestamp,
            }
            for a in self.actions_log
        ]
    
    def clear_actions_log(self) -> None:
        """Clear the actions log"""
        self.actions_log.clear()


def create_automation_executor(recorder_service=None) -> MacOSNativeAutomation:
    """Factory function to create an automation executor
    
    Args:
        recorder_service: Optional recorder service for recording actions
        
    Returns:
        MacOSNativeAutomation instance
    """
    return MacOSNativeAutomation(recorder_service)
