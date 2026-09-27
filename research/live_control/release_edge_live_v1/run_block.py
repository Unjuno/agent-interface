"""Frozen 12-case block for Issue #869.

Do not run while freeze.json says formal_authorized=false.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "freeze.json").read_text())


def main() -> None:
    if not FREEZE.get("formal_authorized", False):
        raise RuntimeError("formal allocation blocked by freeze.json; resolve Issue #60 formal/live lease first")
    if FREEZE["formal_invocation_budget"] != 1 or FREEZE["same_id_rerun_budget"] != 0:
        raise RuntimeError("unexpected formal budget")

    out = HERE / "results" / "release-edge-live-x11-01"
    if out.exists():
        raise RuntimeError(f"formal output already exists: {out}")
    out.mkdir(parents=True)
    manifest = {
        "task": FREEZE["task"],
        "started_ns": time.perf_counter_ns(),
        "schedule": FREEZE["schedule"],
        "cases": [],
        "formal_invocations": 1,
        "reruns": 0,
        "case_runner": "run_case_v2.py",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))

    for index, (case_id, arm) in enumerate(FREEZE["schedule"]):
        case_out = out / case_id
        command = [
            sys.executable,
            str(HERE / "run_case_v2.py"),
            "--case-id",
            case_id,
            "--arm",
            arm,
            "--display-number",
            str(430 + index),
            "--out",
            str(case_out),
        ]
        completed = subprocess.run(command, cwd=HERE, text=True, capture_output=True)
        manifest["cases"].append({
            "case_id": case_id,
            "arm": arm,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
        if completed.returncode != 0:
            manifest["stopped_after_case"] = case_id
            manifest["finished_ns"] = time.perf_counter_ns()
            (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
            raise SystemExit(completed.returncode)

    manifest["finished_ns"] = time.perf_counter_ns()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
