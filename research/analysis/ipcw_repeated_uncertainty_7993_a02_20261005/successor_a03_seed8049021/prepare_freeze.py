#!/usr/bin/env python3
"""Generate new A03 fixtures and hash-bind all candidate/auditor inputs."""
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import generate

ROOT = Path(__file__).parent.resolve()
PARENT = ROOT.parent
BASE = "0db00a564daff64e47fd6931954ace0f71ab8f2b"
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
SOURCES = (
    "PROTOCOL.md", "CONSTRUCTION_LOG.md", "MAIN_ADVANCEMENT.md", "generate.py", "test_protocol.py",
    "run_mount_preflight.py", "prepare_freeze.py", "PREFLIGHT.json", "preflight-stdout.txt",
    "preflight-stderr.txt", "preflight-setup-stop.stdout.txt",
    "preflight-setup-stop.stderr.txt", "preflight-output/mount-smoke.txt",
    "run_formal.py", "../candidate.py", "../auditor.py",
    "public_input.json", "oracle_input.json",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    latest = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    merge_base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    if latest != BASE or merge_base != BASE:
        raise SystemExit(f"STOP_MAIN_CHANGED expected={BASE} latest={latest} merge_base={merge_base}")
    parent_freeze = json.loads((PARENT / "FROZEN.json").read_text())
    parent_sources = parent_freeze["source_sha256"]
    for name in ("candidate.py", "auditor.py"):
        if sha(PARENT / name) != parent_sources[name]:
            raise SystemExit("STOP_PARENT_SOURCE_CHANGED:" + name)
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE,
                                    "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                                   text=True).strip()
    expected_image_id = IMAGE.split("@", 1)[1]
    if not image.startswith(expected_image_id + " linux/arm64"):
        raise SystemExit("STOP_IMAGE_IDENTITY:" + image)
    generate.write()
    frozen = {
        "allocation": "UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A03-ORBSTACK-20261005",
        "issue": 8049, "parent_issue": 7993, "predecessor_allocation": "A02_STOP_CONTAINER_CLI_MOUNT_SYNTAX",
        "base_commit": BASE, "branch": "research/8049-ht-bootstrap-a02-20261005",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "formal_seed": generate.SEED, "cohorts": generate.COHORTS,
        "population": {"stratum_units": 200, "risk": {"A": 0.40, "B": 0.10},
                       "resolution_probability": {"A": 0.25, "B": 0.75},
                       "marginal_risk": 0.25},
        "interval": {"method": "stratified exact conditional percentile bootstrap",
                     "numerator": "3*K_A+K_B", "denominator": 300,
                     "cdf_thresholds": [0.025000000001, 0.975000000001],
                     "clip_ticks": [0, 300]},
        "source_references": {"candidate": {"path": "../candidate.py", "sha256": sha(PARENT / "candidate.py")},
                              "auditor": {"path": "../auditor.py", "sha256": sha(PARENT / "auditor.py")}},
        "image": IMAGE, "image_id": image,
        "preflight_sha256": sha(ROOT / "PREFLIGHT.json"),
        "runtime": {"engine": "OrbStack Docker", "network": "none",
                    "rootfs": "read-only", "cpu_requested": 1,
                    "memory_requested": "1g", "memory_enforcement": "not asserted",
                    "candidate_oracle_mount": False, "separate_readwrite_output": True},
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
        "formal_invocations_before_freeze": {"candidate": 0, "auditor": 0, "retries": 0},
    }
    (ROOT / "FROZEN.json").write_text(json.dumps(frozen, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"freeze": "written", "base": BASE, "seed": generate.SEED,
                      "image": image, "sources": len(SOURCES), "formal_invocations": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
