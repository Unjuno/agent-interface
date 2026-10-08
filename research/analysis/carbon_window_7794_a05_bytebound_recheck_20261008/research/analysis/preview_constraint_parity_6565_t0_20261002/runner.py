#!/usr/bin/env python3
"""One-shot OrbStack runner for the frozen Issue #6565 card-parity allocation."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = "research/analysis/preview_constraint_parity_6565_t0_20261002"
ALLOCATION = "PREVIEW-CONSTRAINT-PARITY-6565-ORB-T0-20261002-01"
IMAGE = "python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
FORMAL = ROOT / "results" / "formal_01"


def call(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze_path = ROOT / "FREEZE.json"
    checksum_path = ROOT / "FREEZE.sha256"
    if not freeze_path.is_file() or not checksum_path.is_file():
        print("STOP: committed freeze receipt missing", file=sys.stderr)
        return 90
    freeze = json.loads(freeze_path.read_text())
    freeze_hash = sha(freeze_path)
    if checksum_path.read_text().split()[0] != freeze_hash:
        print("STOP: freeze checksum mismatch", file=sys.stderr)
        return 98
    marker = FORMAL / "RUN_RECORD.json"
    if marker.exists():
        print("STOP: allocation already attempted", file=sys.stderr)
        return 91
    if freeze.get("allocation") != ALLOCATION or freeze.get("image") != IMAGE:
        print("STOP: freeze identity mismatch", file=sys.stderr)
        return 92
    head = call(["git", "rev-parse", "HEAD"]).stdout.strip()
    parent = call(["git", "rev-parse", "HEAD^"]).stdout.strip()
    committed_freeze = call(["git", "show", f"HEAD:{PACKAGE}/FREEZE.json"])
    if parent != freeze.get("source_commit") or committed_freeze.returncode or \
            hashlib.sha256(committed_freeze.stdout.encode()).hexdigest() != freeze_hash:
        print("STOP: checkout does not match frozen source/freeze commits", file=sys.stderr)
        return 99
    if call(["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"]).returncode != 0:
        print("STOP: current origin/main is not an ancestor", file=sys.stderr)
        return 100
    if call(["git", "status", "--porcelain"]).stdout.strip():
        print("STOP: checkout is not clean", file=sys.stderr)
        return 101
    if call(["docker", "context", "show"]).stdout.strip() != "orbstack":
        print("STOP: non-OrbStack Docker context", file=sys.stderr)
        return 93
    inspect = call(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if inspect.returncode or inspect.stdout.strip() != freeze.get("image_id_platform"):
        print("STOP: cached image identity mismatch", file=sys.stderr)
        return 94
    for rel, expected_hash in freeze["source_sha256"].items():
        path = (ROOT.parents[2] / ".github/workflows/preview-constraint-parity-6565.yml"
                if rel == "workflow" else ROOT / rel)
        if not path.is_file() or sha(path) != expected_hash:
            print(f"STOP: source hash mismatch: {rel}", file=sys.stderr)
            return 95
    if any(path.exists() for path in (FORMAL / "candidate", FORMAL / "auditor")):
        print("STOP: output path already exists", file=sys.stderr)
        return 96
    if FORMAL.exists() and any(FORMAL.iterdir()):
        print("STOP: formal allocation path is not empty", file=sys.stderr)
        return 97
    FORMAL.mkdir(parents=True, exist_ok=True)
    (FORMAL / "candidate").mkdir()
    (FORMAL / "auditor").mkdir()

    common = ["docker", "run", "--pull", "never", "--network", "none", "--cpus", "1",
              "--memory", "256m", "--pids-limit", "64", "--read-only", IMAGE]
    candidate_name = "preview6565-candidate-formal01-20261002"
    auditor_name = "preview6565-auditor-formal01-20261002"
    for name in (candidate_name, auditor_name):
        if call(["docker", "container", "inspect", name]).returncode == 0:
            print(f"STOP: container name already exists: {name}", file=sys.stderr)
            return 102
    candidate_argv = common[:2] + ["--name", candidate_name] + common[2:-1] + [
        "--mount", f"type=bind,source={ROOT},target=/src,readonly",
        "--mount", f"type=bind,source={FORMAL / 'candidate'},target=/out",
        "--workdir", "/src", IMAGE, "python", "-B", "/src/candidate.py",
        "--out", "/out/raw.json"]
    candidate_run = call(candidate_argv)
    (FORMAL / "candidate" / "combined.log").write_text(candidate_run.stdout)
    (FORMAL / "candidate" / "exit.txt").write_text(f"{candidate_run.returncode}\n")
    candidate_inspect = call(["docker", "inspect", candidate_name])
    (FORMAL / "candidate" / "container-inspect.json").write_text(candidate_inspect.stdout + "\n")
    if candidate_run.returncode != 0 or not (FORMAL / "candidate" / "raw.json").is_file():
        print("STOP: candidate failed; auditor not launched", file=sys.stderr)
        return 20

    audit_argv = common[:2] + ["--name", auditor_name] + common[2:-1] + [
        "--mount", f"type=bind,source={ROOT},target=/src,readonly",
        "--mount", f"type=bind,source={FORMAL / 'candidate' / 'raw.json'},target=/input/raw.json,readonly",
        "--mount", f"type=bind,source={FORMAL / 'auditor'},target=/out",
        "--workdir", "/src", IMAGE, "python", "-B", "/src/auditor.py",
        "/input/raw.json", "--out", "/out/audit.json"]
    auditor_run = call(audit_argv)
    (FORMAL / "auditor" / "combined.log").write_text(auditor_run.stdout)
    (FORMAL / "auditor" / "exit.txt").write_text(f"{auditor_run.returncode}\n")
    auditor_inspect = call(["docker", "inspect", auditor_name])
    (FORMAL / "auditor" / "container-inspect.json").write_text(auditor_inspect.stdout + "\n")

    record = {
        "allocation": ALLOCATION, "source_commit": freeze["source_commit"],
        "freeze_sha256": freeze_hash, "container_context": "orbstack",
        "image": IMAGE, "image_id_platform": inspect.stdout.strip(),
        "candidate_container": candidate_name, "auditor_container": auditor_name,
        "candidate_argv": candidate_argv, "candidate_exit": candidate_run.returncode,
        "candidate_sha256": sha(FORMAL / "candidate" / "raw.json"),
        "candidate_bytes": (FORMAL / "candidate" / "raw.json").stat().st_size,
        "auditor_argv": audit_argv, "auditor_exit": auditor_run.returncode,
        "audit_sha256": sha(FORMAL / "auditor" / "audit.json") if (FORMAL / "auditor" / "audit.json").is_file() else None,
        "formal_counts": {"candidate_containers": 1, "auditor_containers": 1, "retries": 0},
    }
    (FORMAL / "RUN_RECORD.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"candidate_exit": candidate_run.returncode, "auditor_exit": auditor_run.returncode,
                      "candidate_sha256": record["candidate_sha256"],
                      "audit_sha256": record["audit_sha256"]}))
    return 0 if auditor_run.returncode == 0 else 21


if __name__ == "__main__":
    raise SystemExit(main())
