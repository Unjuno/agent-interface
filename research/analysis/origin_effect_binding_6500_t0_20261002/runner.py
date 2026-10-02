#!/usr/bin/env python3
"""One-shot OrbStack candidate/auditor launcher for Issue #6500 T0."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = "research/analysis/origin_effect_binding_6500_t0_20261002"
ALLOCATION = "ORIGIN-EFFECT-BINDING-6500-ORB-T0-20261002-01"
IMAGE = "python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
FORMAL = ROOT / "results" / "formal_01"


def call(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze_path = ROOT / "FREEZE.json"
    sidecar = ROOT / "FREEZE.sha256"
    if not freeze_path.is_file() or not sidecar.is_file():
        print("STOP: committed freeze missing", file=sys.stderr)
        return 90
    freeze = json.loads(freeze_path.read_text())
    freeze_hash = sha(freeze_path)
    if sidecar.read_text().split()[0] != freeze_hash:
        print("STOP: freeze checksum mismatch", file=sys.stderr)
        return 91
    if freeze.get("allocation") != ALLOCATION or freeze.get("image") != IMAGE:
        print("STOP: allocation or image mismatch", file=sys.stderr)
        return 92
    if FORMAL.exists() and any(FORMAL.iterdir()):
        print("STOP: allocation already attempted or output path nonempty", file=sys.stderr)
        return 93
    head = call(["git", "rev-parse", "HEAD"]).stdout.strip()
    parent = call(["git", "rev-parse", "HEAD^"]).stdout.strip()
    committed = call(["git", "show", f"HEAD:{PACKAGE}/FREEZE.json"])
    if parent != freeze.get("source_commit") or committed.returncode or \
            hashlib.sha256(committed.stdout.encode()).hexdigest() != freeze_hash:
        print("STOP: source/freeze commit chain mismatch", file=sys.stderr)
        return 94
    if call(["git", "merge-base", "--is-ancestor", "origin/main", head]).returncode:
        print("STOP: origin/main is not an ancestor", file=sys.stderr)
        return 95
    if call(["git", "status", "--porcelain"]).stdout.strip():
        print("STOP: checkout not clean", file=sys.stderr)
        return 96
    if call(["docker", "context", "show"]).stdout.strip() != "orbstack":
        print("STOP: Docker context is not OrbStack", file=sys.stderr)
        return 97
    image = call(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    if image.returncode or image.stdout.strip() != freeze.get("image_id_platform"):
        print("STOP: cached image identity mismatch", file=sys.stderr)
        return 98
    for rel, expected in freeze["source_sha256"].items():
        source = (ROOT.parents[2] / ".github/workflows/origin-effect-binding-6500.yml"
                  if rel == "workflow" else ROOT / rel)
        if not source.is_file() or sha(source) != expected:
            print(f"STOP: source hash mismatch: {rel}", file=sys.stderr)
            return 99
    names = ("origin6500-candidate-formal01-20261002", "origin6500-auditor-formal01-20261002")
    if any(call(["docker", "container", "inspect", name]).returncode == 0 for name in names):
        print("STOP: formal container name already exists", file=sys.stderr)
        return 100
    FORMAL.mkdir(parents=True, exist_ok=True)
    (FORMAL / "candidate").mkdir()
    (FORMAL / "auditor").mkdir()
    common = ["docker", "run", "--pull", "never", "--network", "none", "--cpus", "1",
              "--memory", "256m", "--pids-limit", "64", "--read-only"]
    candidate_argv = common[:2] + ["--name", names[0]] + common[2:] + [
        "--mount", f"type=bind,source={ROOT},target=/src,readonly",
        "--mount", f"type=bind,source={FORMAL / 'candidate'},target=/out",
        "--workdir", "/src", IMAGE, "python", "-B", "/src/candidate.py", "--out", "/out/raw.json"]
    candidate_result = call(candidate_argv)
    (FORMAL / "candidate/combined.log").write_text(candidate_result.stdout)
    (FORMAL / "candidate/exit.txt").write_text(f"{candidate_result.returncode}\n")
    candidate_inspect = call(["docker", "inspect", names[0]])
    (FORMAL / "candidate/container-inspect.json").write_text(candidate_inspect.stdout.rstrip() + "\n")
    if candidate_result.returncode or not (FORMAL / "candidate/raw.json").is_file():
        return 20
    auditor_argv = common[:2] + ["--name", names[1]] + common[2:] + [
        "--mount", f"type=bind,source={ROOT},target=/src,readonly",
        "--mount", f"type=bind,source={FORMAL / 'candidate/raw.json'},target=/input/raw.json,readonly",
        "--mount", f"type=bind,source={FORMAL / 'auditor'},target=/out",
        "--workdir", "/src", IMAGE, "python", "-B", "/src/auditor.py", "/input/raw.json", "--out", "/out/audit.json"]
    auditor_result = call(auditor_argv)
    (FORMAL / "auditor/combined.log").write_text(auditor_result.stdout)
    (FORMAL / "auditor/exit.txt").write_text(f"{auditor_result.returncode}\n")
    auditor_inspect = call(["docker", "inspect", names[1]])
    (FORMAL / "auditor/container-inspect.json").write_text(auditor_inspect.stdout.rstrip() + "\n")
    record = {"allocation": ALLOCATION, "source_commit": freeze["source_commit"],
        "freeze_sha256": freeze_hash, "image": IMAGE, "image_id_platform": image.stdout.strip(),
        "candidate_container": names[0], "candidate_container_id": json.loads(candidate_inspect.stdout)[0]["Id"],
        "candidate_argv": candidate_argv, "candidate_exit": candidate_result.returncode,
        "candidate_sha256": sha(FORMAL / "candidate/raw.json"),
        "auditor_container": names[1], "auditor_container_id": json.loads(auditor_inspect.stdout)[0]["Id"],
        "auditor_argv": auditor_argv, "auditor_exit": auditor_result.returncode,
        "audit_sha256": sha(FORMAL / "auditor/audit.json") if (FORMAL / "auditor/audit.json").is_file() else None,
        "formal_counts": {"candidate_containers": 1, "auditor_containers": 1, "retries": 0}}
    (FORMAL / "RUN_RECORD.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"candidate_exit": candidate_result.returncode, "auditor_exit": auditor_result.returncode,
                      "candidate_sha256": record["candidate_sha256"], "audit_sha256": record["audit_sha256"]}))
    return 0 if auditor_result.returncode == 0 else 21


if __name__ == "__main__":
    raise SystemExit(main())
