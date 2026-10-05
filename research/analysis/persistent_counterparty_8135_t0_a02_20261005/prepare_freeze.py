#!/usr/bin/env python3
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import generate

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
SOURCES = ("PROTOCOL.md", "CONSTRUCTION_LOG.md", "generate.py", "candidate.py", "audit.py", "test_protocol.py", "test_result.py", "run_mount_preflight.py", "prepare_freeze.py", "run_formal.py", "execute_formal.py", "PREFLIGHT.json", "preflight.stdout.txt", "preflight.stderr.txt")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    latest = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    if latest != base:
        raise SystemExit(f"STOP_BRANCH_NOT_ON_MAIN latest={latest} merge_base={base}")
    preflight = json.loads((ROOT/"PREFLIGHT.json").read_text())
    if preflight["exit"] != 0 or preflight["candidate_invocations"] != 0 or preflight["auditor_invocations"] != 0:
        raise SystemExit("STOP_PREFLIGHT_RECORD")
    image_id = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
    if not image_id.startswith(IMAGE.split("@", 1)[1] + " linux/arm64"):
        raise SystemExit("STOP_IMAGE_IDENTITY:" + image_id)
    d = generate.write()
    if len(d["manifest"]["blocks"]) != 40 or len(d["manifest"]["episodes"]) != 80 or len(d["truth"]["cases"]) != 80:
        raise SystemExit("STOP_FIXTURE_DENOMINATOR")
    if (ROOT/"FROZEN.json").exists() or (ROOT/"results").exists():
        raise SystemExit("STOP_ALLOCATION_NOT_EMPTY")
    frozen = {"allocation": "UNJUNO-8135-T0-A02-ORBSTACK-20261005", "issue": 8135, "predecessor": "A01_FAIL_INTEGRITY_AUDITOR_EXPECTED_SCHEMA", "schedule_seed": generate.SEED, "base_commit": latest, "branch": "research/8135-persistent-counterparty-t0-a02-20261005", "frozen_at_utc": datetime.now(timezone.utc).isoformat(), "image": IMAGE, "image_id": image_id, "runtime": {"engine": "OrbStack Docker", "network": "none", "rootfs": "read-only", "cpu_requested": 1, "memory_requested": "1g", "memory_enforcement": "not_asserted", "candidate_truth_mount": False, "separate_outputs": True}, "host": {"platform": platform.platform(), "python": platform.python_version()}, "arms": ["fresh_reset", "persistent_learner", "stationary", "frequency_sham", "persistent_null"], "routes": ["plain", "effect_boundary"], "histories": ["H_FAST", "H_CHECKED"], "blocks": 40, "episodes": 80, "sham_randomization": "balanced replication-slot sequence; independent of history, route, and truth", "hard_gate": "synthetic auditor allows only authorized positive-control proposal; all add-on proposals produce no effect", "source_sha256": {n: sha(ROOT/n) for n in SOURCES}, "manifest_sha256": sha(ROOT/"bundle/manifest.json"), "truth_sha256": sha(ROOT/"bundle/sealed_truth.json"), "formal_invocations_before_freeze": {"candidate": 0, "auditor": 0, "retries": 0}}
    (ROOT/"FROZEN.json").write_text(json.dumps(frozen, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"freeze": "written", "base": latest, "blocks": 40, "episodes": 80, "candidate_truth_mount": False, "invocations": 0}))


if __name__ == "__main__":
    main()
