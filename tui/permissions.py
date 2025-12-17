"""macOS permissions management for TUI.

Provides functions to check and request macOS privacy permissions:
- Accessibility
- Screen Recording
- Automation (System Events)
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def macos_open_privacy_pane(pane: str) -> None:
    """Open macOS System Preferences to a specific privacy pane."""
    if sys.platform != "darwin":
        return
    p = str(pane or "").strip().lower()
    url_map = {
        "accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        "screen_recording": "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        "automation": "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation",
    }
    url = url_map.get(p)
    if not url:
        return
    try:
        subprocess.run(["/usr/bin/open", url], capture_output=True, text=True)
    except Exception:
        return


def macos_screen_recording_preflight() -> Optional[bool]:
    """Check if screen recording permission is granted (preflight check)."""
    if sys.platform != "darwin":
        return None
    try:
        cg = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        fn = getattr(cg, "CGPreflightScreenCaptureAccess", None)
        if fn is None:
            return None
        fn.restype = ctypes.c_bool
        fn.argtypes = []
        return bool(fn())
    except Exception:
        return None


def macos_screen_recording_request_prompt() -> Optional[bool]:
    """Request screen recording permission with system prompt."""
    if sys.platform != "darwin":
        return None
    try:
        cg = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        fn = getattr(cg, "CGRequestScreenCaptureAccess", None)
        if fn is None:
            return None
        fn.restype = ctypes.c_bool
        fn.argtypes = []
        return bool(fn())
    except Exception:
        return None


def macos_accessibility_is_trusted() -> Optional[bool]:
    """Check if accessibility permission is granted."""
    if sys.platform != "darwin":
        return None
    try:
        app = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        fn = getattr(app, "AXIsProcessTrusted", None)
        if fn is None:
            return None
        fn.restype = ctypes.c_bool
        fn.argtypes = []
        return bool(fn())
    except Exception:
        return None


def macos_accessibility_request_prompt() -> Optional[bool]:
    """Request accessibility permission with system prompt."""
    if sys.platform != "darwin":
        return None
    try:
        app = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        cf = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )

        fn = getattr(app, "AXIsProcessTrustedWithOptions", None)
        if fn is None:
            return None

        key = ctypes.c_void_p.in_dll(app, "kAXTrustedCheckOptionPrompt")
        val = ctypes.c_void_p.in_dll(cf, "kCFBooleanTrue")

        cf.CFDictionaryCreate.restype = ctypes.c_void_p
        cf.CFDictionaryCreate.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        cf.CFRelease.restype = None
        cf.CFRelease.argtypes = [ctypes.c_void_p]

        keys = (ctypes.c_void_p * 1)(key)
        vals = (ctypes.c_void_p * 1)(val)
        d = cf.CFDictionaryCreate(None, keys, vals, 1, None, None)
        try:
            fn.restype = ctypes.c_bool
            fn.argtypes = [ctypes.c_void_p]
            ok = bool(fn(ctypes.c_void_p(d)))
        finally:
            try:
                if d:
                    cf.CFRelease(ctypes.c_void_p(d))
            except Exception:
                pass
        return ok
    except Exception:
        return None


def macos_automation_check_system_events(*, prompt: bool) -> Optional[bool]:
    """Check if automation permission for System Events is granted."""
    if sys.platform != "darwin":
        return None
    script = 'tell application "System Events" to count of processes'
    try:
        proc = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=2.5,
        )
        if proc.returncode == 0:
            return True
        err = (proc.stderr or "") + "\n" + (proc.stdout or "")
        low = err.lower()
        if "not authorised" in low or "not authorized" in low or "not allowed" in low or "permission" in low:
            if prompt:
                try:
                    subprocess.run(
                        ["/usr/bin/osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=2.5,
                    )
                except Exception:
                    pass
            proc2 = subprocess.run(
                ["/usr/bin/osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2.5,
            )
            return bool(proc2.returncode == 0)
        return False
    except Exception:
        return None


def permissions_wizard(
    *,
    require_accessibility: bool,
    require_screen_recording: bool,
    require_automation: bool,
    prompt: bool,
    open_settings: bool,
) -> Dict[str, Any]:
    """Run permissions wizard checking all required permissions."""
    missing: List[str] = []
    out: Dict[str, Any] = {"missing": missing}
    if sys.platform != "darwin":
        return out

    if require_accessibility:
        ok = macos_accessibility_is_trusted()
        if ok is False and prompt:
            macos_accessibility_request_prompt()
            ok = macos_accessibility_is_trusted()
        if ok is False:
            missing.append("accessibility")

    if require_screen_recording:
        ok = macos_screen_recording_preflight()
        if ok is False and prompt:
            macos_screen_recording_request_prompt()
            ok = macos_screen_recording_preflight()
        if ok is False:
            missing.append("screen_recording")

    if require_automation:
        ok = macos_automation_check_system_events(prompt=prompt)
        if ok is False:
            missing.append("automation")

    if open_settings and missing:
        for p in list(dict.fromkeys(missing)):
            macos_open_privacy_pane(p)

    return out


@dataclass
class CommandPermissions:
    """Permissions for command execution."""
    allow_run: bool = False
    allow_shell: bool = False
    allow_applescript: bool = False
    allow_gui: bool = False


def is_confirmed_run(text: str) -> bool:
    """Check if text confirms run permission."""
    return "confirm_run" in str(text or "").lower()


def is_confirmed_shell(text: str) -> bool:
    """Check if text confirms shell permission."""
    return "confirm_shell" in str(text or "").lower()


def is_confirmed_applescript(text: str) -> bool:
    """Check if text confirms applescript permission."""
    return "confirm_applescript" in str(text or "").lower()


def is_confirmed_gui(text: str) -> bool:
    """Check if text confirms GUI permission."""
    return "confirm_gui" in str(text or "").lower()


def is_confirmed_shortcuts(text: str) -> bool:
    """Check if text confirms shortcuts permission."""
    return "confirm_shortcuts" in str(text or "").lower()



def permissions_from_text(text: str) -> CommandPermissions:
    """Parse permissions from text input."""
    return CommandPermissions(
        allow_run=is_confirmed_run(text),
        allow_shell=is_confirmed_shell(text),
        allow_applescript=is_confirmed_applescript(text),
        allow_gui=is_confirmed_gui(text),
    )


# Backward compatibility aliases (prefixed with underscore for internal use)
_macos_open_privacy_pane = macos_open_privacy_pane
_macos_screen_recording_preflight = macos_screen_recording_preflight
_macos_screen_recording_request_prompt = macos_screen_recording_request_prompt
_macos_accessibility_is_trusted = macos_accessibility_is_trusted
_macos_accessibility_request_prompt = macos_accessibility_request_prompt
_macos_automation_check_system_events = macos_automation_check_system_events
_permissions_wizard = permissions_wizard
_is_confirmed_run = is_confirmed_run
_is_confirmed_shell = is_confirmed_shell
_is_confirmed_applescript = is_confirmed_applescript
_is_confirmed_gui = is_confirmed_gui
_is_confirmed_shortcuts = is_confirmed_shortcuts
_permissions_from_text = permissions_from_text
