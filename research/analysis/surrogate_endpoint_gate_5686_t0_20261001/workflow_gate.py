#!/usr/bin/env python3
"""Fail-closed source/main/one-shot gate for the isolated Docker workflow."""
import argparse
import hashlib
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ALLOCATION = "SURROGATE-ENDPOINT-GATE-5686-T0-GHA-20261001-01"
IMAGE = "python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a"
BRANCH = "research/surrogate-endpoint-gate-5686-t0-20261001"
ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("candidate", "audit"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    freeze_path = ROOT / "research/analysis/surrogate_endpoint_gate_5686_t0_20261001/FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("allocation") != ALLOCATION or freeze.get("docker_image") != IMAGE:
        raise SystemExit("STOP_FREEZE_IDENTITY_MISMATCH")
    if os.environ.get("GITHUB_REPOSITORY") != "Unjuno/agent-interface":
        raise SystemExit("STOP_REPOSITORY_MISMATCH")
    if os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH:
        raise SystemExit("STOP_REF_MISMATCH")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise SystemExit("STOP_WORKFLOW_RERUN_NO_RETRY")
    head = os.environ.get("GITHUB_SHA", "")
    local_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    if not head or head != local_head:
        raise SystemExit("STOP_HEAD_MISMATCH")
    with Path(os.environ["GITHUB_EVENT_PATH"]).open() as stream:
        event = json.load(stream)
    if event.get("before") != "0" * 40:
        raise SystemExit("STOP_NOT_FIRST_PUSH_NO_RETRY")
    request = urllib.request.Request(
        "https://api.github.com/repos/Unjuno/agent-interface/commits/main",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "issue-5686-t0-gate"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        current_main = json.load(response)["sha"]
    if current_main != freeze.get("base_main_sha"):
        raise SystemExit("STOP_MAIN_DRIFT")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", current_main, head], cwd=ROOT, check=False)
    if ancestor.returncode:
        raise SystemExit("STOP_BRANCH_NOT_BASED_ON_FROZEN_MAIN")
    observed = {}
    for relative, expected in freeze["files_sha256"].items():
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents:
            raise SystemExit("STOP_UNSAFE_FREEZE_PATH")
        actual = sha(path)
        observed[relative] = actual
        if actual != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + relative)
    result = {
        "status": "PASS_SOURCE_GATE",
        "role": args.role,
        "allocation": ALLOCATION,
        "head_sha": head,
        "base_main_sha": current_main,
        "freeze_sha256": sha(freeze_path),
        "source_sha256": observed,
        "docker_image": IMAGE,
        "expected_platform": "linux/amd64",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PASS_SOURCE_GATE", args.role, head, current_main)


if __name__ == "__main__":
    main()
