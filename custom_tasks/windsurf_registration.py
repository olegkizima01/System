import sys
import time
import subprocess
import ctypes
import json
import os
from typing import Tuple, Optional, List, Dict, Any

def log(msg: str):
    print(f"[WindsurfReg] {msg}")


def _notify(msg: str):
    safe_msg = msg.replace('"', '\\"')
    script = f'''
    try
        display notification "{safe_msg}" with title "Windsurf Registration"
    end try
    '''
    subprocess.run(["osascript", "-e", script], stderr=subprocess.DEVNULL)

def activate_app(app_name: str):
    """
    Attempts to force-activate an application using multiple methods.
    1. 'open -a' (tells OS to switch)
    2. AppleScript 'activate'
    3. System Events 'set frontmost'
    """
    log(f"Activating {app_name}...")
    
    # Method 1: Standard open command (handles potential launch if closed)
    subprocess.run(["open", "-a", app_name], stderr=subprocess.DEVNULL)
    time.sleep(0.5) # Give OS a moment

    # Method 2 & 3: AppleScript Force
    script = f'''
    tell application "{app_name}" to activate
    delay 0.2
    tell application "System Events"
        set frontmost of (first process whose name contains "{app_name}") to true
    end tell
    '''
    subprocess.run(["osascript", "-e", script], stderr=subprocess.DEVNULL)

def gui_prompt_step(msg: str, app_to_focus: str = None) -> bool:
    """
    Uses macOS System Dialog to prompt. 
    If app_to_focus is provided, it tries to keep that app active *before* showing the dialog.
    """
    if app_to_focus:
        activate_app(app_to_focus)
    
    # Escape quotes for AppleScript
    safe_msg = msg.replace('"', '\\"')
    script = f'''
    tell application "System Events"
        activate
        try
            display dialog "{safe_msg}" buttons {{"Cancel", "OK"}} default button "OK" with icon note
            return "true"
        on error
            return "false"
        end try
    end tell
    '''
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if "true" in proc.stdout:
            print(f"User confirmed: {msg}")
            return True
        print(f"User canceled: {msg}")
        return False
    except Exception as e:
        print(f"Dialog error: {e}")
        return False
        
# Alias prompt_step to gui_prompt_step
prompt_step = gui_prompt_step


def _auto_step(msg: str, app_to_focus: str = None, wait_seconds: float = 0.0):
    log(msg)
    _notify(msg)
    if app_to_focus:
        activate_app(app_to_focus)
    if wait_seconds and wait_seconds > 0:
        time.sleep(wait_seconds)


def _wait_for_path(path: str, timeout_seconds: int, poll_seconds: float = 2.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        proc = subprocess.run(["test", "-e", path])
        if proc.returncode == 0:
            return True
        time.sleep(poll_seconds)
    return False


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


_AS = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
_AS.CGEventCreateMouseEvent.restype = ctypes.c_void_p
_AS.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CGPoint, ctypes.c_uint32]
_AS.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
_AS.CFRelease.argtypes = [ctypes.c_void_p]
_AS.CGEventGetLocation.restype = _CGPoint
_AS.CGEventGetLocation.argtypes = [ctypes.c_void_p]
_AS.CGEventTapCreate.restype = ctypes.c_void_p
_AS.CGEventTapCreate.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_void_p]
_AS.CGEventTapEnable.restype = None
_AS.CGEventTapEnable.argtypes = [ctypes.c_void_p, ctypes.c_bool]


def _cg_post_mouse_event(event_type: int, x: float, y: float):
    ev = _AS.CGEventCreateMouseEvent(None, int(event_type), _CGPoint(float(x), float(y)), 0)
    if ev:
        _AS.CGEventPost(0, ev)
        _AS.CFRelease(ev)


def _mouse_move(x: float, y: float):
    _cg_post_mouse_event(5, x, y)


