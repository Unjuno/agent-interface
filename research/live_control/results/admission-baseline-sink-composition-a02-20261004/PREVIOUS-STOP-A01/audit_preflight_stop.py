"""Saved-only integrity audit for the preserved A01 import preflight STOP."""
import hashlib
import json
from pathlib import Path


root = Path(__file__).resolve().parent
freeze = json.loads((root / "PRE-RUN.json").read_text(encoding="utf-8"))
hashes = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in freeze["source_sha256"]
}
stderr = (root / "RUN_STDERR.txt").read_text(encoding="utf-8")
checks = {
    "frozen_a01_sources_match": hashes == freeze["source_sha256"],
    "runner_exit_1": (root / "RUN_EXIT_CODE.txt").read_text(encoding="ascii").strip() == "1",
    "missing_dependency_named": "ModuleNotFoundError" in stderr and "lease_cause_v1" in stderr,
    "candidate_raw_absent": not (root / "RAW.json").exists(),
    "no_retry_freeze_preserved": freeze["no_retry"] is True,
}
result = {
    "schema": "admission-baseline-sink-compose-a01-preflight-audit-v1",
    "classification": "PRE_CANDIDATE_SETUP_STOP" if all(checks.values()) else "HOLD",
    "checks": checks,
    "passed": all(checks.values()),
    "errors": [key for key, passed in checks.items() if not passed],
}
(root / "AUDIT-PREFLIGHT.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
