"""One-shot, no-input native Win32 target identity probe.

Creates one hidden STATIC HWND owned by this Python process, reads the
production Win32Backend identity/generation path twice, destroys the HWND,
and writes a small immutable receipt. It never activates a window or sends
input. This is not a control/effect qualification.
"""
from __future__ import annotations

import ctypes
import datetime as dt
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from ctypes import wintypes

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(REPO_ROOT))
from runtime.backends.win32_v1.backend import Win32Backend


RAW = ROOT / "raw.json"
if RAW.exists():
    raise SystemExit("raw.json already exists; refusing to repeat frozen probe")
if sys.platform != "win32":
    raise SystemExit("native Win32 probe requires Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
    wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

record = {
    "schema": "win32-native-target-identity-probe-v1",
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "platform": platform.platform(),
    "python": sys.version,
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "actions": ["create_hidden_owned_static_window", "read_identity_twice",
                 "read_target_generation_twice", "destroy_owned_window"],
    "input_sent": False,
    "window_activated": False,
    "status": "RUNNING",
}
hwnd = None
try:
    hwnd = user32.CreateWindowExW(
        0, "STATIC", "codex-native-identity-probe", 0,
        0, 0, 1, 1, None, None, kernel32.GetModuleHandleW(None), None)
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())
    record["hwnd"] = int(hwnd)
    record["is_window_after_create"] = bool(user32.IsWindow(hwnd))

    backend = object.__new__(Win32Backend)
    backend.user32 = user32
    backend.kernel32 = kernel32
    backend.gdi32 = gdi32
    backend.targets = {"probe": int(hwnd)}
    Win32Backend._configure_api(backend)
    record["identity_first"] = backend.process_identity("probe")
    record["generation_first"] = backend.target_generation("probe")
    record["identity_second"] = backend.process_identity("probe")
    record["generation_second"] = backend.target_generation("probe")
    record["identity_stable"] = (
        record["identity_first"] == record["identity_second"])
    record["generation_stable"] = (
        record["generation_first"] == record["generation_second"])
    record["status"] = (
        "PASS" if record["is_window_after_create"]
        and record["identity_stable"] and record["generation_stable"]
        else "FAIL")
except BaseException as exc:
    record["status"] = "ERROR"
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc)
finally:
    if hwnd:
        record["destroy_succeeded"] = bool(user32.DestroyWindow(hwnd))
        record["is_window_after_destroy"] = bool(user32.IsWindow(hwnd))
    record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    encoded = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    RAW.write_bytes(encoded)
    record["raw_sha256"] = hashlib.sha256(encoded).hexdigest()
print(json.dumps(record, indent=2, sort_keys=True))
if record["status"] != "PASS" or not record.get("destroy_succeeded") \
        or record.get("is_window_after_destroy"):
    raise SystemExit(1)
