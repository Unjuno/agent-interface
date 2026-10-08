"""Run the single fixture-derived audit over immutable T1 raw bytes."""

import hashlib
import json
from pathlib import Path
import sys

from audit_truth import audit


HERE = Path(__file__).resolve().parent
T1 = HERE.parent / "same_cohort_negative_control_5841_t1_v1"
FIXTURE_PATH = HERE / "inputs" / "T1_fixture.json"
RAW_PATH = T1 / "results" / "candidate.stdout.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    expected = freeze["input_sha256"]
    actual = {
        "fixture.json": sha256(FIXTURE_PATH),
        "candidate.stdout.json": sha256(RAW_PATH),
    }
    if actual != expected:
        result = {"status": "STOP_FROZEN_INPUT_HASH_MISMATCH", "actual_sha256": actual}
    else:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
        result = audit(fixture, raw)
        result["input_sha256"] = actual
    (HERE / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_FIXTURE_DERIVED_RAW" else 1


if __name__ == "__main__":
    sys.exit(main())
