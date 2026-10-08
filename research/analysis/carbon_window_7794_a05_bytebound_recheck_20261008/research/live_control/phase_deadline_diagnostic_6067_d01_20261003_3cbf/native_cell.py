"""Fresh private display; copied source fixture; one instrumented observer."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "baseline"))
from common import await_file, write

def terminal(process):
    if process.poll() is None:
        process.terminate()
    try:
        return process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.wait(timeout=3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-json", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("construction", "diagnostic"), required=True)
    a = ap.parse_args()
    case = json.loads(a.case_json)
    if case["kind"] != "dark" or type(case["cpu"]) is not int or case["cpu"] not in (1, 2):
        raise ValueError("bounded read-only diagnostic dark case")
    if a.mode == "diagnostic":
        freeze = json.loads((HERE / "FREEZE.json").read_text())
        for name, digest in freeze["source_sha256"].items():
            if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
                raise ValueError("prospective staged source mismatch")
    a.out.mkdir(exist_ok=False)
    write(a.out / "spec.json", case)
    plan = json.loads((HERE / "plan.json").read_text())
    summary = {"status": "STOP", "mode": a.mode, "allocation": plan["allocation"],
               "case": case, "input_events": 0, "model_calls": 0, "scientific_t1_cells": 0,
               "cgroups": {n: Path("/sys/fs/cgroup", n).read_text().strip()
                           for n in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")}}
    children, commands, handles = {}, {}, []
    try:
        def spawn(name, args):
            stdout = (a.out / (name + ".stdout.log")).open("xb")
            stderr = (a.out / (name + ".stderr.log")).open("xb")
            handles.extend([stdout, stderr])
            commands[name] = args
            children[name] = subprocess.Popen(args, stdout=stdout, stderr=stderr)
            return children[name]
        xv = spawn("xvfb", ["Xvfb", ":94", "-screen", "0", "64x64x24", "-nolisten", "tcp", "-noreset", "-ac"])
        until = time.monotonic() + 3
        while not Path("/tmp/.X11-unix/X94").exists():
            if xv.poll() is not None or time.monotonic() > until:
                raise RuntimeError("private X server readiness")
            time.sleep(.005)
        fx = spawn("fixture", [sys.executable, "-B", str(HERE/"baseline/fixture.py"), "--display", ":94",
                              "--cell", str(a.out/"spec.json"), "--out", str(a.out)])
        ready = await_file(a.out/"fixture-ready.json")
        ob = spawn("observer", [sys.executable, "-B", str(HERE/"observer_trace.py"), "--display", ":94",
            "--window", str(ready["window"]), "--offsets", json.dumps(case["offsets"]), "--out", str(a.out)])
        await_file(a.out/"observer-ready.json")
        write(a.out/"epoch.json", {"epoch_ns": time.monotonic_ns() + 200_000_000})
        if ob.wait(timeout=4) != 0 or fx.wait(timeout=4) != 0:
            raise RuntimeError("child source/acquisition failure")
        summary["status"] = "COMPLETE_DIAGNOSTIC"
    except Exception:
        summary["reason"] = traceback.format_exc()
    finally:
        summary["lifecycle"] = {name+"_pid": p.pid for name, p in children.items()}
        summary["lifecycle"].update({name+"_exit": terminal(p) for name, p in children.items()})
        for handle in handles:
            handle.close()
    summary["commands"] = commands
    summary["files_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in a.out.iterdir() if p.is_file()}
    write(a.out/"cell.json", summary)
    if summary["status"] != "COMPLETE_DIAGNOSTIC" or any(v != 0 for k,v in summary["lifecycle"].items() if k.endswith("_exit")):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
