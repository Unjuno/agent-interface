#!/usr/bin/env python3
"""Generate formal inputs and freeze A02 sources/environment before formal run."""
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import generate

ROOT = Path(__file__).parent
BASE = "a6d12178e6ce70b178ba73c5d2d37d483fa3abda"
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
SOURCE_FILES = (
    "PROTOCOL.md", "CONSTRUCTION_LOG.md", "generate.py", "candidate.py", "auditor.py", "pilot.py",
    "PILOT_RESULTS.json", "test_protocol.py", "prepare_freeze.py",
    "public_input.json", "oracle_input.json",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    if head != BASE:
        raise SystemExit(f"STOP_BASE_MISMATCH expected={BASE} observed={head}")
    if "oracle_input" in (ROOT / "candidate.py").read_text() or "outcome_mask" in (ROOT / "candidate.py").read_text():
        raise SystemExit("STOP_CANDIDATE_ORACLE_PATH")
    generate.write()
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE,
                                     "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                                    text=True).strip()
    expected_image_id = "sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
    if not image.startswith(expected_image_id + " linux/arm64"):
        raise SystemExit("STOP_IMAGE_IDENTITY " + image)
    frozen = {
        "allocation": "UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A02-ORBSTACK-20261005",
        "issue": 8049, "parent_issue": 7993, "predecessor_pr": 8056,
        "base_commit": BASE, "branch": "research/8049-ht-bootstrap-a02-20261005",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "formal_seed": generate.SEED, "cohorts": generate.COHORTS,
        "population": {"stratum_units": 200, "risk": {"A": 0.40, "B": 0.10},
                       "resolution_probability": {"A": 0.25, "B": 0.75},
                       "marginal_risk": 0.25},
        "bootstrap": {"replicate_distribution": "exact conditional binomial product distribution",
                      "scale": "integer numerator / 300",
                      "quantile_cumulative_thresholds": [0.025000000001, 0.975000000001],
                      "clip_ticks": [0, 300]},
        "image": IMAGE, "image_id": image,
        "runtime": {"engine": "OrbStack Docker", "network": "none",
                    "source_rootfs": "read-only", "cpu_requested": 1,
                    "memory_requested": "1g", "memory_enforcement": "not asserted",
                    "candidate_truth_mount": False, "separate_rw_output": True},
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "formal_invocations_before_freeze": {"candidate": 0, "auditor": 0, "retries": 0},
    }
    (ROOT / "FROZEN.json").write_text(json.dumps(frozen, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"freeze": "written", "base": head, "image": image,
                      "source_count": len(SOURCE_FILES), "formal_invocations": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
