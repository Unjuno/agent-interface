"""Frozen no-input native Win32 HWND batch reuse discriminator."""
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
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
if RAW.exists():
    raise SystemExit("raw.json already exists; refusing to repeat frozen probe")
if sys.platform != "win32":
    raise SystemExit("native Win32 probe requires Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
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

count = CONDITIONS["cohort_size"]
record = {
    "schema": "win32-hidden-hwnd-reuse-batch-receipt-v1",
    "attempt_id": CONDITIONS["attempt_id"],
    "source_commit": os.environ.get("SOURCE_COMMIT", "UNSET"),
    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "platform": platform.platform(),
    "python": sys.version,
    "input_sent": False,
    "window_activated": False,
    "status": "RUNNING",
    "first": [],
    "second": [],
    "first_cleanup": [],
    "second_cleanup": [],
}
backend = object.__new__(Win32Backend)
backend.user32 = user32
backend.kernel32 = kernel32
backend.gdi32 = gdi32
backend.advapi32 = advapi32
backend.targets = {"probe": 0}
Win32Backend._configure_api(backend)
module = kernel32.GetModuleHandleW(None)
windows: list[int] = []


def capture_row(cohort: str, index: int, hwnd: int) -> dict:
    backend.targets["probe"] = hwnd
    return {
        "cohort": cohort,
        "index": index,
        "hwnd": hwnd,
        "identity": backend._window_owner_identity_for_hwnd(hwnd),
        "generation": backend.target_generation("probe"),
    }


def create_cohort(label: str) -> list[int]:
    created: list[int] = []
    for index in range(count):
        hwnd = user32.CreateWindowExW(
            0, "STATIC", f"codex-hwnd-reuse-{label}-{index}", 0,
            0, 0, 1, 1, None, None, module, None)
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        value = int(hwnd)
        created.append(value)
        windows.append(value)
        record[label].append(capture_row(label, index, value))
    return created


def destroy_cohort(label: str, created: list[int]) -> None:
    for index, value in reversed(list(enumerate(created))):
        existed = bool(user32.IsWindow(value))
        destroyed = bool(user32.DestroyWindow(value)) if existed else False
        still_exists = bool(user32.IsWindow(value))
        record[f"{label}_cleanup"].append({
            "index": index, "hwnd": value, "was_window": existed,
            "destroy_succeeded": destroyed,
            "is_window_after_destroy": still_exists,
        })
        if value in windows:
            windows.remove(value)


first: list[int] = []
second: list[int] = []
try:
    first = create_cohort("first")
    destroy_cohort("first", first)
    second = create_cohort("second")
    first_by_hwnd = {row["hwnd"]: row for row in record["first"]}
    matches = []
    for row in record["second"]:
        prior = first_by_hwnd.get(row["hwnd"])
        if prior is not None:
            matches.append({
                "hwnd": row["hwnd"],
                "first_index": prior["index"],
                "second_index": row["index"],
                "same_identity": prior["identity"] == row["identity"],
                "same_generation": prior["generation"] == row["generation"],
                "first_generation": prior["generation"],
                "second_generation": row["generation"],
            })
    record["same_handle_matches"] = matches
    if any(not item["same_identity"] for item in matches):
        record["status"] = "INVALID_EXPERIMENT_HOLD"
    elif any(item["same_generation"] for item in matches):
        record["status"] = "COUNTEREXAMPLE_CONFIRMED"
    elif matches:
        record["status"] = "REUSED_HANDLE_DISTINGUISHED"
    else:
        record["status"] = "NO_HANDLE_REUSE_OBSERVED_IN_THIS_BATCH"
except BaseException as exc:
    record["status"] = "INVALID_EXPERIMENT_HOLD"
    record["error_type"] = type(exc).__name__
    record["error"] = str(exc)
finally:
    if second:
        destroy_cohort("second", second)
    for hwnd in list(reversed(windows)):
        if user32.IsWindow(hwnd):
            user32.DestroyWindow(hwnd)
        windows.remove(hwnd)
    record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    encoded = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    RAW.write_bytes(encoded)
    record["raw_sha256"] = hashlib.sha256(encoded).hexdigest()

print(json.dumps(record, indent=2, sort_keys=True))
if (record["status"] == "INVALID_EXPERIMENT_HOLD"
        or len(record["first"]) != count or len(record["second"]) != count
        or any(item["is_window_after_destroy"] for item in
               record["first_cleanup"] + record["second_cleanup"])):
    raise SystemExit(1)
