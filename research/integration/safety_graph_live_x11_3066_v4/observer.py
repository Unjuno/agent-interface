from __future__ import annotations

import argparse
import json
import os
import signal
import time
from pathlib import Path

from Xlib import X, display

running = True


def stop(_signum, _frame):
    global running
    running = False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", required=True)
    parser.add_argument("--events", required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, stop)
    d = display.Display()
    root = d.screen().root
    win = root.create_window(
        40, 40, 240, 120, 0, X.CopyFromParent, X.InputOutput,
        X.CopyFromParent, background_pixel=0xFFFFFF,
        event_mask=X.KeyPressMask | X.KeyReleaseMask,
    )
    win.set_wm_name("AgentInterfaceSafety3066V4")
    win.set_wm_class("agent-interface-safety-3066-v4", "AgentInterfaceSafety3066V4")
    win.map()
    d.sync()
    Path(args.meta).write_text(json.dumps({
        "window_id": win.id, "pid": os.getpid(), "mapped_ns": time.monotonic_ns(),
    }, sort_keys=True) + "\n")
    try:
        with Path(args.events).open("a", encoding="utf-8") as out:
            while running:
                if not d.pending_events():
                    time.sleep(0.001)
                    continue
                event = d.next_event()
                if event.type not in (X.KeyPress, X.KeyRelease):
                    continue
                row = {
                    "kind": "press" if event.type == X.KeyPress else "release",
                    "keycode": event.detail,
                    "server_time": event.time,
                    "monotonic_ns": time.monotonic_ns(),
                    "window_id": win.id,
                }
                out.write(json.dumps(row, sort_keys=True) + "\n")
                out.flush()
    finally:
        d.close()
        Path(args.meta).with_suffix(".exit.json").write_text(json.dumps({
            "pid": os.getpid(), "exit_ns": time.monotonic_ns(), "reason": "SIGTERM_or_parent_cleanup",
        }, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
