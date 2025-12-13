import os
import time
from typing import Any, Dict, Optional


def smart_capture(target_app: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Thin wrapper around dop_materials implementation if present; fallback to screencapture full screen."""
    try:
        from dop_materials.super_rag_agent.screenshot_utils import smart_capture as legacy_smart_capture  # type: ignore

        return legacy_smart_capture(target_app=target_app, output_path=output_path)
    except Exception:
        pass

    if not output_path:
        output_path = os.path.join(os.path.expanduser("~/Desktop"), f"screenshot_{int(time.time())}.jpg")

    try:
        import subprocess

        proc = subprocess.run(
            ["screencapture", "-x", "-t", "jpg", output_path],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and os.path.exists(output_path):
            return {"status": "success", "path": output_path, "strategy": "fullscreen_fallback"}
        return {"status": "error", "error": (proc.stderr or "Unknown error").strip()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def take_screenshot(app_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        result = smart_capture(target_app=app_name)
        if result.get("status") == "success":
            return {
                "tool": "take_screenshot",
                "status": "success",
                "path": result.get("path"),
                "method": result.get("strategy", result.get("method")),
                "app": result.get("app", app_name or "focused"),
            }
        return {"tool": "take_screenshot", "status": "error", "error": result.get("error", "Unknown error")}
    except Exception as e:
        return {"tool": "take_screenshot", "status": "error", "error": str(e)}
