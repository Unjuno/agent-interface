"""Audit retained cleanup-overlap evidence without running the candidate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
repo = HERE.parents[3]
candidate_bytes = (HERE / "candidate.json").read_bytes()
candidate = json.loads(candidate_bytes)
record = candidate["record"]
overlapping = [
    row for row in candidate.get("owner_records", [])
    if isinstance(row, dict) and row.get("event") == "owner_release"
    and type(row.get("verified_ns")) is int
    and type(record.get("release_call_started_ns")) is int
    and type(record.get("release_call_returned_ns")) is int
    and record["release_call_started_ns"] <= row["verified_ns"] <= record["release_call_returned_ns"]
]
frozen_candidate_sources = {
    "research/doom/doom_retained_input_backend_v3.py":
        "6db0845c42f285b43c42639a390fb535a522bc913f417c1ccad9a1153d15484e",
    "research/live_control/input_transition_owner_v3.py":
        "5ffdbb3679451fefdc3836917d43d924f0f43c8082d21327207ecefbd87f5be6",
    "research/live_control/input_owner_v10.py":
        "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
}
actual_sources = {
    path: hashlib.sha256((repo / path).read_bytes()).hexdigest()
    for path in frozen_candidate_sources
}
checks = {
    "cleanup_record_is_inside_explicit_up_bracket": len(overlapping) == 1,
    "wrapper_snapshot_was_ordinary_at_request": (
        record.get("ordinary_release_candidate_at_request") is True
    ),
    "adapter_reclassifies_overlapping_cleanup": (
        record.get("owner_cleanup_log_available") is True
        and
        record.get("owner_cleanup_overlapped_release_call") is True
        and record.get("ordinary_release_candidate") is False
        and record.get("owner_transition_verified") is False
    ),
    "no_authority_or_physical_claim": (
        record.get("grants_input_authority") is False
        and record.get("physical_verification_authoritative") is False
    ),
    "candidate_implementation_source_hashes": actual_sources == frozen_candidate_sources,
}
result = {
    "schema": "input-release-owner-cleanup-race-audit-v1",
    "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    "implementation_source_sha256": actual_sources,
    "overlapping_cleanup_records": len(overlapping),
    "checks": checks,
    "outcome": "PASS" if all(checks.values()) else "FAIL",
    "scope": "synthetic in-bracket cleanup reclassification only",
}
(HERE / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
if result["outcome"] != "PASS":
    raise SystemExit(1)
