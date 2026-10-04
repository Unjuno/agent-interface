"""No-input Tk readiness epoch construction; no XTest import or input."""
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from readiness_once import ReadinessOnce


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def main(mode, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.geometry("520x250+80+70")
    root.title("5260-a03-no-input-" + mode)
    root.resizable(False, False)
    tk.Label(root, text="Decoy field").pack(anchor="w", padx=16, pady=(12, 0))
    decoy = tk.Entry(root, width=40)
    decoy.pack(anchor="w", padx=16)
    tk.Label(root, text="Target field").pack(anchor="w", padx=16, pady=(10, 0))
    target = tk.Entry(root, width=40)
    target.pack(anchor="w", padx=16)
    tk.Label(root, text="Not saved").pack(anchor="w", padx=16, pady=(6, 0))
    tk.Button(root, text="Save (never clicked)").pack(anchor="w", padx=16, pady=(8, 8))
    state = {"mapped": False, "configured": False, "legacy_ready_written": False}
    gate = ReadinessOnce()
    record = {"schema": "5260-a03-no-input-app-v1", "mode": mode, "pid": os.getpid(),
        "events": [], "scheduled": 0, "focus_callbacks": 0, "finalizations": 0,
        "first_ready": None, "last_ready": None, "input_events": 0}

    def log(kind):
        record["events"].append({"kind": kind, "ns": time.monotonic_ns()})

    def positive():
        return (root.winfo_ismapped() and target.winfo_ismapped() and
                min(root.winfo_width(), root.winfo_height(),
                    target.winfo_width(), target.winfo_height()) > 1)

    def focus_decoy():
        record["focus_callbacks"] += 1
        decoy.focus_force()
        log("decoy_focus_callback")

    def snapshot():
        root.update_idletasks()
        record["finalizations"] += 1
        value = {"epoch": record["finalizations"], "ready_ns": time.monotonic_ns(),
            "root_id": root.winfo_id(), "target_id": target.winfo_id(),
            "mapped": bool(root.winfo_ismapped() and target.winfo_ismapped()),
            "root_width": root.winfo_width(), "root_height": root.winfo_height(),
            "target_width": target.winfo_width(), "target_height": target.winfo_height()}
        if record["first_ready"] is None:
            record["first_ready"] = value
        record["last_ready"] = value
        write_json(out / "ready.json", value)

    def finalize():
        if mode == "FIXED":
            gate.finalize(snapshot)
        else:
            snapshot()

    def schedule():
        record["scheduled"] += 1
        log("schedule")
        root.after(50, focus_decoy)
        root.after(100, finalize)

    def retry():
        root.after(20, maybe_ready)

    def maybe_ready():
        if not (state["mapped"] and state["configured"]):
            return
        if mode == "FIXED":
            gate.prepare(root.update_idletasks, positive, retry, schedule)
        else:
            if state["legacy_ready_written"]:
                return
            # Exactly the inherited A02 claim-after-reentrant-work pattern.
            root.update_idletasks()
            if not positive():
                retry()
                return
            state["legacy_ready_written"] = True
            schedule()

    def on_map(event):
        state["mapped"] = True
        log("Map")
        maybe_ready()

    def on_configure(event):
        state["configured"] = True
        log("Configure")
        maybe_ready()

    def input_seen(event):
        record["input_events"] += 1
        log("UNEXPECTED_INPUT")

    def finish():
        record["ended_ns"] = time.monotonic_ns()
        record["target_text"] = target.get()
        record["decoy_text"] = decoy.get()
        write_json(out / "app_result.json", record)
        print(json.dumps(record, sort_keys=True), flush=True)
        root.destroy()

    root.bind("<Map>", on_map, add="+")
    root.bind("<Configure>", on_configure, add="+")
    root.bind("<KeyPress>", input_seen, add="+")
    root.bind("<ButtonPress>", input_seen, add="+")
    root.after(1000, finish)
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
