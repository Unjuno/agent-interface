"""Independent raw-only oracle for the frozen candidate matrix."""
from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--input-dir", type=Path, default=HERE)
parser.add_argument("--out", type=Path)
args = parser.parse_args()
INPUT_DIR = args.input_dir.resolve()
INPUT = INPUT_DIR / "raw_cases.json"
CANDIDATE = INPUT_DIR / "candidate_results.json"
OUT = (args.out or (INPUT_DIR / "audit_result_v2.json")).resolve()
FROZEN_CANDIDATE_SOURCE_SHA256 = "c0187d5a95751e340f66fbbb03fe9066899bdb9c795a3dcaf1fd3be291d13496"

if OUT.exists():
    raise FileExistsError(f"refusing to overwrite audit output: {OUT}")
cases = json.loads(INPUT.read_text(encoding="utf-8"))
candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
assert candidate["schema"] == "map01-direct-retained-input-order-matrix-candidate-v1"
assert candidate["candidate_source_sha256"] == FROZEN_CANDIDATE_SOURCE_SHA256
assert len(cases) == 256 and candidate["case_count"] == len(cases)
assert len(candidate["results"]) == len(cases)

errors = []
valid_count = invalid_count = 0
for raw, wrapped in zip(cases, candidate["results"], strict=True):
    if raw["case_id"] != wrapped["case_id"]:
        errors.append({"case_id": raw.get("case_id"), "error": "case_order_or_identity_mismatch"})
        continue
    admitted, ack = raw["timestamps_ns"][0:2]
    release_start, release_return = raw["timestamps_ns"][2:4]
    expected_events = [
        {"event": "input_admission", "intent_token": "t", "key": "a",
         "admitted_ns": admitted, "input_ack_ns": ack},
        {"event": "input_release_transition", "intent_token": "t", "operation": "up",
         "key": "a", "release_call_started_ns": release_start,
         "release_call_returned_ns": release_return, "owner_transition_verified": True},
    ]
    if raw.get("events") != expected_events:
        errors.append({"case_id": raw["case_id"], "error": "raw_event_fields_do_not_match_timestamp_tuple"})
        continue
    valid = admitted <= ack <= release_start <= release_return
    result = wrapped["result"]
    if result.get("measurement_ready") is not valid:
        errors.append({"case_id": raw["case_id"], "error": "readiness_mismatch",
                       "expected": valid, "got": result.get("measurement_ready")})
        continue
    if valid:
        valid_count += 1
        if (result.get("hold_count") != 1 or result.get("invalid_release_count") != 0 or
                result["holds"][0]["retained_lower_ms"] != (release_start - ack) / 1e6 or
                result["holds"][0]["retained_upper_ms"] != (release_return - admitted) / 1e6):
            errors.append({"case_id": raw["case_id"], "error": "valid_interval_mismatch"})
    else:
        invalid_count += 1
        if result.get("hold_count") != 0 or result.get("invalid_release_count") != 1:
            errors.append({"case_id": raw["case_id"], "error": "invalid_pair_not_fail_closed"})

payload = {
    "schema": "map01-direct-retained-input-order-matrix-audit-v1",
    "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
    "candidate_source_sha256": candidate["candidate_source_sha256"],
    "cases": len(cases),
    "valid_monotonic_cases": valid_count,
    "invalid_order_cases": invalid_count,
    "errors": errors,
    "decision": "PASS_ORDERING_INVARIANT" if not errors and valid_count == 35 and invalid_count == 221 else "FAIL",
}
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
