#!/usr/bin/env python3
"""Run the frozen ordinary regression replay once and retain every exit."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
if RAW.exists():
    raise SystemExit(f"refusing to overwrite existing replay output: {RAW}")
RAW.mkdir(parents=True)
py = sys.executable
commands = {
    "candidate": [py, "-B", "-m", "unittest", "research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release", "-v"],
    "candidate_optimized": [py, "-B", "-O", "-m", "unittest", "research.doom.map01_v39_cancel_release_fix_a01_20261005.test_cancel_release", "-v"],
    "executor_v12": [py, "-B", "-m", "unittest", "research.doom.map01_v39_cancel_release_fix_a01_20261005.test_executor_v12_expiry_composition", "-v"],
    "owner_compatibility": [py, "-B", "research/doom/map01_v39_cancel_release_fix_a01_20261005/run_owner_compat_suite.py"],
    "v39_bridge": [py, "-B", "-m", "unittest", "discover", "-s", "research/doom/map01_v39_perkey_bridge_a01", "-p", "test_*.py", "-v"],
    "source_audit": [py, "-B", "research/doom/map01_v39_cancel_release_fix_a01_20261005/audit.py"],
}
run = {
    "python": sys.version,
    "executable": py,
    "cwd": str(ROOT),
    "commands": {},
}
for name, argv in commands.items():
    env = os.environ.copy()
    if name == "v39_bridge":
        prefix = os.pathsep.join((
            str(ROOT / "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12"),
            str(ROOT / "research/live_control"),
            str(ROOT / "research/doom"),
        ))
        env["PYTHONPATH"] = prefix + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(argv, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    (RAW / f"{name}.log").write_text(result.stdout, encoding="utf-8")
    (RAW / f"{name}.exit").write_text(f"{result.returncode}\n", encoding="ascii")
    run["commands"][name] = {"argv": argv, "exit": result.returncode}
    print(f"{name}: exit={result.returncode}")
    if result.returncode:
        print(result.stdout[-4000:])
(HERE / "RUN.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
if any(v["exit"] for v in run["commands"].values()):
    raise SystemExit(1)
