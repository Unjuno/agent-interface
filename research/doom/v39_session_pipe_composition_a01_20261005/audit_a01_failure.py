"""Independent integrity check for the pre-launch A01 runner/freeze HOLD."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    attempt = json.loads((HERE / "ATTEMPT_A01.json").read_text(encoding="utf-8"))
    raw_path = HERE / attempt["raw_output"]
    raw = raw_path.read_text(encoding="utf-8")
    runner_sha = hashlib.sha256((HERE / freeze["candidate"]["file"]).read_bytes()).hexdigest()
    checks = [
        {"check": "runner_matches_freeze", "pass": runner_sha == freeze["candidate"]["sha256"]},
        {"check": "freeze_runner_mismatch_reproduced", "pass": "KeyError: 'python_version'" in raw and "python_version" not in freeze},
        {"check": "no_child_output", "pass": attempt["child_started"] is False and not (HERE / "results" / "a01").exists()},
        {"check": "held_not_scientific_result", "pass": attempt["disposition"] == "HOLD_CONSTRUCTION" and attempt["transport_result"] is None},
    ]
    audit = {
        "schema": "v39-session-child-pipe-a01-failure-audit-v1",
        "disposition": "PASS_AUDIT" if all(row["pass"] for row in checks) else "FAIL_AUDIT",
        "checks": checks,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }
    (HERE / "AUDIT_A01.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["disposition"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
