#!/usr/bin/env python3
"""Independently check source snapshot identities and retained test outcomes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text())
    run = json.loads((ROOT / "results" / "invocation.json").read_text())
    checks = {}
    checks["source_commit_is_frozen"] = (
        manifest["candidate_commit"] == freeze["candidate_commit"]
    )
    checks["source_manifest_count"] = len(manifest["files"]) == 23
    checks["all_source_snapshot_hashes"] = all(
        sha(ROOT / "source_snapshot" / item["path"]) == item["sha256"]
        for item in manifest["files"]
    )
    checks["runner_hash"] = sha(ROOT / "run_verification.py") == freeze["runner_sha256"]
    checks["auditor_hash"] = sha(ROOT / "audit.py") == freeze["auditor_sha256"]
    for mode in ("normal", "optimized"):
        output = (ROOT / "results" / f"{mode}.txt").read_text()
        row = run["results"].get(mode, {})
        checks[f"{mode}_exit_zero"] = row.get("exit_code") == 0
        checks[f"{mode}_40_tests"] = "Ran 40 tests" in output
        checks[f"{mode}_all_pass"] = "OK" in output and "FAILED" not in output
    checks["compile_exit_zero"] = run["results"].get("compile", {}).get("exit_code") == 0
    audit = {
        "schema": "v39-currentmain-renewal-overlay-a01-audit-v1",
        "checks": checks,
        "passed": all(checks.values()),
        "scope": "source identity and local deterministic test-result audit only",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
