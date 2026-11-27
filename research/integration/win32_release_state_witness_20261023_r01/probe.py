"""One-shot, input-free Win32 release-state observability diagnostic."""
from __future__ import annotations
import ctypes
import datetime as dt
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONDITIONS = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
RAW = ROOT / "raw.json"
RUN = ROOT / "run"
if RAW.exists() or RUN.exists():
    raise SystemExit("frozen output exists; refusing to repeat")
if sys.platform != "win32":
    raise SystemExit("Windows required")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.OpenInputDesktop.restype = wintypes.HANDLE
user32.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID,
                                             wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
user32.GetUserObjectInformationW.restype = wintypes.BOOL
user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
user32.GetThreadDesktop.restype = wintypes.HANDLE
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.GetCurrentProcessId.restype = wintypes.DWORD
kernel32.SetLastError.argtypes = [wintypes.DWORD]
kernel32.GetLastError.restype = wintypes.DWORD

UOI_NAME = 2
UOI_IO = 6
DESKTOP_HOOKCONTROL = 0x0008


def object_name(handle):
    needed = wintypes.DWORD()
    user32.GetUserObjectInformationW(handle, UOI_NAME, None, 0, ctypes.byref(needed))
    if not needed.value:
        return {"error": ctypes.get_last_error()}
    buffer = ctypes.create_unicode_buffer((needed.value // ctypes.sizeof(wintypes.WCHAR)) + 2)
    if not user32.GetUserObjectInformationW(handle, UOI_NAME, buffer,
                                            ctypes.sizeof(buffer), ctypes.byref(needed)):
        return {"error": ctypes.get_last_error()}
    return buffer.value


def io_flag(handle):
    value, needed = wintypes.DWORD(), wintypes.DWORD()
    if not user32.GetUserObjectInformationW(handle, UOI_IO, ctypes.byref(value),
                                            ctypes.sizeof(value), ctypes.byref(needed)):
        return {"error": ctypes.get_last_error()}
    return bool(value.value)


def raw_key_state(vk):
    kernel32.SetLastError(0)
    value = int(user32.GetAsyncKeyState(vk))
    return {"vk": vk, "raw_signed": value, "high_bit_down": bool(value & 0x8000),
            "low_bit_pressed_since_query": bool(value & 1), "last_error_after": kernel32.GetLastError()}


def main():
    record = {"schema": "win32-release-state-witness-raw-v1",
              "attempt_id": CONDITIONS["attempt_id"],
              "source_commit": CONDITIONS["source_commit"],
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "probe_pid": int(kernel32.GetCurrentProcessId()),
              "input_sent": False, "status": "UNKNOWN"}
    fixture = None
    hwnd = None
    RUN.mkdir()
    try:
        meta, events, effect = RUN / "fixture-meta.json", RUN / "events.jsonl", RUN / "effect.json"
        fixture = subprocess.Popen([sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
                                    "--meta", str(meta), "--events", str(events), "--effect", str(effect)],
                                   cwd=str(REPO), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                   text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        record["fixture_pid"] = fixture.pid
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not meta.exists():
            if fixture.poll() is not None:
                raise RuntimeError("owned fixture exited before ready")
            time.sleep(0.05)
        fixture_info = json.loads(meta.read_text(encoding="utf-8"))
        hwnd = int(fixture_info["hwnd"])
        record["fixture_hwnd"] = hwnd
        fg = int(user32.GetForegroundWindow() or 0)
        fg_pid = wintypes.DWORD()
        fg_tid = int(user32.GetWindowThreadProcessId(fg, ctypes.byref(fg_pid))) if fg else 0
        record["foreground"] = {"hwnd": fg, "pid": int(fg_pid.value), "thread_id": fg_tid,
                                 "is_fixture": fg == hwnd}
        input_desktop = user32.OpenInputDesktop(0, False, DESKTOP_HOOKCONTROL)
        record["input_desktop"] = {"opened_with_hookcontrol": bool(input_desktop),
                                    "error": ctypes.get_last_error() if not input_desktop else 0}
        current_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
        fixture_tid = int(fixture_info.get("thread_id", 0))
        fixture_desktop = user32.GetThreadDesktop(fixture_tid) if fixture_tid else None
        record["desktop_names"] = {"input": object_name(input_desktop) if input_desktop else None,
                                    "probe_thread": object_name(current_desktop) if current_desktop else None,
                                    "fixture_thread": object_name(fixture_desktop) if fixture_desktop else None}
        record["input_desktop_is_receiving_input"] = io_flag(input_desktop) if input_desktop else None
        record["async_key_state"] = [raw_key_state(vk) for vk in (0x11, 0x53, 0x01)]
        record["fixture_events_before_close"] = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        record["status"] = "RECORDED"
    except BaseException as exc:
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
    finally:
        if input_desktop if 'input_desktop' in locals() else False:
            user32.CloseDesktop(input_desktop)
        record["fixture_close_posted"] = bool(user32.PostMessageW(hwnd, 0x0010, 0, 0)) if hwnd else False
        if fixture is not None:
            try:
                fixture.wait(timeout=5)
            except subprocess.TimeoutExpired:
                record["fixture_terminate_attempted"] = True
                fixture.terminate()
                try:
                    fixture.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    record["fixture_kill_attempted"] = True
                    fixture.kill()
                    fixture.wait(timeout=2)
            record["fixture_exit_code"] = fixture.returncode
            if fixture.stderr:
                record["fixture_stderr"] = fixture.stderr.read()
                fixture.stderr.close()
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        RAW.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
