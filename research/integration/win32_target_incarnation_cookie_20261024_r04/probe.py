"""One-shot no-input Win32 shared-marker lifecycle probe."""
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
from runtime.backends.win32_v1.backend import (
    TARGET_INCARNATION_PROPERTY, Win32Backend,
)

RAW = ROOT / "raw.json"
if RAW.exists():
    raise SystemExit("raw.json already exists; refusing to repeat frozen probe")
if sys.platform != "win32":
    raise SystemExit("native Win32 probe requires Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
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
user32.GetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.GetPropW.restype = wintypes.HANDLE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

record = {
    "schema": "win32-target-incarnation-cookie-shared-lifecycle-probe-v1",
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "platform": platform.platform(),
    "python": sys.version,
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "actions": ["create_hidden_owned_static_window", "read_generation",
                "open_second_backend_and_read_shared_generation",
                "close_first_backend", "verify_second_backend_still_works",
                "close_second_backend", "verify_property_until_window_destroy",
                "destroy_owned_window", "verify_property_removed_by_os"],
    "input_sent": False,
    "window_activated": False,
    "targeted_existing_user_window": False,
    "status": "RUNNING",
}
hwnd = None
backend = None
try:
    hwnd = user32.CreateWindowExW(
        0, "STATIC", "codex-target-incarnation-probe", 0,
        0, 0, 1, 1, None, None, kernel32.GetModuleHandleW(None), None)
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())
    record["hwnd"] = int(hwnd)
    record["is_window_after_create"] = bool(user32.IsWindow(hwnd))

    backend = object.__new__(Win32Backend)
    backend.user32 = user32
    backend.kernel32 = kernel32
    backend.advapi32 = advapi32
    backend.gdi32 = gdi32
    backend.targets = {"probe": int(hwnd)}
    Win32Backend._configure_api(backend)
    backend._target_incarnation_bindings = {}
    backend._closed = False
    backend._close_report = None
    record["generation_first"] = backend.target_generation("probe")
    second_backend = object.__new__(Win32Backend)
    second_backend.user32 = user32
    second_backend.kernel32 = kernel32
    second_backend.advapi32 = advapi32
    second_backend.gdi32 = gdi32
    second_backend.targets = {"probe": int(hwnd)}
    Win32Backend._configure_api(second_backend)
    second_backend._target_incarnation_bindings = {}
    second_backend._closed = False
    second_backend._close_report = None
    record["generation_second_backend"] = second_backend.target_generation("probe")
    property_value = user32.GetPropW(hwnd, TARGET_INCARNATION_PROPERTY)
    record["native_property_present"] = bool(property_value)
    record["native_property_value"] = int(property_value or 0)
    record["close_report"] = backend.close()
    record["native_property_after_first_close"] = int(
        user32.GetPropW(hwnd, TARGET_INCARNATION_PROPERTY) or 0)
    record["second_backend_generation_after_first_close"] = (
        second_backend.target_generation("probe"))
    record["second_close_report"] = second_backend.close()
    record["native_property_after_both_close"] = int(
        user32.GetPropW(hwnd, TARGET_INCARNATION_PROPERTY) or 0)
    record["status"] = (
        "PASS" if record["is_window_after_create"]
        and record["generation_first"] == record["generation_second_backend"]
        and record["generation_first"] == record["second_backend_generation_after_first_close"]
        and record["native_property_present"]
        and record["close_report"].get("status") == "closed"
        and record["close_report"]["property_cleanup"][0]["status"]
        == "retained_until_window_destroyed"
        and record["second_close_report"].get("status") == "closed"
        and record["second_close_report"]["property_cleanup"][0]["status"]
        == "retained_until_window_destroyed"
        and record["native_property_after_first_close"] == int(property_value)
        and record["native_property_after_both_close"] == int(property_value)
        else "FAIL")
except BaseException as exc:
    record["status"] = "ERROR"
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc)
finally:
    if hwnd:
        record["destroy_succeeded"] = bool(user32.DestroyWindow(hwnd))
        record["is_window_after_destroy"] = bool(user32.IsWindow(hwnd))
        record["native_property_after_destroy"] = int(
            user32.GetPropW(hwnd, TARGET_INCARNATION_PROPERTY) or 0)
        record["property_removed_by_window_destroy"] = (
            record["native_property_after_destroy"] == 0)
        if (record["status"] == "PASS" and
                record["property_removed_by_window_destroy"] is not True):
            record["status"] = "FAIL"
    record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    encoded = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    RAW.write_bytes(encoded)
    record["raw_sha256"] = hashlib.sha256(encoded).hexdigest()
print(json.dumps(record, indent=2, sort_keys=True))
if record["status"] != "PASS" or not record.get("destroy_succeeded") \
        or record.get("is_window_after_destroy") \
        or not record.get("property_removed_by_window_destroy"):
    raise SystemExit(1)
