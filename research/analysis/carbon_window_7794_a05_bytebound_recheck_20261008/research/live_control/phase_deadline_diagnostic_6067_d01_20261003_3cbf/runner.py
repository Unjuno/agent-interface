"""Host-side one-shot private-engine orchestrator; no default Docker access."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path
import guard

HERE = Path(__file__).resolve().parent
VM = "research-6183-t0-20261003"

def write(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, sort_keys=True)
        f.write("\n")

def check_plan(plan):
    if any(type(plan.get(k)) is not int or plan[k] != v for k, v in
           {"samples_per_cell": 8, "final_spin_ns": 15_000_000,
            "epoch_lead_ns": 200_000_000, "threshold_ns": 10_000_000}.items()):
        raise ValueError("exact prospective clock/frame contract")
    conditions = [(1, "fixed", [0]*4), (1, "irregular", [1,7,3,9]),
                  (2, "fixed", [0]*4), (2, "irregular", [1,7,3,9])]
    expected = []
    for r in range(4):
        for k in range(4):
            cpu, schedule, offsets = conditions[(r+k)%4]
            expected.append({"id": f"d{len(expected):03}", "cpu": cpu,
                             "schedule": schedule, "offsets": offsets, "kind": "dark"})
    if json.dumps(plan["cells"], sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("complete balanced 16-cell contrast, exact types")

def command(plan, cell, source, output, stage):
    if type(cell["cpu"]) is not int or cell["cpu"] not in (1, 2):
        raise ValueError("CPU arm")
    return ["orbctl", "run", "-m", VM, "-u", "root", "docker", "run",
        "--pull=never", "--name", "deadline-6067-d01-3cbf-" + cell["id"],
        "--label", "owner=" + plan["owner"], "--label", "stage=" + stage,
        "--user", "501:501", "--cpus", str(cell["cpu"]),
        "--memory", "512m", "--memory-swap", "512m", "--pids-limit", "64",
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=64m",
        "--mount", "type=bind,src=" + source + ",dst=/src,readonly",
        "--mount", "type=bind,src=" + output + ",dst=/out",
        plan["image_id"], "python3", "-B", "/src/native_cell.py",
        "--case-json", json.dumps(cell, sort_keys=True), "--out", "/out/result",
        "--mode", "construction" if stage == "construction-only" else "diagnostic"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("construction", "diagnostic"), required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--guest-source", required=True)
    ap.add_argument("--guest-output-prefix", required=True)
    a = ap.parse_args()
    plan = json.loads((HERE / "plan.json").read_text())
    check_plan(plan)
    if a.mode == "diagnostic":
        freeze = json.loads((HERE / "FREEZE.json").read_text())
        for name, digest in freeze["source_sha256"].items():
            if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
                raise ValueError("published source bytes differ: " + name)
        guard.preflight(plan, freeze, a.guest_source, a.guest_output_prefix, command)
    a.out.mkdir(exist_ok=False)
    cells = plan["cells"] if a.mode == "diagnostic" else [dict(plan["cells"][1], id="construction-01")]
    summary = {"allocation": plan["allocation"], "mode": a.mode, "status": "STOP",
               "started_cells": [], "completed_cells": [], "scientific_t1_cells": 0,
               "input_events": 0, "model_calls": 0}
    write(a.out / "consumed.json", {"allocation": plan["allocation"], "mode": a.mode,
                                   "started_ns": time.monotonic_ns()})
    try:
        for c in cells:
            summary["started_cells"].append(c["id"])
            cell = a.out / c["id"]
            cell.mkdir()
            guest = a.guest_output_prefix + "-" + c["id"]
            mkdir = ["orbctl", "run", "-m", VM, "mkdir", guest]
            subprocess.run(mkdir, check=True)
            args = command(plan, c, a.guest_source, guest,
                           "construction-only" if a.mode == "construction" else "diagnostic-only")
            started = time.monotonic_ns()
            with (cell / "launch.stdout.log").open("xb") as stdout, (cell / "launch.stderr.log").open("xb") as stderr:
                run = subprocess.run(args, stdout=stdout, stderr=stderr)
            finished = time.monotonic_ns()
            inspect_args = ["orbctl", "run", "-m", VM, "-u", "root", "docker", "inspect",
                            "--format", "{{json .}}", args[args.index("--name")+1]]
            inspected = subprocess.run(inspect_args, capture_output=True, text=True)
            receipt = {"command": args, "exit_code": run.returncode, "started_ns": started,
                       "finished_ns": finished, "mkdir_command": mkdir,
                       "inspect_command": inspect_args, "inspect_exit": inspected.returncode,
                       "inspect_stdout": inspected.stdout, "inspect_stderr": inspected.stderr}
            write(cell / "launch.json", receipt)
            copy_args = ["orbctl", "run", "-m", VM, "cp", "-a", guest + "/result",
                         "/mnt/mac" + str(cell.resolve() / "record")]
            copied = subprocess.run(copy_args, capture_output=True, text=True)
            write(cell / "copy.json", {"command": copy_args, "exit": copied.returncode,
                                      "stdout": copied.stdout, "stderr": copied.stderr})
            if run.returncode != 0 or copied.returncode != 0 or inspected.returncode != 0:
                raise RuntimeError("first native/retention/inspection STOP, no replay")
            guard.check_cell(cell, c, plan)
            summary["completed_cells"].append(c["id"])
            print(json.dumps({"completed": len(summary["completed_cells"]), "planned": len(cells),
                              "id": c["id"], "cpu": c["cpu"], "schedule": c["schedule"]}), flush=True)
        summary["status"] = "COMPLETE_DIAGNOSTIC"
    except Exception:
        summary["reason"] = traceback.format_exc()
    write(a.out / "raw.json", summary)
    if summary["status"] != "COMPLETE_DIAGNOSTIC":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
