import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any, Dict, Optional, Set, Tuple


@dataclass
class RecorderConfig:
    base_dir: str = "~/.system_cli/recordings"
    focus_poll_interval_sec: float = 0.5
    clipboard_poll_interval_sec: float = 0.5
    screenshot_min_interval_sec: float = 0.5
    screenshot_click_min_interval_sec: float = 0.3
    screenshot_on_events: bool = True
    screenshot_periodic_enabled: bool = True
    screenshot_periodic_interval_sec: float = 0.5
    mouse_move_enabled: bool = True
    mouse_move_min_interval_sec: float = 0.12
    log_collection_enabled: bool = True
    log_collection_interval_sec: float = 2.0


@dataclass
class RecorderStatus:
    running: bool = False
    session_dir: str = ""
    session_id: str = ""
    start_ts: float = 0.0
    events_count: int = 0


class RecorderService:
    def __init__(self, config: Optional[RecorderConfig] = None) -> None:
        self.config = config or RecorderConfig()
        self.status = RecorderStatus()

        self._stop_event = threading.Event()
        self._events_q: "Queue[Dict[str, Any]]" = Queue(maxsize=5000)
        self._events_fp: Optional[Any] = None
        self._lock = threading.RLock()

        self._writer_thread: Optional[threading.Thread] = None
        self._focus_thread: Optional[threading.Thread] = None
        self._clipboard_thread: Optional[threading.Thread] = None
        self._tap_thread: Optional[threading.Thread] = None
        self._screenshot_periodic_thread: Optional[threading.Thread] = None
        self._log_collection_thread: Optional[threading.Thread] = None

        self._run_loop: Optional[int] = None
        self._tap: Optional[int] = None
        self._src: Optional[int] = None
        self._callback_ref: Any = None

        self._last_front_app: str = ""
        self._last_front_title: str = ""
        self._last_clipboard: Optional[str] = None

        self._last_screenshot_ts: float = 0.0
        self._screen_permission_warned: bool = False

        self._last_mouse_move_ts: float = 0.0

        self._tap_init_event = threading.Event()
        self._tap_init_ok: Optional[bool] = None
        self._tap_init_error: str = ""

    def start(self) -> Tuple[bool, str]:
        with self._lock:
            if self.status.running:
                return False, "Recorder already running"
            if sys.platform != "darwin":
                return False, "Recorder is supported only on macOS"

            self._stop_event.clear()
            self._tap_init_event.clear()
            self._tap_init_ok = None
            self._tap_init_error = ""

            sid = str(int(time.time()))
            base_dir = os.path.expanduser(self.config.base_dir)
            session_dir = os.path.join(base_dir, sid)
            screens_dir = os.path.join(session_dir, "screens")
            os.makedirs(screens_dir, exist_ok=True)

            events_path = os.path.join(session_dir, "events.jsonl")
            self._events_fp = open(events_path, "a", encoding="utf-8")

            self.status.running = True
            self.status.session_id = sid
            self.status.session_dir = session_dir
            self.status.start_ts = time.time()
            self.status.events_count = 0

            self._writer_thread = threading.Thread(target=self._run_writer, daemon=True)
            self._tap_thread = threading.Thread(target=self._run_event_tap, daemon=True)
            self._focus_thread = threading.Thread(target=self._run_focus_poll, daemon=True)
            self._clipboard_thread = threading.Thread(target=self._run_clipboard_poll, daemon=True)
            self._screenshot_periodic_thread = threading.Thread(target=self._run_screenshot_periodic, daemon=True)
            self._log_collection_thread = threading.Thread(target=self._run_log_collection, daemon=True)

            self._writer_thread.start()
            self._tap_thread.start()
            self._focus_thread.start()
            self._clipboard_thread.start()
            self._screenshot_periodic_thread.start()
            self._log_collection_thread.start()

            try:
                self._tap_init_event.wait(timeout=2.0)
            except Exception:
                pass

            if self._tap_init_ok is False:
                err = self._tap_init_error or "Event tap init failed"
                try:
                    self.stop()
                except Exception:
                    pass
                return False, err

            return True, f"Recorder started: {session_dir}"

    def stop(self) -> Tuple[bool, str, Optional[str]]:
        with self._lock:
            if not self.status.running:
                return False, "Recorder is not running", None
            self.status.running = False
            self._stop_event.set()

            run_loop = self._run_loop
            if run_loop:
                try:
                    _CF = ctypes.cdll.LoadLibrary(
                        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
                    )
                    _CF.CFRunLoopStop.argtypes = [ctypes.c_void_p]
                    _CF.CFRunLoopStop(ctypes.c_void_p(run_loop))
                except Exception:
                    pass

        for t in [self._tap_thread, self._focus_thread, self._clipboard_thread]:
            try:
                if t:
                    t.join(timeout=3)
            except Exception:
                pass

        try:
            if self._writer_thread:
                self._writer_thread.join(timeout=5)
        except Exception:
            pass

        with self._lock:
            try:
                if self._events_fp:
                    self._events_fp.flush()
                    self._events_fp.close()
            except Exception:
                pass
            self._events_fp = None

            try:
                meta_path = os.path.join(self.status.session_dir, "meta.json")
                front_app, front_title = self._get_frontmost_app_and_title()
                nm = ""
                try:
                    if str(front_app or "").strip() and str(front_title or "").strip():
                        nm = f"{str(front_app).strip()} — {str(front_title).strip()}".strip()
                    else:
                        nm = str(front_app or "").strip()
                    nm = nm[:120] if nm else ""
                except Exception:
                    nm = ""
                payload = {
                    "session_id": self.status.session_id,
                    "start_ts": float(self.status.start_ts or 0.0),
                    "end_ts": float(time.time()),
                    "events_count": int(self.status.events_count),
                    "front_app": str(front_app or "").strip(),
                    "front_title": str(front_title or "").strip(),
                }
                if nm:
                    payload["name"] = nm
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            out_dir = self.status.session_dir
            return True, f"Recorder stopped: {out_dir}", out_dir

    def get_status(self) -> RecorderStatus:
        with self._lock:
            return RecorderStatus(**self.status.__dict__)

    def _enqueue(self, ev: Dict[str, Any]) -> None:
        try:
            self._events_q.put_nowait(ev)
        except Exception:
            return

    def _run_writer(self) -> None:
        while True:
            if self._stop_event.is_set() and self._events_q.empty():
                break

            try:
                ev = self._events_q.get(timeout=0.25)
            except Empty:
                continue

            try:
                shot_path = self._maybe_screenshot(ev)
                if shot_path:
                    ev["screenshot"] = shot_path
            except Exception:
                pass

            with self._lock:
                try:
                    if self._events_fp:
                        self._events_fp.write(json.dumps(ev, ensure_ascii=False) + "\n")
                        self.status.events_count += 1
                except Exception:
                    pass

    def _maybe_screenshot(self, ev: Dict[str, Any]) -> str:
        if not bool(self.config.screenshot_on_events):
            return ""

        et = str(ev.get("type") or "")
        if et not in {"mouse", "key", "focus", "clipboard"}:
            return ""

        now = time.time()
        min_interval = float(self.config.screenshot_min_interval_sec or 0.0)
        if et == "mouse":
            stp = 0
            try:
                stp = int(ev.get("subtype") or 0)
            except Exception:
                stp = 0
            if stp in {1, 3}:
                try:
                    min_interval = float(getattr(self.config, "screenshot_click_min_interval_sec", min_interval) or min_interval)
                except Exception:
                    min_interval = float(self.config.screenshot_min_interval_sec or 0.0)

        if (now - float(self._last_screenshot_ts or 0.0)) < float(min_interval or 0.0):
            if et != "focus":
                return ""

        app = str(ev.get("front_app") or "").strip() or None

        from system_ai.tools.screenshot import take_screenshot

        out = take_screenshot(app)
        if isinstance(out, dict) and out.get("status") != "success":
            if (
                not self._screen_permission_warned
                and out.get("error_type") == "permission_required"
                and out.get("permission") == "screen_recording"
            ):
                self._screen_permission_warned = True
                self._enqueue(
                    {
                        "type": "warning",
                        "ts": time.time(),
                        "warning": "Screen Recording permission required for screenshots",
                        "permission": "screen_recording",
                    }
                )
            return ""
        if not isinstance(out, dict) or out.get("status") != "success":
            return ""

        src_path = str(out.get("path") or "")
        if not src_path or not os.path.exists(src_path):
            return ""

        screens_dir = os.path.join(self.status.session_dir, "screens")
        os.makedirs(screens_dir, exist_ok=True)

        ext = os.path.splitext(src_path)[1] or ".jpg"
        dst_name = f"shot_{int(now * 1000)}{ext}"
        dst_path = os.path.join(screens_dir, dst_name)

        try:
            shutil.copy2(src_path, dst_path)
        except Exception:
            return ""

        self._last_screenshot_ts = now
        return dst_path

    def _run_focus_poll(self) -> None:
        while not self._stop_event.wait(timeout=max(0.1, float(self.config.focus_poll_interval_sec or 0.5))):
            front_app, front_title = self._get_frontmost_app_and_title()
            if not front_app and not front_title:
                continue

            if front_app != self._last_front_app or front_title != self._last_front_title:
                self._last_front_app = front_app
                self._last_front_title = front_title
                self._enqueue(
                    {
                        "type": "focus",
                        "ts": time.time(),
                        "front_app": front_app,
                        "front_title": front_title,
                    }
                )

    def _run_clipboard_poll(self) -> None:
        while not self._stop_event.wait(timeout=max(0.1, float(self.config.clipboard_poll_interval_sec or 0.5))):
            txt = self._read_clipboard_text()
            if txt is None:
                continue

            if self._last_clipboard is None:
                self._last_clipboard = txt
                continue

            if txt != self._last_clipboard:
                self._last_clipboard = txt
                front_app, front_title = self._get_frontmost_app_and_title()
                self._enqueue(
                    {
                        "type": "clipboard",
                        "ts": time.time(),
                        "front_app": front_app,
                        "front_title": front_title,
                        "text_preview": (txt[:500] if isinstance(txt, str) else ""),
                        "text_len": (len(txt) if isinstance(txt, str) else 0),
                    }
                )

    def _read_clipboard_text(self) -> Optional[str]:
        try:
            proc = subprocess.run(["pbpaste"], capture_output=True, text=True)
            if proc.returncode != 0:
                return None
            return str(proc.stdout or "")
        except Exception:
            return None

    def _get_frontmost_app_and_title(self) -> Tuple[str, str]:
        script = (
            'tell application "System Events"\n'
            'set p to first application process whose frontmost is true\n'
            'set appName to name of p\n'
            'set winName to ""\n'
            'try\n'
            'set winName to name of front window of p\n'
            'end try\n'
            'return appName & "\n" & winName\n'
            'end tell'
        )
        try:
            proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
            if proc.returncode != 0:
                return "", ""
            out = (proc.stdout or "").splitlines()
            app = (out[0] if len(out) > 0 else "").strip()
            title = (out[1] if len(out) > 1 else "").strip()
            return app, title
        except Exception:
            return "", ""

    def _run_event_tap(self) -> None:
        try:
            _AS = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
            )
            _CF = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
            )

            class _CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

            _AS.CGEventGetLocation.restype = _CGPoint
            _AS.CGEventGetLocation.argtypes = [ctypes.c_void_p]
            _AS.CGEventTapCreate.restype = ctypes.c_void_p
            _AS.CGEventTapCreate.argtypes = [
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint64,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]
            _AS.CGEventTapEnable.argtypes = [ctypes.c_void_p, ctypes.c_bool]
            _AS.CFRelease.argtypes = [ctypes.c_void_p]
            _AS.CGEventGetIntegerValueField.restype = ctypes.c_int64
            _AS.CGEventGetIntegerValueField.argtypes = [ctypes.c_void_p, ctypes.c_int]
            _AS.CGEventGetFlags.restype = ctypes.c_uint64
            _AS.CGEventGetFlags.argtypes = [ctypes.c_void_p]

            _CF.CFRunLoopGetCurrent.restype = ctypes.c_void_p
            _CF.CFRunLoopGetCurrent.argtypes = []
            _CF.CFRunLoopRun.restype = None
            _CF.CFRunLoopRun.argtypes = []
            _CF.CFRunLoopStop.restype = None
            _CF.CFRunLoopStop.argtypes = [ctypes.c_void_p]
            _CF.CFMachPortCreateRunLoopSource.restype = ctypes.c_void_p
            _CF.CFMachPortCreateRunLoopSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
            _CF.CFRunLoopAddSource.restype = None
            _CF.CFRunLoopAddSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
            _CF.CFRunLoopRemoveSource.restype = None
            _CF.CFRunLoopRemoveSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

            kCGSessionEventTap = 1
            kCGHeadInsertEventTap = 0
            kCGEventTapOptionDefault = 0

            kCGEventLeftMouseDown = 1
            kCGEventLeftMouseUp = 2
            kCGEventRightMouseDown = 3
            kCGEventRightMouseUp = 4
            kCGEventMouseMoved = 5
            kCGEventLeftMouseDragged = 6
            kCGEventRightMouseDragged = 7
            kCGEventKeyDown = 10
            kCGEventKeyUp = 11
            kCGEventFlagsChanged = 12

            kCGKeyboardEventKeycode = 9

            event_mask = ctypes.c_uint64(
                (1 << kCGEventLeftMouseDown)
                | (1 << kCGEventLeftMouseUp)
                | (1 << kCGEventRightMouseDown)
                | (1 << kCGEventRightMouseUp)
                | (1 << kCGEventMouseMoved)
                | (1 << kCGEventLeftMouseDragged)
                | (1 << kCGEventRightMouseDragged)
                | (1 << kCGEventKeyDown)
                | (1 << kCGEventKeyUp)
                | (1 << kCGEventFlagsChanged)
            )

            run_loop = int(_CF.CFRunLoopGetCurrent() or 0)
            with self._lock:
                self._run_loop = run_loop

            CALLBACK = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)

            def _cb(proxy, etype, event, refcon):
                try:
                    if self._stop_event.is_set():
                        if run_loop:
                            _CF.CFRunLoopStop(ctypes.c_void_p(run_loop))
                        return event

                    et = int(etype)
                    ts = time.time()
                    front_app, front_title = self._get_frontmost_app_and_title()

                    if et in {kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, kCGEventRightMouseUp}:
                        p = _AS.CGEventGetLocation(event)
                        self._enqueue(
                            {
                                "type": "mouse",
                                "ts": ts,
                                "subtype": et,
                                "x": float(p.x),
                                "y": float(p.y),
                                "front_app": front_app,
                                "front_title": front_title,
                            }
                        )
                    elif et in {kCGEventMouseMoved, kCGEventLeftMouseDragged, kCGEventRightMouseDragged}:
                        if not bool(self.config.mouse_move_enabled):
                            return event
                        now = ts
                        min_dt = float(self.config.mouse_move_min_interval_sec or 0.0)
                        if min_dt > 0 and (now - float(self._last_mouse_move_ts or 0.0)) < min_dt:
                            return event
                        self._last_mouse_move_ts = now
                        p = _AS.CGEventGetLocation(event)
                        self._enqueue(
                            {
                                "type": "mouse_move",
                                "ts": ts,
                                "subtype": et,
                                "x": float(p.x),
                                "y": float(p.y),
                                "front_app": front_app,
                                "front_title": front_title,
                            }
                        )
                    elif et in {kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged}:
                        keycode = int(_AS.CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode) or 0)
                        flags = int(_AS.CGEventGetFlags(event) or 0)
                        self._enqueue(
                            {
                                "type": "key",
                                "ts": ts,
                                "subtype": et,
                                "keycode": keycode,
                                "flags": flags,
                                "front_app": front_app,
                                "front_title": front_title,
                            }
                        )
                except Exception:
                    try:
                        if run_loop:
                            _CF.CFRunLoopStop(ctypes.c_void_p(run_loop))
                    except Exception:
                        pass
                return event

            cb = CALLBACK(_cb)
            self._callback_ref = cb

            tap = _AS.CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                event_mask,
                cb,
                None,
            )

            if not tap:
                self._tap_init_ok = False
                self._tap_init_error = "CGEventTapCreate failed (enable Accessibility permission for Terminal/IDE)"
                try:
                    self._tap_init_event.set()
                except Exception:
                    pass
                self._enqueue({"type": "error", "ts": time.time(), "error": self._tap_init_error})
                return

            self._tap_init_ok = True
            try:
                self._tap_init_event.set()
            except Exception:
                pass

            src = _CF.CFMachPortCreateRunLoopSource(None, tap, 0)
            kCFRunLoopCommonModes = ctypes.c_void_p.in_dll(_CF, "kCFRunLoopCommonModes")
            _CF.CFRunLoopAddSource(ctypes.c_void_p(run_loop), src, kCFRunLoopCommonModes)
            _AS.CGEventTapEnable(tap, True)

            with self._lock:
                self._tap = int(tap)
                self._src = int(src)

            _CF.CFRunLoopRun()

            try:
                _AS.CGEventTapEnable(tap, False)
            except Exception:
                pass
            try:
                _CF.CFRunLoopRemoveSource(ctypes.c_void_p(run_loop), src, kCFRunLoopCommonModes)
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
        except Exception as e:
            self._tap_init_ok = False
            self._tap_init_error = str(e)
            try:
                self._tap_init_event.set()
            except Exception:
                pass
            self._enqueue({"type": "error", "ts": time.time(), "error": str(e)})
            return

    def _run_screenshot_periodic(self) -> None:
        if not bool(self.config.screenshot_periodic_enabled):
            return
        while not self._stop_event.wait(timeout=max(0.1, float(self.config.screenshot_periodic_interval_sec or 0.5))):
            try:
                front_app, front_title = self._get_frontmost_app_and_title()
                if not front_app:
                    continue
                from system_ai.tools.screenshot import take_screenshot
                out = take_screenshot(front_app)
                if isinstance(out, dict) and out.get("status") == "success":
                    src_path = str(out.get("path") or "")
                    if src_path and os.path.exists(src_path):
                        screens_dir = os.path.join(self.status.session_dir, "screens")
                        os.makedirs(screens_dir, exist_ok=True)
                        ext = os.path.splitext(src_path)[1] or ".jpg"
                        dst_name = f"periodic_{int(time.time() * 1000)}{ext}"
                        dst_path = os.path.join(screens_dir, dst_name)
                        try:
                            shutil.copy2(src_path, dst_path)
                            self._enqueue({
                                "type": "screenshot_periodic",
                                "ts": time.time(),
                                "path": dst_path,
                                "front_app": front_app,
                                "front_title": front_title,
                            })
                        except Exception:
                            pass
            except Exception:
                pass

    def _run_log_collection(self) -> None:
        if not bool(self.config.log_collection_enabled):
            return
        logs_dir = os.path.join(self.status.session_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        last_log_ts: Dict[str, float] = {}
        tracked_apps: Set[str] = set()
        
        while not self._stop_event.wait(timeout=max(0.1, float(self.config.log_collection_interval_sec or 2.0))):
            try:
                front_app, _ = self._get_frontmost_app_and_title()
                if not front_app:
                    continue
                
                now = time.time()
                
                if front_app not in tracked_apps:
                    tracked_apps.add(front_app)
                    last_log_ts[front_app] = now
                
                start_ts = int(last_log_ts.get(front_app, now))
                end_ts = int(now)
                
                log_file = os.path.join(logs_dir, f"{front_app}.log")
                
                cmd = f"log stream --predicate 'process==\"{front_app}\"' --level debug --style json --start '{start_ts}' --end '{end_ts}' 2>/dev/null || true"
                try:
                    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                    if proc.stdout:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(f"[{now}] {front_app}:\n")
                            f.write(proc.stdout)
                            f.write("\n")
                        self._enqueue({
                            "type": "log_collected",
                            "ts": now,
                            "app": front_app,
                            "log_file": log_file,
                        })
                except Exception:
                    pass
                
                last_log_ts[front_app] = now
            except Exception:
                pass
