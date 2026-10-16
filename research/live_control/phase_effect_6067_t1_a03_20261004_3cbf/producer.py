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
from reference import check_fixture_plan
from protocol import cases_for, admit_stage
from cell_validation import validate_cell

HERE = Path(__file__).resolve().parent


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
    paths = sorted(p.name for p in root.iterdir() if p.is_file() and p.name != "cell.json")
    saved = {"spec": spec, "lifecycle": lifecycle, "commands": commands,
             "files_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                              for name in paths if (root / name).exists()}, "error": error}
    write(root / "cell.json", saved)
    if error is not None:
        raise RuntimeError(error)
    return need_valid_execution(spec, root, lifecycle)


def need_valid_execution(spec, root, life):
    def journal(name):
        from reference import parse_record
        return [parse_record(s) for s in (root/name).read_text().splitlines()]
    from reference import read
    return validate_cell(spec, {'source':read(root/'source.json'),
        'capture':read(root/'capture.json'), 'lifecycle':life,
        'source_journal':journal('source.jsonl'), 'source_waits':journal('source-waits.jsonl'),
        'frames':journal('frames.jsonl'), 'observer_waits':journal('waits.jsonl')})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", choices=("readiness","formal"), required=True)
    ap.add_argument("--freeze", type=Path, required=True)
    a = ap.parse_args()
    from reference import read
    fixture = read(HERE/"fixture.json")
    freeze = read(a.freeze)
    mode = a.mode
    hashes = {name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
              for name in freeze["source_sha256"]}
    readiness_bytes=(HERE/'readiness-RESULT.json').read_bytes() if mode=='formal' else None
    admit_stage(freeze, mode, hashes, fixture,readiness_bytes)
    allocation = freeze["allocation"]
    cases = cases_for(mode, fixture)
    a.out.mkdir(exist_ok=False)
    write(a.out / "consumed.json", {"allocation": allocation, "mode": mode,
                                    "pid": os.getpid(), "started_ns": time.monotonic_ns()})
    (a.out / "cells").mkdir()
    summary = {"allocation": allocation, "mode": mode, "cells": [], "started_cells": [],
               "source_sha256": hashes,
               "cgroups": {name: Path("/sys/fs/cgroup", name).read_text().strip()
                           for name in ("cpu.max", "memory.max", "memory.swap.max", "pids.max")},
               "status": "STOP", "input_events": 0, "model_calls": 0}
    try:
        if summary['cgroups'] != {'cpu.max': '100000 100000', 'memory.max': '536870912',
                                  'memory.swap.max': '0', 'pids.max': '64'}:
            raise RuntimeError('actual cgroup limits outside frozen CPU1 contract')
        for i, case in enumerate(cases):
            summary["started_cells"].append(case["id"])
            qualified=run_cell(case, a.out / "cells" / case["id"])
            if mode=='readiness':
                expected=[] if case['kind']=='dark' else [1] if case['kind']=='persistent' else list(range(1,9))
                if (qualified['stable_ids']!=expected or qualified['boundary_hits']!=0 or
                        qualified['unknown_frames']!=0):
                    raise ValueError('readiness stable source/capture qualification')
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
