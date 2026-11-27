"""Request normal WM_CLOSE for only the exact experiment-owned Notepad HWND."""
from __future__ import annotations

import ctypes
import json
import sys
import time
from pathlib import Path
from ctypes import wintypes

from launch_target import windows_with_title

USER32 = ctypes.WinDLL("user32", use_last_error=True)
USER32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
USER32.PostMessageW.restype = wintypes.BOOL
WM_CLOSE = 0x0010


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: close_target.py LAUNCH_RECEIPT OUTPUT_JSON")
    launch = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    if output.exists():
        raise RuntimeError("CLOSE_RECEIPT_ALREADY_EXISTS")
    expected = launch["target_window"]
    title_fragment = Path(launch["target_file"]).name
    matches = windows_with_title(title_fragment)
    exact = [row for row in matches
             if row.get("hwnd") == expected.get("hwnd")
             and row.get("pid") == expected.get("pid")]
    requested = False
    if len(exact) == 1:
        requested = bool(USER32.PostMessageW(expected["hwnd"], WM_CLOSE, 0, 0))
    deadline = time.monotonic() + 10
    while requested and time.monotonic() < deadline:
        if not any(row.get("hwnd") == expected.get("hwnd")
                   for row in windows_with_title(title_fragment)):
            break
        time.sleep(0.1)
    remaining = [row for row in windows_with_title(title_fragment)
                 if row.get("hwnd") == expected.get("hwnd")]
    row = {
        "schema": "agent-interface/win32-notepad-close-r01-v1",
        "hwnd": expected.get("hwnd"),
        "pid": expected.get("pid"),
        "wm_close_requested": requested,
        "window_absent_after_close": not remaining,
        "remaining": remaining,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(row, sort_keys=True))
    return 0 if requested and not remaining else 1


if __name__ == "__main__":
    raise SystemExit(main())
