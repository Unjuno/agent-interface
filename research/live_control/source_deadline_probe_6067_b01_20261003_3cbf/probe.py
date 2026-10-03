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

from common import await_file, write

def collected(summary):
    return summary.get('status')=='COLLECTED_SOURCE_DIAGNOSTIC' and all(
        type(summary['lifecycle'].get(k)) is int and summary['lifecycle'][k]==0
        for k in ('fixture_exit','observer_exit','xvfb_exit'))

def observer_args(root, window):
    return [sys.executable,'-B',str(HERE/'observer.py'),'--display',':94','--window',str(window),
            '--offsets','[0, 0, 0, 0]','--out',str(root),'--epoch-file',str(root/'epoch.json')]

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
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    plan = json.loads((HERE / "plan.json").read_text())
    case = plan["case"]
    if json.dumps(case,sort_keys=True) != json.dumps({"id":"b000","kind":"pulse","schedule":"fixed","offsets":[0,0,0,0],"phase":0,"width_ms":20},sort_keys=True):
        raise ValueError("bounded fixed20ms source diagnostic")
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, digest in freeze["source_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            raise ValueError("prospective staged source mismatch")
    a.out.mkdir(exist_ok=False)
    write(a.out / "spec.json", case)
    plan = json.loads((HERE / "plan.json").read_text())
    summary = {"status": "STOP", "mode": "source-boundary-diagnostic", "allocation": plan["allocation"],
               "case": case, "input_events": 0, "model_calls": 0, "scientific_t1_cells": 0, "source_sha256": freeze["source_sha256"],
               "cgroups": {n: Path("/sys/fs/cgroup", n).read_text().strip()
                           for n in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")}}
    children, commands, handles = {}, {}, []
    try:
        if summary["cgroups"] != {"cpu.max":"100000 100000","memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}:
            raise ValueError("actual limits outside CPU1 diagnostic")
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
        fx = spawn("fixture", [sys.executable, "-B", str(HERE/"fixture_trace.py"), "--display", ":94",
                              "--cell", str(a.out/"spec.json"), "--out", str(a.out)])
        ready = await_file(a.out/"fixture-ready.json")
        ob = spawn("observer", observer_args(a.out,ready["window"]))
        await_file(a.out/"observer-ready.json")
        write(a.out/"epoch.json", {"epoch_ns": time.monotonic_ns() + 200_000_000})
        if ob.wait(timeout=4) != 0 or fx.wait(timeout=4) != 0:
            raise RuntimeError("child source/acquisition failure")
        summary["status"] = "COLLECTED_SOURCE_DIAGNOSTIC"
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
    if not collected(summary):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
