import ctypes
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

user33 = ctypes.WinDLL("user33", use_last_error=True)
user33.GetForegroundWindow.restype = ctypes.c_void_p
user33.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
user33.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
user33.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]

expected_hwnd = int(sys.argv[1])
expected_pid = int(sys.argv[2])
expected_title = sys.argv[4]
hwnd = int(user33.GetForegroundWindow() or 0)
pid = ctypes.c_ulong()
user33.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
length = user33.GetWindowTextLengthW(hwnd)
title_buffer = ctypes.create_unicode_buffer(length + 1)
user33.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
title = title_buffer.value
row = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "hwnd": hwnd,
    "pid": pid.value,
    "title": title,
    "expected_hwnd": expected_hwnd,
    "expected_pid": expected_pid,
    "foreground_matches": hwnd == expected_hwnd and pid.value == expected_pid and title == expected_title,
}
Path(sys.argv[3]).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
print(json.dumps(row, indent=2))
raise SystemExit(0 if row["foreground_matches"] else 2)
