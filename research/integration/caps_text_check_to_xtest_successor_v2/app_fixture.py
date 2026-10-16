"""Independent Tk Entry recipient for successor construction probes."""
from __future__ import annotations

import json
import os
import sys
import time
import tkinter as tk
from pathlib import Path

log = Path(sys.argv[1]).open("x", encoding="utf-8")


def emit(kind: str, **fields):
    row = {"event": kind, "ns": time.monotonic_ns(), "pid": os.getpid(), **fields}
    log.write(json.dumps(row, sort_keys=True) + "\n")
    log.flush()
    return row


root = tk.Tk()
root.geometry("440x140+20+20")
value = tk.StringVar()
entry = tk.Entry(root, textvariable=value)
entry.pack(padx=20, pady=35)
value.trace_add("write", lambda *_: emit("value", value=value.get()))
for name in ("KeyPress", "KeyRelease"):
    entry.bind("<" + name + ">", lambda e, kind=name: emit(
        kind, keysym=e.keysym, keycode=e.keycode, state=e.state, char=e.char
    ), add="+")


def answer(command: str) -> None:
    row = emit("snapshot", command=command, value=value.get())
    print(json.dumps(row, sort_keys=True), flush=True)
    if command == "close":
        root.destroy()


def read_command(*_args) -> None:
    line = sys.stdin.readline()
    if not line:
        root.destroy()
        return
    command = json.loads(line)["command"]
    if command not in ("snapshot", "close"):
        raise ValueError("bad fixture command")
    root.after(30, lambda: answer(command))


root.createfilehandler(sys.stdin, tk.READABLE, read_command)
root.update()
entry.focus_force()
root.update()
print(json.dumps(emit("ready", window=entry.winfo_id(), root=root.winfo_id())), flush=True)
root.mainloop()
emit("exit", value=value.get())
log.close()
