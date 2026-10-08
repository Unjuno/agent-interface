#!/usr/bin/env python3
"""One-shot local candidate/auditor runner for frozen Issue #6684 T0."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS: Path
PREFORMAL: Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def prelaunch_stop(reason: str, details: dict) -> int:
    path = PREFORMAL / "STOP.json"
    path.parent.mkdir(parents=True, exist_ok=False)
    record = {"schema": "relational-coordinate-bounds-6684-prelaunch-stop-v1",
              "allocation": json.loads((ROOT / "FREEZE.json").read_text())["allocation"],
              "reason": reason, "candidate_invocations": 0,
              "auditor_invocations": 0, "retries": 0, **details}
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    path.with_suffix(".sha256").write_text(sha256(path) + "  STOP.json\n")
    print(json.dumps({"decision": "STOP", "reason": reason, "counts": "0/0/0"}))
    return 3


def source_preflight_failure(reason: str, details: dict) -> int:
    """Preserve a failed source preflight without claiming formal allocation."""
    path = PREFORMAL / "source-preflight-failure.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit("STOP_PREFORMAL_FAILURE_RECORD_ALREADY_EXISTS")
    record = {"schema": "relational-coordinate-bounds-6684-preformal-failure-v1",
              "allocation": json.loads((ROOT / "FREEZE.json").read_text())["allocation"],
              "stage": "construction/preflight", "reason": reason,
              "candidate_invocations": 0, "auditor_invocations": 0,
              "retries": 0, "formal_allocation_started": False, **details}
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    path.with_suffix(".sha256").write_text(sha256(path) + "  source-preflight-failure.json\n")
    print(json.dumps({"decision": "PREFORMAL_FAILURE", "reason": reason,
                      "formal_counts": "0/0/0"}))
    return 3


def write_preformal_failure(reason: str, details: dict) -> int:
    path = PREFORMAL / "construction-performance-failure.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SystemExit("STOP_PREFORMAL_FAILURE_RECORD_ALREADY_EXISTS")
    record = {"schema": "relational-coordinate-bounds-6684-preformal-failure-v1",
              "allocation": json.loads((ROOT / "FREEZE.json").read_text())["allocation"],
              "stage": "construction test", "reason": reason,
              "candidate_invocations": 0, "auditor_invocations": 0,
              "retries": 0, "formal_allocation_started": False, **details}
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    path.with_suffix(".sha256").write_text(sha256(path) + "  construction-performance-failure.json\n")
    print(json.dumps({"decision": "PREFORMAL_FAILURE_RETAINED", "formal_counts": "0/0/0"}))
    return 0


def main() -> int:
    global RESULTS, PREFORMAL
    freeze_path = ROOT / "FREEZE.json"
    freeze_sha_path = ROOT / "FREEZE.sha256"
    freeze = json.loads(freeze_path.read_text())
    allocation = freeze["allocation"]
    PREFORMAL = ROOT / "results" / allocation
    RESULTS = PREFORMAL / "formal-01"
    if RESULTS.exists():
        raise SystemExit("STOP_OUTPUT_PATH_ALREADY_EXISTS")
    prior_freeze_sha = freeze["supersedes_freeze_sha256"]
    retired_record_sha = freeze["supersedes_retired_record_sha256"]
    retired = ROOT / "FREEZE_T0_RETIRED.json"
    if not retired.exists() or not freeze_sha_path.exists():
        return source_preflight_failure("STOP_SUPERSEDED_ALLOCATION_STATE", {})
    if sha256(retired) != retired_record_sha:
        return source_preflight_failure("STOP_RETIRED_RECORD_HASH_MISMATCH",
                                        {"expected": retired_record_sha, "actual": sha256(retired)})
    retired_record = json.loads(retired.read_text())
    if retired_record.get("superseded_freeze_sha256") != prior_freeze_sha:
        return source_preflight_failure("STOP_RETIRED_FREEZE_CHAIN_MISMATCH", {})
    if freeze_sha_path.read_text().split()[0] != sha256(freeze_path):
        return prelaunch_stop("STOP_FREEZE_HASH_MISMATCH", {})
    if not PREFORMAL.exists():
        PREFORMAL.mkdir(parents=True)
        failure = {"schema": "relational-coordinate-bounds-6684-preformal-failure-v1",
                   "allocation": allocation, "stage": "construction test",
                   "reason": "Initial independent auditor construction exceeded responsive runtime and was interrupted before completion.",
                   "candidate_invocations": 0, "auditor_invocations": 0, "retries": 0,
                   "formal_allocation_started": False, "initial_max_worlds_per_case": 9529569,
                   "corrective_change": "Bound fixture to <=100000 states per case and combine exact audit summaries in one enumeration pass.",
                   "post_correction_construction_tests": 11,
                   "post_correction_construction_test_seconds": 1.04}
        failure_path = PREFORMAL / "construction-performance-failure.json"
        failure_path.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n")
        failure_path.with_suffix(".sha256").write_text(sha256(failure_path) + "  construction-performance-failure.json\n")
    if not allocation.endswith("-06"):
        return source_preflight_failure("STOP_WRONG_SUCCESSOR_ALLOCATION", {"allocation": allocation})
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", freeze["source_commit"], "HEAD"],
                             cwd=ROOT, check=False, capture_output=True)
    if ancestor.returncode != 0:
        return prelaunch_stop("STOP_FROZEN_SOURCE_NOT_ANCESTOR", {"head": git("rev-parse", "HEAD")})
    repo_root = Path(git("rev-parse", "--show-toplevel"))
    for rel, expected in freeze["source_sha256"].items():
        actual = sha256(repo_root / rel)
        if actual != expected:
            return prelaunch_stop("STOP_SOURCE_HASH_MISMATCH", {"path": rel,
                                  "expected": expected, "actual": actual})
    runner_rel = (ROOT / "runner.py").relative_to(repo_root).as_posix()
    frozen_runner = subprocess.run(["git", "show", freeze["source_commit"] + ":" + runner_rel],
                                   cwd=ROOT, check=False, capture_output=True)
    if frozen_runner.returncode or hashlib.sha256(frozen_runner.stdout).hexdigest() != sha256(ROOT / "runner.py"):
        return prelaunch_stop("STOP_RUNNER_DIFFERS_FROM_FROZEN_BLOB", {"path": runner_rel})
    design_rel = (ROOT / "design.json").relative_to(repo_root).as_posix()
    design_blob = subprocess.run(["git", "cat-file", "-e", freeze["source_commit"] + ":" + design_rel],
                                 cwd=ROOT, check=False, capture_output=True)
    if design_blob.returncode != 0:
        return prelaunch_stop("STOP_FROZEN_DESIGN_BLOB_MISSING", {"source_commit": freeze["source_commit"]})

    fetch = subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT,
                           capture_output=True, check=False)
    if fetch.returncode != 0:
        return prelaunch_stop("STOP_LIVE_MAIN_FETCH_FAILED", {"stderr": fetch.stderr.decode(errors="replace")})
    live_main = git("rev-parse", "origin/main")
    baseline = freeze["baseline_main_sha"]
    baseline_ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", baseline, live_main],
                                       cwd=ROOT, check=False, capture_output=True)
    if baseline_ancestor.returncode != 0:
        return prelaunch_stop("STOP_FROZEN_MAIN_NOT_ANCESTOR", {"baseline_main": baseline,
                                "live_main": live_main})
    advanced_paths = git("diff", "--name-only", baseline + ".." + live_main).splitlines()
    protected = freeze["prelaunch_parallel_guard"]["protected_paths"]
    collisions = sorted(path for path in advanced_paths
                        if any(path == prefix or path.startswith(prefix.rstrip("/") + "/")
                               for prefix in protected))
    if collisions:
        return prelaunch_stop("STOP_LIVE_MAIN_PROTECTED_PATH_COLLISION",
                              {"baseline_main": baseline, "live_main": live_main,
                               "collision_paths": collisions,
                               "main_advanced_paths": advanced_paths})

    RESULTS.mkdir(parents=True)
    candidate_dir = RESULTS / "candidate"
    audit_dir = RESULTS / "audit"
    env_record = {"started_utc": datetime.now(timezone.utc).isoformat(),
                  "python_version": sys.version, "python_executable": sys.executable,
                  "python_executable_sha256": sha256(Path(sys.executable)),
                  "platform": platform.platform(), "machine": platform.machine(),
                  "execution": "local-host CPU finite-state method fixture",
                  "baseline_main_sha": baseline, "live_main_sha_prelaunch": live_main,
                  "main_advanced_disjointly": live_main != baseline,
                  "main_paths_advanced": advanced_paths,
                  "container_used": False,
                  "container_reason": "No GUI or runtime authority is exercised; unrelated OrbStack containers were active, so this bounded pure-Python method fixture ran locally without touching shared containers."}
    (RESULTS / "environment.json").write_text(json.dumps(env_record, sort_keys=True, indent=2) + "\n")
    commands = [
        [sys.executable, "-B", str(ROOT / "candidate.py"), "--design", str(ROOT / "design.json"), "--out", str(candidate_dir)],
        [sys.executable, "-B", str(ROOT / "auditor.py"), "--design", str(ROOT / "design.json"),
         "--candidate", str(candidate_dir / "candidate.json"), "--out", str(audit_dir)],
    ]
    invocations = []
    stdout = []
    stderr = []
    # Exactly one candidate process and one separate auditor process; never retry.
    for argv in commands:
        started = time.monotonic()
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
        invocations.append({"argv": argv, "exit_code": proc.returncode,
                            "duration_seconds": time.monotonic() - started})
        stdout.append(proc.stdout)
        stderr.append(proc.stderr)
    (RESULTS / "candidate.stdout.txt").write_bytes(stdout[0])
    (RESULTS / "candidate.stderr.txt").write_bytes(stderr[0])
    (RESULTS / "auditor.stdout.txt").write_bytes(stdout[1])
    (RESULTS / "auditor.stderr.txt").write_bytes(stderr[1])
    audit_path = audit_dir / "audit.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        decision = audit.get("disposition", "HOLD_AUDIT_OUTPUT_MISSING")
    else:
        decision = "HOLD_AUDIT_OUTPUT_MISSING"
    artifacts = [RESULTS / "environment.json", candidate_dir / "candidate.json", audit_path,
                 RESULTS / "candidate.stdout.txt", RESULTS / "candidate.stderr.txt",
                 RESULTS / "auditor.stdout.txt", RESULTS / "auditor.stderr.txt"]
    manifest = {str(p.relative_to(RESULTS)): sha256(p) for p in artifacts if p.exists()}
    (RESULTS / "SHA256.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    record = {"schema": "relational-coordinate-bounds-6684-run-v1",
              "allocation": freeze["allocation"], "source_commit": freeze["source_commit"],
              "freeze_sha256": sha256(freeze_path), "decision": decision,
              "candidate_invocations": 1, "auditor_invocations": 1, "retries": 0,
              "commands": invocations, "artifacts_sha256": manifest,
              "ended_utc": datetime.now(timezone.utc).isoformat()}
    (RESULTS / "RUN_RECORD.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"decision": decision, "candidate_exit": invocations[0]["exit_code"],
                      "auditor_exit": invocations[1]["exit_code"], "retries": 0}))
    return 0 if decision == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
