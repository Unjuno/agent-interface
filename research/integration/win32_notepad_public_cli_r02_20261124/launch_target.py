"""Create exactly one fresh Notepad document and report its native identity."""
from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path


USER32 = ctypes.WinDLL("user32", use_last_error=True)
KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
ENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
USER32.IsWindowVisible.argtypes = [wintypes.HWND]
USER32.IsWindowVisible.restype = wintypes.BOOL
USER32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
USER32.GetWindowTextLengthW.restype = ctypes.c_int
USER32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
USER32.GetWindowTextW.restype = ctypes.c_int
USER32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
USER32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
USER32.GetWindowRect.restype = wintypes.BOOL
USER32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
USER32.GetClientRect.restype = wintypes.BOOL
USER32.GetForegroundWindow.restype = wintypes.HWND
USER32.EnumWindows.argtypes = [ENUMPROC, wintypes.LPARAM]
USER32.EnumWindows.restype = wintypes.BOOL
KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
KERNEL32.OpenProcess.restype = wintypes.HANDLE
KERNEL32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
KERNEL32.QueryFullProcessImageNameW.restype = wintypes.BOOL
KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
KERNEL32.CloseHandle.restype = wintypes.BOOL


def windows_with_title(fragment: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def visit(hwnd: int, _param: int) -> bool:
        if not USER32.IsWindowVisible(hwnd):
            return True
        length = USER32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        USER32.GetWindowTextW(hwnd, title, length + 1)
        if fragment.casefold() not in title.value.casefold():
            return True
        pid = wintypes.DWORD()
        USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = wintypes.RECT()
        client = wintypes.RECT()
        USER32.GetWindowRect(hwnd, ctypes.byref(rect))
        USER32.GetClientRect(hwnd, ctypes.byref(client))
        process_path = None
        process = KERNEL32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if process:
            size = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(size.value)
            if KERNEL32.QueryFullProcessImageNameW(process, 0, path, ctypes.byref(size)):
                process_path = path.value
            KERNEL32.CloseHandle(process)
        rows.append({
            "hwnd": int(hwnd), "pid": int(pid.value), "title": title.value,
            "process_path": process_path,
            "window_rect": [rect.left, rect.top, rect.right, rect.bottom],
            "client_size": [client.right - client.left, client.bottom - client.top],
            "is_foreground": int(USER32.GetForegroundWindow()) == int(hwnd),
        })
        return True

    USER32.EnumWindows(ENUMPROC(visit), 0)
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: launch_target.py TARGET_DIR RESULT_JSON")
    target_dir = Path(sys.argv[1]).resolve()
    result_path = Path(sys.argv[2]).resolve()
    target_file = target_dir / "task-r02-6C2D9E.txt"
    notepad = Path(r"C:\Windows\System32\notepad.exe")
    target_dir.mkdir(parents=True, exist_ok=True)
    if not notepad.is_file():
        raise RuntimeError("NOTEPAD_EXECUTABLE_MISSING")
    if target_file.exists():
        raise RuntimeError("TARGET_FILE_ALREADY_EXISTS")
    if result_path.exists():
        raise RuntimeError("TARGET_RECEIPT_ALREADY_EXISTS")
    target_file.open("xb").close()
    title_fragment = target_file.name
    if windows_with_title(title_fragment):
        raise RuntimeError("TARGET_TITLE_ALREADY_OPEN")
    launcher = subprocess.Popen([str(notepad), str(target_file)], close_fds=True)
    deadline = time.monotonic() + 20
    matches: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        matches = windows_with_title(title_fragment)
        if len(matches) == 1:
            break
        if len(matches) > 1:
            raise RuntimeError("AMBIGUOUS_TARGET_WINDOW")
        time.sleep(0.1)
    if len(matches) != 1:
        raise RuntimeError("TARGET_WINDOW_NOT_FOUND")
    row = matches[0]
    if not isinstance(row["process_path"], str) or "notepad.exe" not in row["process_path"].casefold():
        raise RuntimeError("TARGET_PROCESS_IDENTITY_MISMATCH")
    if row["client_size"][0] <= 0 or row["client_size"][1] <= 0:
        raise RuntimeError("TARGET_CLIENT_GEOMETRY_INVALID")
    if target_file.stat().st_size != 0:
        raise RuntimeError("TARGET_NOT_EMPTY_BEFORE_TASK")
    result = {
        "schema": "agent-interface/win32-notepad-target-r02-v1",
        "attempt_id": "win32-notepad-public-cli-r02-20261124",
        "launcher_pid": launcher.pid,
        "target_file": str(target_file),
        "target_bytes_before": target_file.stat().st_size,
        "target_window": row,
        "captured_monotonic_ns": time.monotonic_ns(),
    }
    result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (target_dir / "targets.json").write_text(
        json.dumps({"notepad": row["hwnd"]}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
