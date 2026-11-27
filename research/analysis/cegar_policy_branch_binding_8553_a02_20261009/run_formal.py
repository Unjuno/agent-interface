#!/usr/bin/env python3
"""No-retry, audit-only runner for Issue #8553 A02."""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = HERE / "results"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    freeze_sha = freeze["freeze_sha256"]
    payload = {k: v for k, v in freeze.items() if k != "freeze_sha256"}
    if hashlib.sha256(canonical(payload)).hexdigest() != freeze_sha:
        raise SystemExit("freeze digest mismatch")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head == freeze["base_commit"]:
        raise SystemExit("freeze has not been committed")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", freeze["base_commit"], head], cwd=ROOT)
    subprocess.check_call(["git", "cat-file", "-e", f"{head}:{HERE.relative_to(ROOT)}/FREEZE.json"], cwd=ROOT)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("worktree must be clean")
    main_ref = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT, text=True).split()[0]
    if main_ref != freeze["base_commit"]:
        raise SystemExit("origin/main changed after freeze; preserve this allocation without running")
    for rel, expected in freeze["files"].items():
        if sha(HERE / rel) != expected:
            raise SystemExit(f"frozen input/source changed: {rel}")
    if RESULTS.exists() and any(RESULTS.iterdir()):
        raise SystemExit("formal results directory is not empty; refusing to rerun")
    RESULTS.mkdir(exist_ok=True)

    commands = [
        ("legacy_probe", [sys.executable, "-B", str(HERE / "legacy_probe.py"),
                          "--fixture", str(HERE / "input/fixture.json"),
                          "--candidate", str(HERE / "input/candidate-a01.json"),
                          "--legacy-audit", str(HERE / "input/audit-a01.py"),
                          "--saved-audit", str(HERE / "input/audit-a01.json"),
                          "--output", str(RESULTS / "LEGACY_PROBE.json")]),
        ("independent_auditor", [sys.executable, "-B", str(HERE / "branch_audit.py"),
                                 "--fixture", str(HERE / "input/fixture.json"),
                                 "--candidate", str(HERE / "input/candidate-a01.json"),
                                 "--freeze-sha256", freeze_sha,
                                 "--output", str(RESULTS / "BRANCH_AUDIT.json")]),
    ]
    runs = {}
    for name, argv in commands:
        started = datetime.now(timezone.utc).isoformat()
        proc = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, check=False)
        (RESULTS / f"{name}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (RESULTS / f"{name}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
        (RESULTS / f"{name}.exit.txt").write_text(f"{proc.returncode}\n", encoding="ascii")
        runs[name] = {"argv": argv, "started_utc": started,
                      "completed_utc": datetime.now(timezone.utc).isoformat(),
                      "exit_code": proc.returncode, "attempted": True}
        if proc.returncode != 0:
            break
    runner = {"schema": "issue8553-a02-formal-run-v1", "allocation": freeze["allocation"],
              "base_commit": freeze["base_commit"], "freeze_commit": head,
              "freeze_sha256": freeze_sha, "host": {"system": platform.platform(),
                  "python": sys.version, "executable": sys.executable},
              "candidate_invocations": 0,
              "legacy_checker_diagnostic_invocations": int("legacy_probe" in runs),
              "independent_auditor_invocations": int("independent_auditor" in runs),
              "retries": 0, "processes": runs,
              "finalized_utc": datetime.now(timezone.utc).isoformat()}
    with (RESULTS / "RUN.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(runner, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(runner, sort_keys=True))
    if any(item["exit_code"] != 0 for item in runs.values()) or len(runs) != 2:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
