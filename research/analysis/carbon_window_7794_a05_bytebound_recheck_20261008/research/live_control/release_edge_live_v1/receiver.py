"""Independent Tk effect witness for Issue #869.

The controller never reads this log while acting. The auditor reads it only after
case completion.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import tkinter as tk


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--ready", required=True)
    args = parser.parse_args()

    root = tk.Tk()
    root.title("agent-interface-release-edge-v1")
    root.geometry("320x120+20+20")
    counts = {"press": 0, "release": 0}

    def emit(kind: str, event) -> None:
        counts[kind] += 1
        row = {
            "event": kind,
            "time_ns": time.perf_counter_ns(),
            "keysym": event.keysym,
            "keycode": event.keycode,
            "press_count": counts["press"],
            "release_count": counts["release"],
        }
        with open(args.log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    root.bind("<KeyPress-F8>", lambda event: emit("press", event))
    root.bind("<KeyRelease-F8>", lambda event: emit("release", event))
    root.update_idletasks()
    root.update()
    root.focus_force()
    root.update()
    with open(args.ready, "w", encoding="utf-8") as handle:
        handle.write(str(root.winfo_id()))
    root.after(5000, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
