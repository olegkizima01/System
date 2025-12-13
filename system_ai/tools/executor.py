import os
import subprocess
import time
from typing import Any, Dict, Optional


_DEFAULT_FORBIDDEN_TOKENS = [
    "rm -rf",
    " shutdown",
    "reboot",
    "halt",
    "diskutil erase",
    "mkfs",
    ":(){ :|:& };:",
]


def open_app(name: str) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            ["open", "-a", name],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return {"tool": "open_app", "status": "error", "error": (proc.stderr or "").strip()}
        time.sleep(1.5)
        return {"tool": "open_app", "status": "success", "app": name}
    except Exception as e:
        return {"tool": "open_app", "status": "error", "error": str(e)}


def run_shell(command: str, *, allow: bool, cwd: Optional[str] = None) -> Dict[str, Any]:
    if not allow:
        return {"tool": "run_shell", "status": "error", "error": "Confirmation required"}

    lower_cmd = command.lower()
    for token in _DEFAULT_FORBIDDEN_TOKENS:
        if token in lower_cmd:
            return {"tool": "run_shell", "status": "error", "error": "Command blocked by safety filter", "command": command}

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
        )
        return {
            "tool": "run_shell",
            "status": "success" if proc.returncode == 0 else "error",
            "command": command,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-8000:],
            "stderr": (proc.stderr or "")[-8000:],
        }
    except Exception as e:
        return {"tool": "run_shell", "status": "error", "command": command, "error": str(e)}


def run_applescript(script: str, *, allow: bool) -> Dict[str, Any]:
    if not allow:
        return {"tool": "run_applescript", "status": "error", "error": "Confirmation required"}

    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return {
                "tool": "run_applescript",
                "status": "error",
                "error": (proc.stderr or "").strip(),
                "script_preview": (script[:120] + "...") if len(script) > 120 else script,
            }
        return {"tool": "run_applescript", "status": "success", "output": (proc.stdout or "").strip()}
    except Exception as e:
        return {"tool": "run_applescript", "status": "error", "error": str(e)}
