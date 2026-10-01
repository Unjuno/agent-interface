import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
from Xlib import X, display
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


OUT = Path("/out")
WIDTH, HEIGHT = 320, 180
COMMON_LABEL = "FIXTURE ITEM"
BASE = [("base-target", "#22cc44", 1), ("base-other", "#2244cc", 0)]
EVAL = [("shift-target", "#55dd66", 1), ("shift-other", "#5566dd", 0)]
SEEDS = [40, 41, 42, 43, 44]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def configure_window():
    Gtk.init([])
    win = Gtk.Window()
    win.set_decorated(False)
    win.set_resizable(False)
    win.set_default_size(WIDTH, HEIGHT)
    label = Gtk.Label(label=COMMON_LABEL)
    win.add(label)
    css = Gtk.CssProvider()
    win.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    win.show_all()
    for _ in range(12):
        Gtk.main_iteration_do(False)
    return win, label, css


def capture(win, label, css, color, d):
    css.load_from_data(("* { background-color: %s; color: #ffffff; }" % color).encode())
    label.set_text(COMMON_LABEL)
    label.show()
    for _ in range(8):
        Gtk.main_iteration_do(False)
    win.get_window().process_all_updates()
    d.sync()
    raw = d.screen().root.get_image(0, 0, WIDTH, HEIGHT, X.ZPixmap, 0xFFFFFFFF)
    frame = np.frombuffer(raw.data, dtype=np.uint8)[:WIDTH * HEIGHT * 4].reshape(HEIGHT, WIDTH, 4)[:, :, :3].copy()
    return frame


def forward(x, w, b):
    return 1.0 / (1.0 + np.exp(-np.clip(x @ w + b, -30.0, 30.0)))


def preflight():
    win, label, css = configure_window()
    d = display.Display()
    frame = capture(win, label, css, BASE[0][1], d)
    result = {"state": "PASS_X11_CONSTRUCTION", "shape": list(frame.shape),
              "label": label.get_text(), "window_size": list(win.get_size()),
              "label_size": [label.get_allocation().width, label.get_allocation().height],
              "frame_sha256": sha(frame.tobytes()), "display": os.environ.get("DISPLAY"),
              "python": platform.python_version(), "numpy": np.__version__,
              "gtk": [Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()]}
    win.destroy()
    d.close()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "construction.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


def formal():
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise RuntimeError("fresh_output_not_empty")
    win, label, css = configure_window()
    d = display.Display()
    captures = {}
    layout = None
    for name, color, y in BASE:
        frames = []
        for _ in range(8):
            frame = capture(win, label, css, color, d)
            frames.append(frame)
            current_layout = [label.get_text(), list(win.get_size()),
                              label.get_allocation().width, label.get_allocation().height]
            if layout is None:
                layout = current_layout
            if current_layout != layout:
                raise RuntimeError("label_or_layout_changed")
        captures[name] = np.stack(frames)
    base_x = np.concatenate([captures[name].reshape(8, -1) for name, _, _ in BASE], axis=0).astype(np.float32) / 255.0
    base_y = np.concatenate([np.full(8, y, dtype=np.float32) for _, _, y in BASE])
    shifted = {}
    for name, color, _ in EVAL:
        shifted[name] = capture(win, label, css, color, d)

    rows, all_weights, all_biases, losses = [], [], [], []
    start_all = time.perf_counter_ns()
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        w = rng.normal(0.0, 0.02, size=base_x.shape[1]).astype(np.float32)
        b = 0.0
        loss_trace = []
        for _ in range(100):
            p = forward(base_x, w, b)
            grad = (p - base_y) / len(base_y)
            w -= np.float32(0.3) * (base_x.T @ grad).astype(np.float32)
            b -= float(np.float32(0.3) * grad.sum())
            p = np.clip(forward(base_x, w, b), 1e-7, 1 - 1e-7)
            loss_trace.append(float(-np.mean(base_y * np.log(p) + (1 - base_y) * np.log(1 - p))))
        all_weights.append(w)
        all_biases.append(b)
        losses.append(loss_trace)
        for name, _, ytrue in EVAL:
            frame = shifted[name]
            x = frame.reshape(-1).astype(np.float32) / 255.0
            t0 = time.perf_counter_ns()
            prob = float(forward(x, w, b))
            pred_ns = time.perf_counter_ns() - t0
            rows.append({"seed": seed, "case": name, "expected_target": bool(ytrue),
                         "p_target": prob, "predicted_target": bool(prob >= 0.5),
                         "correct": bool((prob >= 0.5) == bool(ytrue)),
                         "threshold_pass": bool(prob >= 0.75) if ytrue else bool(prob < 0.5),
                         "frame_sha256": sha(frame.tobytes()), "prediction_ns": pred_ns})
    elapsed = time.perf_counter_ns() - start_all
    frame_hashes = {name: [sha(f.tobytes()) for f in frames] for name, frames in captures.items()}
    frame_hashes.update({name: [sha(frame.tobytes())] for name, frame in shifted.items()})
    result = {
        "allocation": "gtk-label-cue-ablation-2599-20260927-01",
        "label": COMMON_LABEL, "layout": layout, "colors": {n: c for n, c, _ in BASE + EVAL},
        "base_capture_count": int(sum(len(v) for v in captures.values())),
        "base_frame_hashes": frame_hashes,
        "unique_base_hashes_by_class": {n: sorted(set(frame_hashes[n])) for n, _, _ in BASE},
        "seeds": SEEDS, "train_rows_per_class": 8, "gradient_steps": 100,
        "learning_rate": 0.3, "input_dims": int(base_x.shape[1]),
        "rows": rows, "weights_sha256": [sha(w.tobytes()) for w in all_weights],
        "biases": all_biases,
        "loss_first_last": [[trace[0], trace[-1]] for trace in losses],
        "all_finite": bool(np.isfinite(np.asarray(all_weights)).all() and np.isfinite(np.asarray(losses)).all()),
        "accuracy": float(np.mean([r["correct"] for r in rows])),
        "threshold_pass_count": int(sum(r["threshold_pass"] for r in rows)),
        "training_wall_ns": elapsed,
        "python": platform.python_version(), "numpy": np.__version__,
        "gtk": [Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version()],
    }
    np.savez_compressed(OUT / "raw_frames_and_weights.npz",
                        base_target=captures["base-target"], base_other=captures["base-other"],
                        shift_target=shifted["shift-target"], shift_other=shifted["shift-other"],
                        weights=np.stack(all_weights), biases=np.asarray(all_biases, dtype=np.float32))
    (OUT / "formal-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": result["allocation"], "accuracy": result["accuracy"],
                      "threshold_pass_count": result["threshold_pass_count"],
                      "base_capture_count": result["base_capture_count"],
                      "label": result["label"], "training_wall_ns": elapsed}, sort_keys=True))
    win.destroy()
    d.close()


if __name__ == "__main__":
    if "--preflight" in sys.argv:
        preflight()
    elif "--formal" in sys.argv:
        formal()
    else:
        raise SystemExit("expected --preflight or --formal")

