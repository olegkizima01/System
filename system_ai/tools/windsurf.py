import os
import subprocess
from typing import Any, Dict, Optional


def _truthy_env(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _blocked_by_vibe(tool: str) -> Dict[str, Any]:
    return {
        "tool": tool,
        "status": "blocked_by_doctor_vibe",
        "error": "Blocked: TRINITY_DEV_BY_VIBE is enabled",
    }


def is_windsurf_running() -> Dict[str, Any]:
    if _truthy_env("TRINITY_DEV_BY_VIBE"):
        return _blocked_by_vibe("is_windsurf_running")

    try:
        try:
            import psutil  # type: ignore

            for p in psutil.process_iter(["name", "cmdline"]):
                try:
                    name = str((p.info or {}).get("name") or "")
                    cmdline = " ".join((p.info or {}).get("cmdline") or [])
                    hay = (name + " " + cmdline).lower()
                    if "windsurf" in hay:
                        return {"tool": "is_windsurf_running", "status": "success", "running": True}
                except Exception:
                    continue
            return {"tool": "is_windsurf_running", "status": "success", "running": False}
        except Exception:
            proc = subprocess.run(["pgrep", "-f", "Windsurf"], capture_output=True, text=True)
            running = proc.returncode == 0 and bool((proc.stdout or "").strip())
            return {"tool": "is_windsurf_running", "status": "success", "running": bool(running)}
    except Exception as e:
        return {"tool": "is_windsurf_running", "status": "error", "error": str(e)}


def open_project_in_windsurf(path: str, new_window: bool = False) -> Dict[str, Any]:
    if _truthy_env("TRINITY_DEV_BY_VIBE"):
        return _blocked_by_vibe("open_project_in_windsurf")

    p = os.path.abspath(os.path.expanduser(str(path or "").strip()))
    if not p or not os.path.isdir(p):
        return {"tool": "open_project_in_windsurf", "status": "error", "error": f"Path is not a directory: {p}", "path": p}

    try:
        cmd = ["open"]
        if new_window:
            cmd += ["-n"]
        cmd += ["-a", "Windsurf", p]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "tool": "open_project_in_windsurf",
            "status": "success" if proc.returncode == 0 else "error",
            "path": p,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
        }
    except Exception as e:
        return {"tool": "open_project_in_windsurf", "status": "error", "error": str(e), "path": p}


def open_file_in_windsurf(path: str, line: Optional[int] = None) -> Dict[str, Any]:
    if _truthy_env("TRINITY_DEV_BY_VIBE"):
        return _blocked_by_vibe("open_file_in_windsurf")

    p = os.path.abspath(os.path.expanduser(str(path or "").strip()))
    if not p or not os.path.exists(p):
        return {"tool": "open_file_in_windsurf", "status": "error", "error": f"File not found: {p}", "path": p, "line": line}

    try:
        cmd = ["open", "-a", "Windsurf", p]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "tool": "open_file_in_windsurf",
            "status": "success" if proc.returncode == 0 else "error",
            "path": p,
            "line": int(line) if line is not None else None,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
        }
    except Exception as e:
        return {"tool": "open_file_in_windsurf", "status": "error", "error": str(e), "path": p, "line": line}


def get_windsurf_current_project_path() -> Dict[str, Any]:
    if _truthy_env("TRINITY_DEV_BY_VIBE"):
        return _blocked_by_vibe("get_windsurf_current_project_path")

    return {
        "tool": "get_windsurf_current_project_path",
        "status": "error",
        "error": "Not available: current project path discovery is not implemented in this build",
    }


def send_to_windsurf(message: str) -> Dict[str, Any]:
    if _truthy_env("TRINITY_DEV_BY_VIBE"):
        return _blocked_by_vibe("send_to_windsurf")

    msg = str(message or "").strip()
    if not msg:
        return {"tool": "send_to_windsurf", "status": "error", "error": "Empty message"}

    return {
        "tool": "send_to_windsurf",
        "status": "error",
        "error": "Not available: no supported automation bridge to Windsurf Chat in this build",
    }
