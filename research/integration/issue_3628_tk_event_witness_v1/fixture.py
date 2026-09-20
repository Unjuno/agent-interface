"""Construction fixture with a passive KeyPress witness before Tk class bindings."""
from __future__ import annotations

import argparse
import json
import time
import tkinter as tk
from pathlib import Path


def configure_fixture(root: tk.Tk, effect_path: Path, events_path: Path) -> tk.Entry:
    root.title("AgentInterfaceX11Fixture")
    root.geometry("400x180+80+90")
    entry = tk.Entry(root)
    entry.place(x=20, y=40, width=220, height=30)
    label = tk.Label(root, text="unsaved")
    label.place(x=20, y=90)

    def save(_event: tk.Event | None = None) -> str:
        value = entry.get()
        effect_path.write_text(
            json.dumps(
                {
                    "saved": True,
                    "text": value,
                    "save_callback_monotonic_ns": time.monotonic_ns(),
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        label.config(text="saved:" + value)
        return "break"

    def focus_entry(_event: tk.Event) -> None:
        entry.focus_force()

    entry.bind("<ButtonPress-1>", focus_entry, add="+")

    def log_key(event: tk.Event) -> None:
        row = {
            "type": str(event.type),
            "keysym": getattr(event, "keysym", None),
            "char": getattr(event, "char", ""),
            "state": int(getattr(event, "state", 0)),
            "widget": str(event.widget),
            "monotonic_ns": time.monotonic_ns(),
        }
        with events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
        # Deliberately return None: this witness must not consume the event.

    witness_tag = "AgentInterfacePassiveKeyWitness"
    root.bind_class(witness_tag, "<KeyPress>", log_key, add="+")
    tags = list(entry.bindtags())
    class_index = tags.index(entry.winfo_class())
    tags.insert(class_index, witness_tag)
    entry.bindtags(tuple(tags))

    root.bind_all("<Control-s>", save)

    def log_button(event: tk.Event) -> None:
        row = {
            "type": str(event.type),
            "keysym": getattr(event, "keysym", None),
            "char": getattr(event, "char", ""),
            "state": int(getattr(event, "state", 0)),
            "widget": str(event.widget),
            "monotonic_ns": time.monotonic_ns(),
        }
        with events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    root.bind_all("<ButtonPress-1>", log_button, add="+")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    args = parser.parse_args()

    root = tk.Tk()
    entry = configure_fixture(root, args.effect, args.events)
    root.update_idletasks()
    root.update()
    args.meta.write_text(
        json.dumps(
            {
                "window_id": root.winfo_id(),
                "bindtags": list(entry.bindtags()),
                "witness_tag": "AgentInterfacePassiveKeyWitness",
                "witness_precedes_class": entry.bindtags().index(
                    "AgentInterfacePassiveKeyWitness"
                )
                < entry.bindtags().index(entry.winfo_class()),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
