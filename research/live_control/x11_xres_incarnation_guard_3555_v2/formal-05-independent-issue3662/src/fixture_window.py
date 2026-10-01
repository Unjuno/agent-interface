#!/usr/bin/env python3
"""Deterministic Tk window fixture; never generates input."""
import os
import json
import tkinter as tk

root = tk.Tk()
root.title("XRes incarnation fixture")
root.geometry("240x160+80+80")
root.configure(background="#336699")
effect_path = os.environ["EFFECT_PATH"]

def apply_effect():
    try:
        with open(effect_path, encoding="utf-8") as stream:
            state = json.load(stream)
    except FileNotFoundError:
        state = {"count": 0}
    state["count"] += 1
    state["pid"] = os.getpid()
    with open(effect_path, "w", encoding="utf-8") as stream:
        json.dump(state, stream, sort_keys=True)

button = tk.Button(root, text="Apply", command=apply_effect)
button.place(x=80, y=60, width=80, height=32)
root.update_idletasks()
root.update()
print(f"READY pid={os.getpid()} xid={root.winfo_id()}", flush=True)
root.mainloop()
