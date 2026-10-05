"""One-shot, process-targeted Win32 SendInput / GetAsyncKeyState smoke."""
from __future__ import annotations

import ctypes
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent / "result.json"
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite write-once result: {OUTPUT}")
if sys.platform != "win32":
    raise SystemExit("STOP_WRONG_PLATFORM")
sys.path.insert(0, str(ROOT))

from runtime.backends.win32_v1.backend import Win32Backend  # noqa: E402

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
    wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

VK_SHIFT = 0x10
WS_OVERLAPPEDWINDOW = 0x00CF0000
SW_SHOWNORMAL = 5
old_foreground = int(user32.GetForegroundWindow() or 0)
hwnd = 0
backend = None
result = {
    "schema": "win32-key-transition-host-smoke-a01-v1",
    "platform": sys.platform,
    "input_key": "SHIFT",
    "preconditions": {},
    "transitions": [],
    "release": None,
    "outcome": "UNSET",
}

try:
    hwnd = int(user32.CreateWindowExW(
        0, "STATIC", "Codex isolated Win32 key-state smoke target",
        WS_OVERLAPPEDWINDOW, 8, 8, 1, 1, None, None,
        kernel32.GetModuleHandleW(None), None,
    ) or 0)
    if not hwnd:
        raise OSError(ctypes.get_last_error(), "CreateWindowExW failed")
    user32.ShowWindow(hwnd, SW_SHOWNORMAL)
    focused_by_call = bool(user32.SetForegroundWindow(hwnd))
    if not focused_by_call and int(user32.GetForegroundWindow() or 0) != hwnd:
        result["outcome"] = "STOP_CANNOT_FOCUS_OWN_WINDOW"
    else:
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline and int(user32.GetForegroundWindow() or 0) != hwnd:
            time.sleep(0.005)
        focused = int(user32.GetForegroundWindow() or 0) == hwnd
        shift_initially_down = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
        result["preconditions"] = {
            "probe_hwnd_foreground": focused,
            "shift_initially_down": shift_initially_down,
            "prior_foreground_hwnd": old_foreground,
            "probe_hwnd": hwnd,
        }
        if not focused:
            result["outcome"] = "STOP_OWN_WINDOW_NOT_FOREGROUND"
        elif shift_initially_down:
            result["outcome"] = "STOP_SHIFT_ALREADY_DOWN"
        else:
            backend = Win32Backend({"probe": hwnd})
            backend._current_program_id = "win32-key-transition-smoke-a01"
            backend._current_operation_index = 0
            backend._current_admitted_ns = time.monotonic_ns()
            backend.key_state("SHIFT", True)
            backend._current_operation_index = 1
            backend.key_state("SHIFT", False)
            result["transitions"] = list(backend.last_input_transitions)
            result["release"] = backend.release_all()
            result["outcome"] = "PASS_SCOPED"
except BaseException as exc:
    result["outcome"] = "FAIL_EXCEPTION"
    result["error"] = {"type": type(exc).__name__, "detail": str(exc)}
finally:
    if backend is not None:
        try:
            if backend.held_keys or backend.held_buttons:
                result["final_safety_release"] = backend.release_all()
            if result["transitions"]:
                result["transitions"] = list(backend.last_input_transitions)
        except BaseException as exc:
            result["final_safety_release_error"] = {
                "type": type(exc).__name__, "detail": str(exc)
            }
            result["outcome"] = "FAIL_CLEANUP"
    if hwnd and user32.IsWindow(hwnd):
        user32.DestroyWindow(hwnd)
    if old_foreground and user32.IsWindow(old_foreground):
        user32.SetForegroundWindow(old_foreground)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(OUTPUT)
