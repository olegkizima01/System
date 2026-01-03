"""App scanning utilities for System CLI.
"""

from __future__ import annotations

import os
import plistlib
from typing import List, Set, Tuple


def scan_installed_apps(app_dirs: List[str]) -> List[str]:
    apps: List[str] = []
    for d in app_dirs:
        try:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if name.endswith(".app"):
                    apps.append(name[:-4])
        except Exception:
            continue
    # unique preserve order
    seen: Set[str] = set()
    out: List[str] = []
    for a in apps:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def scan_installed_app_paths(app_dirs: List[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for d in app_dirs:
        try:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if not name.endswith(".app"):
                    continue
                app_name = name[:-4]
                out.append((app_name, os.path.join(d, name)))
        except Exception:
            continue
    # unique by name, prefer first occurrence
    seen: Set[str] = set()
    uniq: List[Tuple[str, str]] = []
    for app_name, app_path in out:
        if app_name in seen:
            continue
        seen.add(app_name)
        uniq.append((app_name, app_path))
    return uniq


def read_bundle_id(app_path: str) -> str:
    try:
        plist_path = os.path.join(app_path, "Contents", "Info.plist")
        if not os.path.exists(plist_path):
            return ""
        with open(plist_path, "rb") as f:
            data = plistlib.load(f)
        bid = data.get("CFBundleIdentifier")
        return str(bid) if bid else ""
    except Exception:
        return ""


def get_installed_browsers() -> List[str]:
    app_dirs = ["/Applications", os.path.expanduser("~/Applications")]
    installed = scan_installed_app_paths(app_dirs)
    keywords_name = [
        "safari",
        "chrome",
        "chromium",
        "firefox",
        "brave",
        "arc",
        "edge",
        "opera",
        "vivaldi",
        "orion",
        "tor",
        "duckduckgo",
        "waterfox",
        "librewolf",
        "zen",
        "yandex",
    ]
    keywords_bundle = [
        "safari",
        "chrome",
        "chromium",
        "firefox",
        "brave",
        "arc",
        "edge",
        "opera",
        "vivaldi",
        "orion",
        "torbrowser",
        "duckduckgo",
        "browser",
    ]
    browsers: List[str] = []
    for app_name, app_path in installed:
        low = app_name.lower()
        if any(k in low for k in keywords_name):
            browsers.append(app_name)
            continue
        bid = read_bundle_id(app_path).lower()
        if bid and any(k in bid for k in keywords_bundle):
            browsers.append(app_name)
    return sorted({b for b in browsers}, key=lambda x: x.lower())
