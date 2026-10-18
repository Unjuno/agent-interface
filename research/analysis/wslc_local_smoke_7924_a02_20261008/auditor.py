"""Independent saved-output verifier for Issue #7924 A02."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "RAW.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen source hash mismatch: {name}")
    expected_result = json.loads((ROOT / "CANDIDATE_RESULT.json").read_text(encoding="utf-8"))
    if raw != expected_result:
        raise ValueError("saved candidate output differs from frozen candidate result")
    if raw["schema"] != "wslc-local-smoke-7924-a02-v1":
        raise ValueError("unexpected output schema")
    if raw["fixture_sha256"] != freeze["sha256"]["fixture.txt"]:
        raise ValueError("fixture bytes differ from pre-run identity")
    if raw["expected_fixture_sha256"] != freeze["sha256"]["fixture.txt"]:
        raise ValueError("candidate did not use frozen fixture digest")
    if raw["read_only_write_errno"] != 30:
        raise ValueError("source bind did not reject write with EROFS")
    if raw["status"] != "PASS_PORTABILITY_SCOPED":
        raise ValueError("candidate did not pass scoped portability gate")
    if any(raw[k] != 0 for k in ("model_calls", "gui_calls", "external_network_calls")):
        raise ValueError("out-of-scope calls recorded")
    print(json.dumps({"status": "PASS_AUDIT_SCOPED", "checked_files": len(freeze["sha256"]),
                      "candidate_status": raw["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
