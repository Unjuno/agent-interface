#!/usr/bin/env python3
"""Write the pre-formal source/input manifest; run only before formal execution."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
FILES = (
    "README.md", "CONSTRUCTION_LOG.md", "generate.py", "candidate.py", "auditor.py", "test_protocol.py",
    "prepare_freeze.py", "run_formal.py", "public_input.json", "oracle_input.json",
)


def main() -> None:
    payload = {
        "issue": 8049,
        "parent_issue": 7993,
        "subgate": "repeated-cohort IPCW uncertainty and 95% interval coverage",
        "branch": "research/7993-ipcw-repeated-uncertainty-a01-20261005",
        "base_commit": "d3a51bc4c962b223d05280225042b96a033df8bf",
        "allocation": "UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A01-ORBSTACK-20261005",
        "environment": {
            "engine": "OrbStack Docker",
            "server": "29.4.0 linux/aarch64",
            "image": "python:3.14-slim",
            "image_id": "sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151",
            "repo_digest": "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151",
            "network": "none", "cpus_requested": 1, "memory_requested": "1g",
            "source_mount": "read-only", "output_mount": "separate read-write",
            "memory_limit_enforcement": "not asserted",
        },
        "formal_invocations_before_freeze": {"candidate": 0, "auditor": 0, "driver": 0},
        "design": {"seed": 8049001, "cohorts": 20000, "units_per_cohort": 400,
                   "stratum_units": {"A": 200, "B": 200}, "risk": {"A": 0.4, "B": 0.1},
                   "resolution_probability": {"A": 0.25, "B": 0.75},
                   "ht_mean_tolerance": "4 exact Monte Carlo standard errors",
                   "ht_sd_relative_tolerance": 0.025, "ht_coverage_absolute_tolerance": 0.006,
                   "wald_z_95": 1.959963984540054},
        "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES},
    }
    (ROOT / "FROZEN.json").write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
