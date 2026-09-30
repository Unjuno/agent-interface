#!/usr/bin/env python3
"""Minimal Tk event recorder for the XKB refresh boundary study."""

from __future__ import annotations

import argparse
import json
import os
import time
import tkinter as tk
from pathlib import Path


def append_json(path: Path, record: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--ready", required=True, type=Path)
    parser.add_argument("--phase-file", required=True, type=Path)
    args = parser.parse_args()

    root = tk.Tk()
    root.title(f"tk-xkb-{args.label}")
    root.geometry("320x120+20+20")

    def record_event(kind: str, event: tk.Event) -> None:
        phase = args.phase_file.read_text(encoding="utf-8").strip()
        append_json(args.events, {
            "phase": phase,
            "kind": kind,
            "keysym": event.keysym,
            "char": event.char,
            "keycode": event.keycode,
            "state": event.state,
            "observed_monotonic_ns": time.monotonic_ns(),
        })

    root.bind("<KeyPress>", lambda event: record_event("press", event))
    root.bind("<KeyRelease>", lambda event: record_event("release", event))

    def publish_ready() -> None:
        root.focus_force()
        root.update_idletasks()
        append_json(args.ready, {
            "label": args.label,
            "pid": os.getpid(),
            "window_id": root.winfo_id(),
            "ready_monotonic_ns": time.monotonic_ns(),
        })

    root.after(100, publish_ready)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
