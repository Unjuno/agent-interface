"""Independent finite audit for observation-only recovery contract successor."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from contract import SCHEMA, validate_request, validate_result  # noqa: E402


def req():
    return {"schema": SCHEMA, "request_id": "r1", "session_id": "s1",
            "surface_id": "surface-a", "freshness_seq": 4, "deadline_ms": 1000,
            "want": ["focus", "surface", "geometry", "motor", "observation"],
            "rejected_action_id": "a1", "reason": "focus_mismatch"}


def ready():
    return {"schema": SCHEMA, "request_id": "r1", "session_id": "s1",
            "surface_id": "surface-a", "freshness_seq": 4, "status": "READY",
            "focus": {"window": "xterm"}, "surface": {"id": "surface-a"},
            "geometry": {"x": 0, "y": 0, "width": 640, "height": 400},
            "motor": {"held": []}, "observation": {"id": "o4"},
            "uncertainty": [], "authority": False}


def main():
    request = req()
    cases = [("valid_request", validate_request(request), None),
             ("valid_ready", validate_result(request, ready(), 4), None)]
    forbidden = ("input_ops", "lease_extension", "lease_transfer", "task_success",
                 "effect_verified", "authority_granted")
    for key in forbidden:
        bad = dict(ready()); bad[key] = False
        cases.append(("forbidden:" + key, validate_result(request, bad, 4), "FORBIDDEN_RESULT_FIELD"))
    stale = dict(ready()); stale["freshness_seq"] = 3
    cases.append(("stale", validate_result(request, stale, 4), "STALE_RESULT"))
    malformed = dict(ready()); malformed.pop("observation")
    cases.append(("missing_observation", validate_result(request, malformed, 4), "REQUESTED_EVIDENCE_MISSING"))
    for name, actual, expected in cases:
        if actual != expected:
            raise AssertionError((name, actual, expected))
    source = subprocess.check_output(["git", "-C", str(ROOT), "show", "HEAD:research/analysis/observation_recovery_contract_2452_v1/contract.py"])
    result = {"status": "PASS_OBSERVATION_ONLY_CONTRACT_SCOPED", "cases": len(cases),
              "oracle_agreement": len(cases), "authority_grants": 0,
              "source_sha256": hashlib.sha256(source).hexdigest(),
              "scope": "finite standard-library contract only",
              "live_recovery": "NOT_TESTED"}
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS_OBSERVATION_ONLY_CONTRACT_SCOPED cases={len(cases)} authority_grants=0")


if __name__ == "__main__":
    main()
