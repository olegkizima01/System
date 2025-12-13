import base64
import os
import tempfile
import subprocess
from typing import Any, Dict, Optional


def analyze_image_local(image_path: str, *, mode: str = "auto") -> Dict[str, Any]:
    """Best-effort local analysis. Uses dop_materials vision module if present; otherwise returns minimal info."""
    try:
        from dop_materials.super_rag_agent.vision_module import get_vision_module  # type: ignore

        vm = get_vision_module()
        return vm.analyze_screenshot(image_path, mode=mode)
    except Exception as e:
        return {"status": "error", "error": str(e), "image_path": image_path, "mode": mode}


def summarize_image_for_prompt(image_path: str) -> str:
    """Return compact textual observation for LLM prompts."""
    try:
        analysis = analyze_image_local(image_path, mode="auto")
        if analysis.get("status") != "success":
            return f"[VISION] error: {analysis.get('error', 'unknown')}"
        combined = str(analysis.get("combined_description") or "").strip()
        if combined:
            return f"[VISION]\n{combined}"
        return "[VISION] (no combined_description)"
    except Exception as e:
        return f"[VISION] error: {e}"


def load_image_b64(image_path: str) -> Optional[str]:
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def load_image_png_b64(image_path: str) -> Optional[str]:
    """Return a PNG base64 payload.

    Copilot Vision is picky about accepted media types; we normalize to PNG.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        from PIL import Image  # type: ignore

        img = Image.open(image_path)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        try:
            img.save(tmp_path, format="PNG")
            return load_image_b64(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception:
        pass

    # macOS fallback: sips conversion
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        try:
            subprocess.run(["sips", "-s", "format", "png", image_path, "--out", tmp_path], capture_output=True)
            if os.path.exists(tmp_path):
                return load_image_b64(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception:
        return None

    return None
