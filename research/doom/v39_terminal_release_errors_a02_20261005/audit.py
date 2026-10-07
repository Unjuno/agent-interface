#!/usr/bin/env python3
"""Audit frozen source identities and the retained baseline/candidate results."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / "BASELINE.json").read_text(encoding="utf-8"))
    invocation = json.loads((ROOT / "results" / "invocation.json").read_text(encoding="utf-8"))
    checks = {
        "manifest_commit_matches_freeze": manifest["candidate_commit"] == freeze["candidate_commit"],
        "candidate_snapshot_hashes": all(
            sha(ROOT / "source_snapshot" / row["path"]) == row["sha256"]
            for row in manifest["files"]),
        "baseline_identity_matches_freeze": baseline["base_main_sha"] == freeze["baseline_main_sha"],
        "baseline_source_hash": sha(ROOT / "baseline_source" / baseline["path"]) == baseline["sha256"],
        "runner_hash": sha(ROOT / "run_verification.py") == freeze["runner_sha256"],
        "auditor_hash": sha(ROOT / "audit.py") == freeze["auditor_sha256"],
        "invocation_candidate_matches": invocation["candidate_commit"] == freeze["candidate_commit"],
        "baseline_expected_failure": (
            invocation["runs"]["baseline"]["exit_code"] == 1 and
            "Ran 1 test" in (ROOT / "results" / "baseline.txt").read_text() and
            "FAILED (failures=1)" in (ROOT / "results" / "baseline.txt").read_text() and
            "None is not an instance of <class 'dict'>" in
            (ROOT / "results" / "baseline.txt").read_text()),
        "candidate_24_pass": (
            invocation["runs"]["candidate"]["exit_code"] == 0 and
            "Ran 24 tests" in (ROOT / "results" / "candidate.txt").read_text() and
            "OK" in (ROOT / "results" / "candidate.txt").read_text() and
            "FAILED" not in (ROOT / "results" / "candidate.txt").read_text()),
        "compile_exit_zero": invocation["runs"]["compile"]["exit_code"] == 0,
    }
    result = {"schema": "v39-terminal-release-errors-a02-audit-v1",
              "checks": checks, "passed": all(checks.values()),
              "scope": "local deterministic source-bound regression only"}
    (ROOT / "results" / "audit.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
