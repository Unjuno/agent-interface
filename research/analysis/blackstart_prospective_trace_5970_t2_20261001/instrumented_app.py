#!/usr/bin/env python3
"""Additive test copy of archived X11/Tk app with explicit actuation IDs."""
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
state_path = out / "state.json"
events_path = out / "app_events.jsonl"
root = tk.Tk()
root.geometry("360x120+40+40")
root.title("reconnect-key-state-instrumented")
var = tk.StringVar(value="")
ent = tk.Entry(root, textvariable=var, font=("TkFixedFont", 18))
ent.pack(fill="both", expand=True, padx=10, pady=10)
pending_id = None
source_seq = 0
control_seq = 0
commands = queue.Queue()


def append(path, obj):
    with path.open("a", encoding="utf-8", buffering=1) as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")


def atomic(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def snap(reason):
    root.update_idletasks()
    atomic(
        state_path,
        {
            "pid": os.getpid(),
            "root_xid": root.winfo_id(),
            "entry_xid": ent.winfo_id(),
            "value": var.get(),
            "focus_widget": str(root.focus_get()),
            "reason": reason,
            "mono_ns": time.monotonic_ns(),
        },
    )


def read_commands():
    for line in sys.stdin:
        commands.put(line.rstrip("\n"))


def poll_commands():
    global pending_id, control_seq
    while True:
        try:
            command = commands.get_nowait()
        except queue.Empty:
            break
        control_seq += 1
        if command == "stop":
            root.after_idle(root.destroy)
        elif command.startswith("arm:") and pending_id is None:
            pending_id = command[4:]
            append(
                events_path,
                {
                    "kind": "arm_ack",
                    "consumer": "app",
                    "control_seq": control_seq,
                    "actuation_id": pending_id,
                    "mono_ns": time.monotonic_ns(),
                },
            )
        else:
            append(
                events_path,
                {
                    "kind": "arm_reject",
                    "consumer": "app",
                    "control_seq": control_seq,
                    "command": command,
                    "pending_id": pending_id,
                    "mono_ns": time.monotonic_ns(),
                },
            )
    root.after(2, poll_commands)


def ev(kind, event):
    global pending_id, source_seq
    source_seq += 1
    action_id = pending_id
    pending_id = None
    append(
        events_path,
        {
            "kind": kind,
            "source": "app",
            "source_seq": source_seq,
            "event_id": f"app:{source_seq}",
            "actuation_id": action_id,
            "causal_parent_ids": [f"act:{action_id}"] if action_id else [],
            "keysym": event.keysym,
            "keycode": int(event.keycode),
            "state": int(event.state),
            "x_time": int(event.time),
            "mono_ns": time.monotonic_ns(),
            "value": var.get(),
        },
    )
    root.after_idle(lambda: snap("event"))


ent.bind("<KeyPress>", lambda e: ev("KeyPress", e), add="+")
ent.bind("<KeyRelease>", lambda e: ev("KeyRelease", e), add="+")
var.trace_add("write", lambda *_: root.after_idle(lambda: snap("trace")))
root.after(100, lambda: (ent.focus_force(), snap("ready")))
root.after(2, poll_commands)
threading.Thread(target=read_commands, daemon=True).start()
root.protocol("WM_DELETE_WINDOW", root.destroy)
try:
    root.mainloop()
finally:
    try:
        snap("closing")
    except Exception:
        pass
