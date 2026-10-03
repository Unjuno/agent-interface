"""Disposable Tk Entry task used by the Issue #5260 private-Xvfb experiment."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from readiness_once import ReadinessOnce


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def main(out_dir, token):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.title("issue5260-disposable-entry")
    root.geometry("520x250+80+70")
    root.resizable(False, False)
    decoy_label = tk.Label(root, text="Decoy field")
    decoy_label.pack(anchor="w", padx=16, pady=(12, 0))
    decoy = tk.Entry(root, width=40)
    decoy.pack(anchor="w", padx=16)
    target_label = tk.Label(root, text="Target field")
    target_label.pack(anchor="w", padx=16, pady=(10, 0))
    target = tk.Entry(root, width=40)
    target.pack(anchor="w", padx=16)
    saved_label = tk.Label(root, text="Not saved")
    saved_label.pack(anchor="w", padx=16, pady=(6, 0))
    record = {"schema": "issue5260-tk-app-v1", "pid": os.getpid(), "token": token, "events": [],
              "payload": "hxy", "saved_text": None, "save_count": 0,
              "readiness": {"scheduled": 0, "focus_callbacks": 0, "finalizations": 0}}
    mapped = False
    configured = False
    readiness = ReadinessOnce()
    first_visual_written = False
    finished = False
    focus_sequence = 0

    def stamp(kind, widget=None, event=None):
        row = {"kind": kind, "monotonic_ns": time.monotonic_ns()}
        if widget is not None:
            row["widget"] = "target" if widget is target else ("decoy" if widget is decoy else "other")
        if event is not None:
            row["char"] = getattr(event, "char", "")
            row["keysym"] = getattr(event, "keysym", "")
            row["keycode"] = getattr(event, "keycode", None)
        record["events"].append(row)
        return row

    def write_json(path, obj):
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as stream:
            stream.write(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)

    def capture(path):
        root.update_idletasks()
        started = time.monotonic_ns()
        proc = subprocess.run(["xwd", "-silent", "-id", str(root.winfo_id())],
                              capture_output=True, timeout=3, check=False)
        if proc.returncode == 0:
            with path.open("wb") as image_file:
                image_file.write(proc.stdout)
                image_file.flush()
                os.fsync(image_file.fileno())
        ended = time.monotonic_ns()
        return {"path": path.name, "exit": proc.returncode, "stderr": proc.stderr.decode("utf-8", "replace"),
                "started_ns": started, "completed_ns": ended,
                "sha256": sha(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else 0}

    def capture_first_visual():
        nonlocal first_visual_written
        if first_visual_written:
            return
        first_visual_written = True
        frame = capture(out / "first_visual.xwd")
        try:
            x = target.winfo_x()
            y = target.winfo_y()
            width = target.winfo_width()
            height = target.winfo_height()
        except tk.TclError:
            x = y = width = height = 0
        first = {"schema": "issue5260-first-visual-v1", "widget": record.get("first_key_widget"),
                 "entry_value": target.get() if record.get("first_key_widget") == "target" else decoy.get(),
                 "target_value": target.get(), "decoy_value": decoy.get(),
                 "entry_crop": {"x": x, "y": y, "width": width, "height": height},
                 "frame": frame, "observed_ns": time.monotonic_ns()}
        record["first_visual"] = first
        write_json(out / "first_visual.json", first)

    def on_map(_event):
        nonlocal mapped
        mapped = True
        stamp("Map")
        maybe_ready()

    def on_configure(_event):
        nonlocal configured
        configured = True
        stamp("Configure")
        maybe_ready()

    def maybe_ready():
        if not (mapped and configured):
            return
        readiness.prepare(root.update_idletasks, positive_geometry,
                          lambda: root.after(20, maybe_ready), schedule_ready)

    def positive_geometry():
        rw, rh = root.winfo_width(), root.winfo_height()
        ew, eh = target.winfo_width(), target.winfo_height()
        return min(rw, rh, ew, eh) > 1 and root.winfo_ismapped() and target.winfo_ismapped()

    def focus_decoy_once():
        record["readiness"]["focus_callbacks"] += 1
        decoy.focus_force()

    def schedule_ready():
        record["readiness"]["scheduled"] += 1
        root.after(50, focus_decoy_once)
        root.after(100, finalize_ready)

    def finalize_ready():
        readiness.finalize(write_ready_once)

    def write_ready_once():
        record["readiness"]["finalizations"] += 1
        root.update_idletasks()
        geometry = {
            "root_id": root.winfo_id(), "target_id": target.winfo_id(), "decoy_id": decoy.winfo_id(),
            "root_x": root.winfo_rootx(), "root_y": root.winfo_rooty(),
            "root_width": root.winfo_width(), "root_height": root.winfo_height(),
            "target_x": target.winfo_x(), "target_y": target.winfo_y(),
            "target_root_x": target.winfo_rootx(), "target_root_y": target.winfo_rooty(),
            "target_width": target.winfo_width(), "target_height": target.winfo_height(),
            "decoy_root_x": decoy.winfo_rootx(), "decoy_root_y": decoy.winfo_rooty(),
            "decoy_width": decoy.winfo_width(), "decoy_height": decoy.winfo_height(),
            "save_root_x": save_button.winfo_rootx(), "save_root_y": save_button.winfo_rooty(),
            "save_width": save_button.winfo_width(), "save_height": save_button.winfo_height(),
        }
        frame = capture(out / "baseline.xwd")
        record["geometry"] = geometry
        record["baseline_frame"] = frame
        record["ready_ns"] = time.monotonic_ns()
        ready_snapshot = {"geometry": geometry, "token": token, "pid": os.getpid(),
            "map_configure_events": [dict(event) for event in record["events"]],
            "baseline_frame": frame, "ready_ns": record["ready_ns"],
            "readiness": dict(record["readiness"])}
        record["ready_snapshot"] = ready_snapshot
        write_json(out / "ready.json", ready_snapshot)
        root.after(1500, finish)

    def on_focus(kind, widget):
        nonlocal focus_sequence
        event = stamp(kind, widget)
        focus_sequence += 1
        label = "target" if widget is target else "decoy"
        state = {"token": token, "pid": os.getpid(), "target_id": target.winfo_id(),
                 "widget": label if kind == "FocusIn" else "none",
                 "sequence": focus_sequence, "event_ns": event["monotonic_ns"]}
        event["sequence"] = focus_sequence
        record["last_focus_state"] = state
        write_json(out / "focus_state.json", state)
        if kind == "FocusIn" and widget is target and record.get("focus_ack") is None:
            ack = {**state, "schema": "issue5260-a05-focus-ack-v1",
                   "focus_get": "target" if root.focus_get() is target else "other",
                   "written_ns": time.monotonic_ns()}
            record["focus_ack"] = ack
            write_json(out / "focus_ack.json", ack)

    def on_key(widget, event):
        stamp("KeyPress", widget, event)
        if record.get("first_key_widget") is None:
            record["first_key_widget"] = "target" if widget is target else "decoy"
            record["first_key_ns"] = time.monotonic_ns()
            root.after_idle(capture_first_visual)

    def save():
        stamp("Save", target)
        record["saved_text"] = target.get()
        record["save_count"] += 1
        saved_label.configure(text="Saved: " + record["saved_text"])
        root.after(150, finish)

    def finish():
        nonlocal finished
        if finished:
            return
        finished = True
        record["final_target"] = target.get()
        record["final_decoy"] = decoy.get()
        record["ended_ns"] = time.monotonic_ns()
        write_json(out / "app_result.json", record)
        print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
        root.destroy()

    root.bind("<Map>", on_map, add="+")
    root.bind("<Configure>", on_configure, add="+")
    for widget in (target, decoy):
        widget.bind("<FocusIn>", lambda e, w=widget: on_focus("FocusIn", w), add="+")
        widget.bind("<FocusOut>", lambda e, w=widget: on_focus("FocusOut", w), add="+")
        widget.bind("<KeyPress>", lambda e, w=widget: on_key(w, e), add="+")
    save_button = tk.Button(root, text="Save", command=save)
    save_button.pack(anchor="w", padx=16, pady=(8, 8))
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
