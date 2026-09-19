"""Tiny independent Tk application used only for X11 backend integration tests."""
from __future__ import annotations
import argparse, json, tkinter as tk
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", type=Path, required=True)
    ap.add_argument("--effect", type=Path, required=True)
    ap.add_argument("--events", type=Path)
    args = ap.parse_args()

    root = tk.Tk()
    root.title("AgentInterfaceX11Fixture")
    root.geometry("400x180+80+90")
    entry = tk.Entry(root)
    entry.place(x=20, y=40, width=220, height=30)
    label = tk.Label(root, text="unsaved")
    label.place(x=20, y=90)

    def save(_event=None):
        value = entry.get()
        args.effect.write_text(json.dumps({"saved": True, "text": value}, sort_keys=True) + "\n", encoding="utf-8")
        label.config(text="saved:" + value)
        return "break"

    entry.bind("<ButtonPress-1>", lambda _event: entry.focus_force(), add="+")
    root.bind_all("<Control-s>", save)

    def log_event(event):
        if args.events is not None:
            with args.events.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"type": str(event.type), "keysym": getattr(event, "keysym", None), "char": getattr(event, "char", ""), "state": getattr(event, "state", 0), "widget": str(event.widget)}, sort_keys=True) + "\n")

    root.bind_all("<KeyPress>", log_event, add="+")
    root.bind_all("<ButtonPress-1>", log_event, add="+")
    root.update_idletasks(); root.update()
    args.meta.write_text(json.dumps({"window_id": root.winfo_id()}, sort_keys=True) + "\n", encoding="utf-8")
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