def _mouse_click(x: float, y: float, hold_seconds: float = 0.03):
    _cg_post_mouse_event(1, x, y)
    time.sleep(float(hold_seconds) if hold_seconds and hold_seconds > 0 else 0.03)
    _cg_post_mouse_event(2, x, y)


def _highlight_click(x: float, y: float, highlight_seconds: float = 0.35, hold_seconds: float = 0.03):
    _mouse_move(x, y)
    time.sleep(highlight_seconds)
    _mouse_click(x, y, hold_seconds=hold_seconds)


_CF = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
_CF.CFRunLoopGetCurrent.restype = ctypes.c_void_p
_CF.CFRunLoopGetCurrent.argtypes = []
_CF.CFRunLoopRun.restype = None
_CF.CFRunLoopRun.argtypes = []
_CF.CFRunLoopStop.restype = None
_CF.CFRunLoopStop.argtypes = [ctypes.c_void_p]
_CF.CFRunLoopAddSource.restype = None
_CF.CFRunLoopAddSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
_CF.CFRunLoopRemoveSource.restype = None
_CF.CFRunLoopRemoveSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
_CF.CFMachPortCreateRunLoopSource.restype = ctypes.c_void_p
_CF.CFMachPortCreateRunLoopSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]


def calibrate_clearvpn_clicks(num_clicks: int = 6, save_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Records user left-clicks (global event tap).
    First click = checkpoint (base). Next clicks saved as offsets dx/dy relative to base.
    Also stores dt between clicks.
    """
    state: Dict[str, Any] = {
        "num_clicks": int(num_clicks),
        "clicks_abs": [],
        "times": [],
        "base": None,
        "last_t": None,
    }

    kCGEventLeftMouseDown = 1
    kCGSessionEventTap = 1
    kCGHeadInsertEventTap = 0
    kCGEventTapOptionDefault = 0
    kCFRunLoopCommonModes = ctypes.c_void_p.in_dll(_CF, "kCFRunLoopCommonModes")

    run_loop = _CF.CFRunLoopGetCurrent()
    state["_run_loop"] = run_loop

    CALLBACK = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)

    def _cb(proxy, etype, event, refcon):
        try:
            if int(etype) == kCGEventLeftMouseDown:
                p = _AS.CGEventGetLocation(event)
                t = time.monotonic()
                state["clicks_abs"].append([float(p.x), float(p.y)])
                state["times"].append(float(t))

                if state["base"] is None:
                    state["base"] = [float(p.x), float(p.y)]
                base_x, base_y = state["base"]
                last_t = state["last_t"]
                dt = 0.0 if last_t is None else max(0.0, float(t - float(last_t)))
                state["last_t"] = float(t)

                dx = float(p.x) - float(base_x)
                dy = float(p.y) - float(base_y)

                idx = len(state["clicks_abs"])
                log(f"[CAL] click {idx}/{num_clicks}: x={p.x:.0f} y={p.y:.0f}  dx={dx:.0f} dy={dy:.0f}  dt={dt:.2f}s")

                if idx >= int(num_clicks):
                    _CF.CFRunLoopStop(run_loop)
        except Exception as e:
            log(f"[CAL] callback error: {e}")
            _CF.CFRunLoopStop(run_loop)
        return event

    cb = CALLBACK(_cb)
    event_mask = ctypes.c_uint64(1 << kCGEventLeftMouseDown)

    tap = _AS.CGEventTapCreate(
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        event_mask,
        cb,
        None,
    )
    if not tap:
        raise RuntimeError("CGEventTapCreate failed. Enable Accessibility permissions for Terminal/IDE and try again.")

    src = _CF.CFMachPortCreateRunLoopSource(None, tap, 0)
    _CF.CFRunLoopAddSource(run_loop, src, kCFRunLoopCommonModes)
    _AS.CGEventTapEnable(tap, True)

    log(f"[CAL] Waiting for {num_clicks} clicks... (ESC not supported; finish by completing clicks)")
    _CF.CFRunLoopRun()

    try:
        _AS.CGEventTapEnable(tap, False)
    except Exception:
        pass
    try:
        _CF.CFRunLoopRemoveSource(run_loop, src, kCFRunLoopCommonModes)
    except Exception:
        pass
    try:
        _AS.CFRelease(src)
    except Exception:
        pass
    try:
        _AS.CFRelease(tap)
    except Exception:
        pass

    clicks_abs: List[List[float]] = state["clicks_abs"]
    times: List[float] = state["times"]
    if not clicks_abs:
        raise RuntimeError("No clicks captured")

    base_x, base_y = clicks_abs[0]
    out_clicks: List[Dict[str, float]] = []
    for i, (x, y) in enumerate(clicks_abs):
        dt = 0.0 if i == 0 else max(0.0, float(times[i] - times[i - 1]))
        out_clicks.append({
            "dx": float(x - base_x),
            "dy": float(y - base_y),
            "dt": float(dt),
        })

    result: Dict[str, Any] = {
        "base": {"x": float(base_x), "y": float(base_y)},
        "clicks": out_clicks,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def _load_click_calibration(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "base" not in data or "clicks" not in data:
        raise ValueError("Invalid calibration format")
    base = data.get("base")
    clicks = data.get("clicks")
    if not isinstance(base, dict) or "x" not in base or "y" not in base:
        raise ValueError("Invalid calibration base")
    if not isinstance(clicks, list) or not clicks:
        raise ValueError("Invalid calibration clicks")
    return data


def _replay_click_calibration(
    calibration: Dict[str, Any],
    max_clicks: Optional[int] = None,
    min_dt: float = 0.25,
    pre_click_delay: float = 0.25,
    hold_seconds: float = 0.06,
    debug_cursor: bool = False,
):
    base = calibration["base"]
    base_x = float(base["x"])
    base_y = float(base["y"])
    clicks = calibration["clicks"]
    if max_clicks is not None:
        clicks = clicks[: int(max_clicks)]

    for i, c in enumerate(clicks):
        dt = float(c.get("dt", 0.0))
        if i > 0:
            time.sleep(max(float(min_dt), dt))

        x = base_x + float(c.get("dx", 0.0))
        y = base_y + float(c.get("dy", 0.0))

        if debug_cursor:
            _highlight_click(x, y, highlight_seconds=float(pre_click_delay), hold_seconds=float(hold_seconds))
        else:
            _mouse_move(x, y)
            time.sleep(float(pre_click_delay))
            _mouse_click(x, y, hold_seconds=float(hold_seconds))


def _get_next_city() -> str:
    """Simple alternator: reads/writes a counter file to toggle between 'odessa' and 'kyiv'."""
    counter_file = os.path.join(os.path.dirname(__file__), ".vpn_city_counter")
    try:
        with open(counter_file, "r", encoding="utf-8") as f:
            val = int(f.read().strip())
    except Exception:
        val = 0
    next_val = 1 - val
    try:
        with open(counter_file, "w", encoding="utf-8") as f:
            f.write(str(next_val))
    except Exception:
        pass
    return "odessa" if val == 0 else "kyiv"


def reset_city_alternator(start_city: str = "odessa"):
    """Reset the alternator to start with a given city ('odessa' or 'kyiv')."""
    counter_file = os.path.join(os.path.dirname(__file__), ".vpn_city_counter")
    val = 0 if start_city == "odessa" else 1
    try:
        with open(counter_file, "w", encoding="utf-8") as f:
            f.write(str(val))
    except Exception:
        pass


def _get_clearvpn_window_rect() -> Optional[Tuple[float, float, float, float]]:
    script = r'''
    try
        tell application "ClearVPN" to activate
    end try
    delay 0.2

    tell application "System Events"
        if not (exists process "ClearVPN") then return ""
        tell process "ClearVPN"
            set frontmost to true
            delay 0.2
            if (count of windows) is 0 then
                delay 0.6
                if (count of windows) is 0 then return ""
            end if
            set w to item 1 of windows
            set p to position of w
            set s to size of w
            set wx to item 1 of p
            set wy to item 2 of p
            set ww to item 1 of s
            set wh to item 2 of s
            return (wx as text) & "," & (wy as text) & "," & (ww as text) & "," & (wh as text)
        end tell
    end tell
    '''
    proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    raw = (proc.stdout or "").strip()
    if proc.returncode != 0 or not raw or "," not in raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 4:
        return None
    try:
        return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
    except Exception:
        return None


def _clearvpn_click_location_control(click_variant: int = 1, debug_cursor: bool = False) -> bool:
    rect = _get_clearvpn_window_rect()
    if not rect:
        return False
    wx, wy, ww, wh = rect
    cy = wy + (wh * 0.78)
    cx = wx + (ww * (0.38 if int(click_variant) == 1 else 0.82))
    if debug_cursor:
        _highlight_click(cx, cy)
    else:
        _mouse_click(cx, cy)
    return True


def _clearvpn_select_inactive_city_under_ukraine(debug_cursor: bool = False) -> bool:
    rect = _get_clearvpn_window_rect()
    if not rect:
        return False
    wx, wy, ww, wh = rect

    arrow_x = wx + (ww * 0.965)
    uk_y = wy + (wh * 0.58)
    if debug_cursor:
        _highlight_click(arrow_x, uk_y)
    else:
        _mouse_click(arrow_x, uk_y)

    time.sleep(0.45)

    city_x = wx + (ww * 0.62)
    city_y = wy + (wh * 0.69)
    if debug_cursor:
        _highlight_click(city_x, city_y)
    else:
        _mouse_click(city_x, city_y)
    return True


def _clearvpn_click_in_list_below_static_area(debug_cursor: bool = False) -> bool:
    rect = _get_clearvpn_window_rect()
    if not rect:
        return False
    wx, wy, ww, wh = rect

    static_bottom_y = wy + (wh * 0.44)

    candidates = [
        (wx + (ww * 0.70), static_bottom_y + (wh * 0.26)),
        (wx + (ww * 0.72), static_bottom_y + (wh * 0.34)),
        (wx + (ww * 0.68), static_bottom_y + (wh * 0.42)),
    ]

    for x, y in candidates:
        if debug_cursor:
            _highlight_click(x, y)
        else:
            _mouse_click(x, y)
        time.sleep(0.25)

    return True

def open_safari_private(url: str):
    """Opens a new Private Window in Safari and loads the URL"""
    activate_app("Safari")
    # Keystroke Cmd+Shift+N to open private window
    script = f'''
    tell application "System Events"
        tell application process "Safari"
            set frontmost to true
            keystroke "n" using {{command down, shift down}}
        end tell
    end tell
    tell application "Safari"
        set URL of front document to "{url}"
    end tell
    '''
    subprocess.run(["osascript", "-e", script])

def open_chrome_guest(url: str = ""):
    """Opens Google Chrome in Guest mode using CLI flags"""
    # -n forces a new instance, --args --guest launches guest mode
    cmd = ["open", "-n", "-a", "Google Chrome", "--args", "--guest"]
    if url:
        cmd.append(url)
    subprocess.run(cmd)

def run_windsurf_registration(interactive: bool = False, debug_cursor: bool = True) -> Tuple[bool, str]:
    log("Запуск сценарію реєстрації Windsurf...")

    step = gui_prompt_step if interactive else _auto_step

    if interactive:
        if not step("КРОК 1: VPN. Відкриваємо ClearVPN. Готові?", app_to_focus="ClearVPN"):
            return False, "Відмінено користувачем (VPN)."
    else:
        step("КРОК 1: VPN. Відкриваємо ClearVPN.", app_to_focus="ClearVPN", wait_seconds=1.0)
    subprocess.run(["open", "-a", "ClearVPN"])
    activate_app("ClearVPN")

    if not interactive:
        city = _get_next_city()
        log(f"[VPN] City selected: {city}")
        calibration_path = os.environ.get("CLEARVPN_CALIBRATION", f"clearvpn_calibration_{city}.json")
        if calibration_path and os.path.exists(calibration_path):
            try:
                log(f"[VPN] Using calibration: {calibration_path}")
                calib = _load_click_calibration(calibration_path)
                time.sleep(0.6)
                activate_app("ClearVPN")
                _replay_click_calibration(
                    calib,
                    max_clicks=int(os.environ.get("CLEARVPN_CLICKS", "3")),
                    min_dt=float(os.environ.get("CLEARVPN_MIN_DT", "0.8")),
                    pre_click_delay=float(os.environ.get("CLEARVPN_PRE_CLICK", "0.6")),
                    hold_seconds=float(os.environ.get("CLEARVPN_HOLD", "0.12")),
                    debug_cursor=bool(debug_cursor),
                )
            except Exception as e:
                log(f"[VPN] Calibration failed, fallback to heuristic clicks: {e}")
                time.sleep(0.4)
                _clearvpn_click_location_control(1, debug_cursor=debug_cursor)
                time.sleep(2.0)
                activate_app("ClearVPN")
                _clearvpn_click_location_control(2, debug_cursor=debug_cursor)
                time.sleep(0.8)
                activate_app("ClearVPN")
                _clearvpn_click_in_list_below_static_area(debug_cursor=debug_cursor)
        else:
            log(f"[VPN] Calibration file not found: {calibration_path}. Using heuristic clicks.")
            time.sleep(0.4)
            _clearvpn_click_location_control(1, debug_cursor=debug_cursor)
            time.sleep(2.0)
            activate_app("ClearVPN")
            _clearvpn_click_location_control(2, debug_cursor=debug_cursor)
            time.sleep(0.8)
            activate_app("ClearVPN")
            _clearvpn_click_in_list_below_static_area(debug_cursor=debug_cursor)

    if interactive:
        if not step("1. (Пересуньте це вікно, якщо заважає).\\nНатисніть на кнопку 'Україна' (або поточну країну), щоб відкрити список.\\n\\nКОЛИ СПИСОК ВІДКРИЄТЬСЯ -> Натисніть OK тут.", app_to_focus="ClearVPN"):
            return False, "Відмінено."
        if not step("2. Виберіть БУДЬ-ЯКУ ІНШУ країну зі списку.\\n\\nКОЛИ ПІДКЛЮЧЕННЯ ПОЧНЕТЬСЯ -> Натисніть OK тут.", app_to_focus="ClearVPN"):
            return False, "Відмінено."
        if not step("VPN підключено? Натисніть OK для продовження.", app_to_focus="ClearVPN"):
            return False, "Відмінено."
    else:
        step("1. Натисніть на кнопку 'Україна' (або поточну країну), щоб відкрити список. Потім виберіть інше місто/локацію.", app_to_focus="ClearVPN", wait_seconds=12.0)
        step("2. Перевірте що VPN підключено.", app_to_focus="ClearVPN", wait_seconds=3.0)

    if interactive:
        if not step("КРОК 2: Відкриваємо temp-mail.org у Safari (Приватне вікно).", app_to_focus="Safari"):
            return False, "Відмінено."
    else:
        step("КРОК 2: Відкриваємо temp-mail.org у Safari (Приватне вікно).", app_to_focus="Safari", wait_seconds=0.5)
    
    open_safari_private("https://temp-mail.org")
    
    if interactive:
        if not step("КРОК 3: Пройдіть перевірку Cloudflare (капча) на сайті temp-mail.org.", app_to_focus="Safari"):
            return False, "Відмінено."
    else:
        step("КРОК 3: Пройдіть перевірку Cloudflare (капча) на сайті temp-mail.org.", app_to_focus="Safari", wait_seconds=45.0)

    if interactive:
        if not step("КРОК 4: Відкриваємо Google Chrome (Гостьовий режим).", app_to_focus="Google Chrome"):
            return False, "Відмінено."
    else:
        step("КРОК 4: Відкриваємо Google Chrome (Гостьовий режим).", app_to_focus="Google Chrome", wait_seconds=0.5)
    open_chrome_guest()

    if interactive:
        if not step("КРОК 5: Завантажте Windsurf з офіційного сайту (codeium.com/windsurf).", app_to_focus="Google Chrome"):
            return False, "Відмінено."
    else:
        step("КРОК 5: Відкриваю сторінку завантаження Windsurf.", app_to_focus="Google Chrome", wait_seconds=0.5)
    # Open download link in the already open Chrome Guest or explicitly
    # We can try to open it in Chrome Guest by passing the URL, but if it's already open, 
    # the user can just type it or we launch a new guest window.
    # Let's launch a specific Guest window for the site if possible, or just tell user to go there.
    # Simplest: Launch another guest window with the URL
    open_chrome_guest("https://codeium.com/windsurf")
    
    if interactive:
        if not step("Встановіть Windsurf (перетягніть в Applications). ПОЧЕКАЙТЕ 10с. Запустіть його.", app_to_focus="Finder"):
            return False, "Відмінено."
    else:
        step("Встановіть Windsurf (перетягніть в Applications). Я чекатиму появи /Applications/Windsurf.app.", app_to_focus="Finder", wait_seconds=1.0)
        if not _wait_for_path("/Applications/Windsurf.app", timeout_seconds=600, poll_seconds=2.0):
            return False, "Windsurf не встановлено (timeout)."
        subprocess.run(["open", "-a", "Windsurf"])
        step("Windsurf запускається...", app_to_focus="Windsurf", wait_seconds=10.0)

    # 6. Registration Flow
    log("Інструкція для реєстрації:")
    log(" - Виберіть 'Sign Up'")
    log(" - Скопіюйте пошту з Safari (temp-mail)")
    log(" - Ім'я: (наприклад, Cristof для домену asurad.com -> перша буква домену)")
    log(" - Прізвище: (наприклад, Asurad -> назва домену)")
    log(" - Пароль: Qwas@000")
    
    if interactive:
        if not step("КРОК 6: Пройдіть реєстрацію. (Автоматично відкриється Chrome з реєстрацією)", app_to_focus="Google Chrome"):
            return False, "Відмінено."
    else:
        step("КРОК 6: Пройдіть етапи установки Windsurf до вибору Sign Up. Далі зареєструйтесь (Chrome відкриється автоматично).", app_to_focus="Windsurf", wait_seconds=40.0)
    
    # User interacts with Windsurf app here. We can activate it for them.
    # We don't know the exact process name if it's 'Windsurf' or 'Electron', assum 'Windsurf'
    activate_app("Windsurf")

    if interactive:
        if not step("КРОК 7: Перевірте Temp Mail у Safari, скопіюйте код.", app_to_focus="Safari"):
            return False, "Відмінено."
    else:
        step("КРОК 7: У Safari відкрийте лист та скопіюйте код підтвердження (сині цифри).", app_to_focus="Safari", wait_seconds=25.0)
    activate_app("Safari")
    
    if interactive:
        if not step("КРОК 8: Вставте код у Chrome, завершіть реєстрацію.", app_to_focus="Google Chrome"):
            return False, "Відмінено."
    else:
        step("КРОК 8: У Chrome вставте код у першу комірку та підтвердіть.", app_to_focus="Google Chrome", wait_seconds=20.0)
    activate_app("Google Chrome")

    if interactive:
        if not step("КРОК 9: Відкрийте Windsurf. Готово?", app_to_focus="Windsurf"):
            return False, "Відмінено."
    else:
        step("КРОК 9: Підтвердіть відкриття Windsurf у браузері (checkbox + Open).", app_to_focus="Google Chrome", wait_seconds=8.0)
    activate_app("Windsurf")

    return True, "Реєстрацію Windsurf завершено успішно."
