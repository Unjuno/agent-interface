"""Audit the saved adapter/wrapper receipt without invoking candidate code."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
repo = HERE.parents[3]
candidate_bytes = (HERE / "candidate.json").read_bytes()
candidate = json.loads(candidate_bytes)
record = candidate["record"]
frozen_sources = {
    "research/doom/doom_retained_input_backend_v3.py":
        "1b96e852fa5da4cee531bdcb4832345a1f8355574bdcaa87665ac50c667b9f55",
    "research/live_control/input_transition_owner_v3.py":
        "5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6",
}
actual_sources = {
    path: hashlib.sha256((repo / path).read_bytes()).hexdigest()
    for path in frozen_sources
}
checks = {
    "receipt_shape": (
        record.get("event") == "input_release_transition"
        and record.get("transition_schema") == "input-release-transition-v3"
        and record.get("operation") == "up"
        and record.get("key") == "a"
    ),
    "identity_and_batch_binding": (
        record.get("owner_id") == "composed-owner"
        and record.get("intent_token") == "intent-1"
        and record.get("owner_identity_matches_after_batch") is True
        and record.get("intent_token_matches_after_batch") is True
        and record.get("release_batch_size") == 1
        and record.get("release_batch_position") == 0
    ),
    "release_precedes_post_batch_state_sample": (
        type(record.get("release_call_returned_ns")) is int
        and type(record.get("release_call_started_ns")) is int
        and type(record.get("owner_sample_after_started_ns")) is int
        and record["release_call_started_ns"] <= record["release_call_returned_ns"]
        and record["release_call_returned_ns"] <= record["owner_sample_after_started_ns"]
        and record.get("owner_sample_ordered_after_batch") is True
    ),
    "verified_only_for_empty_owned_state": (
        record.get("owned_keycodes_after_batch") == []
        and record.get("backend_owned_before_release") is True
        and record.get("ordinary_release_candidate") is True
        and record.get("owner_transition_verified") is True
    ),
    "no_physical_authority_claim": (
        record.get("physical_verification_authoritative") is False
        and record.get("grants_input_authority") is False
    ),
    "frozen_implementation_source_hashes": actual_sources == frozen_sources,
}
result = {
    "schema": "input-release-wrapper-batch-audit-v1",
    "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    "implementation_source_sha256": actual_sources,
    "checks": checks,
    "outcome": "PASS" if all(checks.values()) else "FAIL",
    "scope": "synthetic adapter/wrapper receipt compatibility only",
}
(HERE / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
if result["outcome"] != "PASS":
    raise SystemExit(1)
