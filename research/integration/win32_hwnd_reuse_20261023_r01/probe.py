"""One-shot no-input native Win32 HWND reuse discriminator."""
from __future__ import annotations

import ctypes
import datetime as dt
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
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
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
    "schema": "win32-hidden-hwnd-reuse-receipt-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "platform": platform.platform(),
    "python": sys.version,
    "input_sent": False,
    "window_activated": False,
    "status": "RUNNING",
}
hwnd1 = None
hwnd2 = None
backend = object.__new__(Win32Backend)
backend.user32 = user32
backend.kernel32 = kernel32
backend.gdi32 = gdi32
backend.targets = {"probe": 0}
Win32Backend._configure_api(backend)
try:
    hwnd1 = user32.CreateWindowExW(
        0, "STATIC", "codex-hwnd-reuse-r01-a", 0,
        0, 0, 1, 1, None, None, kernel32.GetModuleHandleW(None), None)
    if not hwnd1:
        raise ctypes.WinError(ctypes.get_last_error())
    backend.targets["probe"] = int(hwnd1)
    record["first_hwnd"] = int(hwnd1)
    record["first_identity"] = backend._window_owner_identity_for_hwnd(int(hwnd1))
    record["first_generation"] = backend.target_generation("probe")
    record["first_destroy_succeeded"] = bool(user32.DestroyWindow(hwnd1))
    record["first_is_window_after_destroy"] = bool(user32.IsWindow(hwnd1))

    hwnd2 = user32.CreateWindowExW(
        0, "STATIC", "codex-hwnd-reuse-r01-b", 0,
        0, 0, 1, 1, None, None, kernel32.GetModuleHandleW(None), None)
    if not hwnd2:
        raise ctypes.WinError(ctypes.get_last_error())
    backend.targets["probe"] = int(hwnd2)
    record["second_hwnd"] = int(hwnd2)
    record["second_identity"] = backend._window_owner_identity_for_hwnd(int(hwnd2))
    record["second_generation"] = backend.target_generation("probe")
    record["same_hwnd"] = int(hwnd1) == int(hwnd2)
    record["same_owner_identity"] = record["first_identity"] == record["second_identity"]
    record["generation_equal"] = record["first_generation"] == record["second_generation"]
    if record["same_hwnd"] and record["same_owner_identity"] and record["generation_equal"]:
        record["status"] = "COUNTEREXAMPLE_CONFIRMED"
    elif record["same_hwnd"]:
        record["status"] = "REUSE_OBSERVED_NO_ALIAS"
    else:
        record["status"] = "NO_REUSE_OBSERVED_IN_THIS_SINGLE_TRIAL"
except BaseException as exc:
    record["status"] = "ERROR"
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc)
finally:
    if hwnd2 and user32.IsWindow(hwnd2):
        record["second_destroy_succeeded"] = bool(user32.DestroyWindow(hwnd2))
    else:
        record["second_destroy_succeeded"] = bool(hwnd2)
    if hwnd2:
        record["second_is_window_after_destroy"] = bool(user32.IsWindow(hwnd2))
    else:
        record["second_is_window_after_destroy"] = False
    record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    RAW.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2, sort_keys=True))
if record["status"] == "ERROR" or not record.get("first_destroy_succeeded") \
        or record.get("first_is_window_after_destroy") \
        or not record.get("second_destroy_succeeded") \
        or record.get("second_is_window_after_destroy"):
    raise SystemExit(1)
