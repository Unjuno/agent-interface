#!/usr/bin/env python3
"""Freeze source/input digests and create a candidate-inaccessible truth seal."""
import hashlib
import json
import subprocess
from pathlib import Path

from spec import exact_spec

ROOT = Path(__file__).resolve().parent
FILES = ("spec.py", "simulator.py", "candidate.py", "audit.py", "PROTOCOL.md",
         "test_construction.py", "prepare.py", "run_formal.py", "report.py", "sealed_truth.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result_dir = ROOT / "results"
    result_dir.mkdir(exist_ok=True)
    if any(result_dir.iterdir()):
        raise SystemExit("STOP: results directory is not empty")
    seal = {"strata": list(range(4)), "instances_per_stratum": 3,
            "target_rates_warm": list(exact_spec()["warm_target_rates_by_stratum"]),
            "target_rates_cold": list(exact_spec()["cold_target_rates_by_stratum"]),
            "competing_rate": exact_spec()["competing_failure_rate"]}
    (ROOT / "sealed_truth.json").write_text(json.dumps(seal, sort_keys=True, indent=2)+"\n")
    manifest = {"schema": "unjuno.issue8152.freeze.v1",
                "spec": exact_spec(), "files": {name: digest(ROOT/name) for name in FILES},
                "image": "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"}
    git_root = ROOT.parents[2]
    head = subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "HEAD"], text=True).strip()
    upstream = subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "origin/main"], text=True).strip()
    if head != upstream:
        raise SystemExit("STOP: freeze requires HEAD to equal locally fetched origin/main")
    manifest["base_commit"] = head
    (ROOT / "FREEZE.json").write_text(json.dumps(manifest, sort_keys=True, indent=2)+"\n")


if __name__ == "__main__":
    main()
