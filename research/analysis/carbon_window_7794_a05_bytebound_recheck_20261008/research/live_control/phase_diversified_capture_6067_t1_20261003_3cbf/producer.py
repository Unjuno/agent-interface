"""One native visual block; exclusive outputs; no scientific retries."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

from common import await_file, write

HERE = Path(__file__).resolve().parent


def check_plan(fixture):
    headers = {"issue": 6067, "period_ms": 120, "slot_ms": 10, "source_bias_ms": 2,
               "capture_bias_ms": 5, "window_ms": 960, "cues_per_pulse_cell": 8,
               "samples_per_cell": 8, "max_gap_ms": 190, "max_lateness_ms": 10,
               "exposure_tolerance_ms": 5}
    if any(type(fixture.get(k)) is not int or fixture[k] != v for k, v in headers.items()):
        raise ValueError("fixed scientific timing/budget contract")
    arms = {"fixed": [0, 0, 0, 0], "irregular": [1, 7, 3, 9], "rotated": [0, 3, 6, 9]}
    cases = fixture["cases"]
    if len(cases) != 114 or [c["id"] for c in cases] != [f"c{i:03}" for i in range(114)]:
        raise ValueError("complete unique 114-cell order")
    pulses, controls = set(), set()
    for c in cases:
        arm = c["schedule"]
        offsets = c["offsets"]
        if arm not in arms or offsets != arms[arm] or any(type(x) is not int for x in offsets):
            raise ValueError("exact declared equal-budget arm")
        if c["kind"] == "pulse":
            if type(c["phase"]) is not int or type(c["width_ms"]) is not int:
                raise ValueError("integer phase/width")
            pulses.add((arm, c["phase"], c["width_ms"]))
        else:
            controls.add((arm, c["kind"]))
    if pulses != {(a, p, w) for a in arms for p in range(12) for w in (10, 20, 30)}:
        raise ValueError("complete matched phase-width matrix")
    if controls != {(a, k) for a in arms for k in ("dark", "persistent")}:
        raise ValueError("complete controls")


def terminal(p):
    if p is None:
        return None
    if p.poll() is None:
        p.terminate()
    try:
        return p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        p.kill()
        return p.wait(timeout=3)


def run_cell(spec, root):
    root.mkdir()
    write(root / "spec.json", spec)
    children, handles, commands = {}, [], {}
    error = None
    try:
        def spawn(name, args):
            stdout = (root / (name + ".stdout.log")).open("xb")
            stderr = (root / (name + ".stderr.log")).open("xb")
            handles.extend([stdout, stderr])
            commands[name] = args
            p = subprocess.Popen(args, stdout=stdout, stderr=stderr)
            children[name] = p
            return p
        xv = spawn("xvfb", ["Xvfb", ":93", "-screen", "0", "64x64x24", "-nolisten", "tcp", "-noreset", "-ac"])
        deadline = time.monotonic() + 3
        while not Path("/tmp/.X11-unix/X93").exists():
            if xv.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("fresh private Xvfb readiness")
            time.sleep(0.005)
        fx = spawn("fixture", [sys.executable, "-B", str(HERE / "fixture.py"),
                               "--display", ":93", "--cell", str(root / "spec.json"), "--out", str(root)])
        ready = await_file(root / "fixture-ready.json")
        ob = spawn("observer", [sys.executable, "-B", str(HERE / "observer.py"), "--display", ":93",
                               "--window", str(ready["window"]), "--offsets", json.dumps(spec["offsets"]),
                               "--out", str(root), "--epoch-file", str(root / "epoch.json")])
        await_file(root / "observer-ready.json")
        write(root / "epoch.json", {"epoch_ns": time.monotonic_ns() + 200_000_000})
        if ob.wait(timeout=4) != 0 or fx.wait(timeout=4) != 0:
            raise RuntimeError("child observation/source failure")
    except Exception:
        error = traceback.format_exc()
    finally:
        exits = {name: terminal(p) for name, p in children.items()}
        for h in handles:
            h.close()
    lifecycle = {name + "_pid": children[name].pid for name in children}
    lifecycle.update({name + "_exit": value for name, value in exits.items()})
    paths = ("source.json", "capture.json", "source.jsonl", "frames.jsonl")
    saved = {"spec": spec, "lifecycle": lifecycle, "commands": commands,
             "files_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                              for name in paths if (root / name).exists()}, "error": error}
    write(root / "cell.json", saved)
    if error is not None:
        raise RuntimeError(error)
    need_valid_execution(spec, root, lifecycle)


def need_valid_execution(spec, root, life):
    # Collector's predeclared execution gate; not the independent scientific oracle.
    if any(life.get(k) != 0 for k in ("fixture_exit", "observer_exit", "xvfb_exit")):
        raise RuntimeError("nonzero child terminal status")
    so = json.loads((root / "source.json").read_text())
    ca = json.loads((root / "capture.json").read_text())
    if len(ca["frames"]) != 8:
        raise RuntimeError("capture count")
    if any(not 0 <= f["start_ns"] - f["due_ns"] <= 10_000_000 for f in ca["frames"]):
        raise RuntimeError("capture lateness >10ms")
    if spec["kind"] == "pulse":
        for e in so["events"]:
            actual = e["clear_start_ns"] - e["draw_end_ns"]
            if abs(actual - spec["width_ms"] * 1_000_000) > 5_000_000:
                raise RuntimeError("source exposure outside width +/-5ms")
    if any(ca[k] != "00" * 32 for k in ("initial_keymap", "final_keymap")) or so["final_keymap"] != "00" * 32:
        raise RuntimeError("private keymap not neutral")
    if any(so["final_pixels"]):
        raise RuntimeError("fixture not finally clear")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--construction", action="store_true")
    group.add_argument("--formal", action="store_true")
    a = ap.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text())
    check_plan(fixture)
    mode = "construction" if a.construction else "formal"
    candidate_names = ("producer.py", "common.py", "policy.py", "x11.py", "fixture.py", "observer.py", "fixture.json")
    hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in candidate_names}
    if mode == "formal":
        freeze = json.loads((HERE / "FREEZE.json").read_text())
        if freeze["allocation"] != fixture["allocation"] or freeze["candidate_sha256"] != hashes:
            raise ValueError("prospectively frozen candidate bytes required")
    a.out.mkdir(exist_ok=False)
    if a.construction:
        cases = [{"id": "construction-dark", "kind": "dark", "schedule": "fixed", "offsets": [0]*4},
                 {"id": "construction-persistent", "kind": "persistent", "schedule": "fixed", "offsets": [0]*4}]
    else:
        cases = fixture["cases"]
    write(a.out / "consumed.json", {"allocation": fixture["allocation"], "mode": mode,
                                    "pid": os.getpid(), "started_ns": time.monotonic_ns()})
    (a.out / "cells").mkdir()
    summary = {"allocation": fixture["allocation"], "mode": mode, "cells": [], "started_cells": [],
               "source_sha256": hashes,
               "cgroups": {name: Path("/sys/fs/cgroup", name).read_text().strip()
                           for name in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")},
               "status": "STOP", "input_events": 0, "model_calls": 0}
    try:
        for i, case in enumerate(cases):
            summary["started_cells"].append(case["id"])
            run_cell(case, a.out / "cells" / case["id"])
            summary["cells"].append(case["id"])
            print(json.dumps({"completed": i+1, "planned": len(cases), "cell": case["id"]}), flush=True)
        summary["status"] = "COMPLETE"
    except Exception:
        summary["reason"] = traceback.format_exc()
    summary["finished_ns"] = time.monotonic_ns()
    write(a.out / "raw.json", summary)
    if summary["status"] != "COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
