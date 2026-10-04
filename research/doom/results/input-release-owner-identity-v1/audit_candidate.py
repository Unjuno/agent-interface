"""Independent scoped audit of the retained synthetic release receipt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
candidate_path = HERE / "candidate.json"
candidate_bytes = candidate_path.read_bytes()
candidate = json.loads(candidate_bytes)
record = candidate["record"]
checks = {
    "fixture_has_no_owner_identity": (
        record.get("owner_id") is None
        and record.get("owner_sample_ordered_after_batch") is True
        and record.get("intent_token_matches_after_batch") is True
        and record.get("owned_keycodes_after_batch") == []
    ),
    "verifier_fails_closed_for_missing_owner_identity": (
        record.get("owner_transition_verified") is False
        and record.get("owner_identity_matches_after_batch") is False
    ),
    "measurement_does_not_claim_physical_authority": (
        record.get("physical_verification_authoritative") is False
    ),
}
result = {
    "schema": "input-release-owner-identity-audit-v1",
    "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
    "checks": checks,
    "outcome": "PASS" if all(checks.values()) else "FAIL",
    "scope": "synthetic receipt-verifier construction only",
}
(HERE / "audit.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
if result["outcome"] != "PASS":
    raise SystemExit(1)
