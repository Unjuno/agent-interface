"""Independent raw-only verifier; intentionally does not import candidate.py."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def stable_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def expected_display(row: dict[str, Any]) -> dict[str, Any]:
    authority = row["authority"]
    proof = row["evidence"]
    fresh = proof["current"] is True and proof["generation"] == authority["generation"]
    identified = proof["actor_known"] is True and proof["footprint_known"] is True
    not_expired = row["now_ms"] < authority["expires_at_ms"]
    revoked = authority["status"] in ("revoked", "closed")
    canceled = row["cancel_requested"] is True
    stop = revoked or not not_expired or canceled
    release_receipt = row["release_verified"] is True and bool(row["release_receipt_id"])

    state = "TERMINAL/UNKNOWN"
    actions = targets = expiry = generation = effect = None
    release = "UNKNOWN"
    if identified:
        targets = list(authority["targets"])
        expiry = authority["expires_at_ms"]
        if fresh:
            generation = proof["generation"]
            effect = proof["effect_status"] == "verified"
        else:
            state = "WAITING_FOR_EVIDENCE"
            actions = []
            release = "PENDING" if row["input_active"] else "UNVERIFIED"

        if fresh and row["phase"] == "terminal" and effect is True and release_receipt and row["obligations_complete"] is True:
            state, actions, release = "TERMINAL", [], "VERIFIED"
        elif fresh and stop:
            actions = []
            if release_receipt:
                state, release = "YIELDING", "VERIFIED"
            else:
                state = "RELEASE_VERIFYING"
                release = "PENDING" if row["input_active"] or canceled or revoked else "UNVERIFIED"
        elif fresh and not stop and row["phase"] == "model_deciding":
            state, actions = "MODEL_DECIDING", list(authority["allowed_action_classes"])
            release = "VERIFIED" if release_receipt else "NOT_REQUIRED"
        elif fresh and not stop and row["phase"] == "waiting_for_evidence":
            state, actions = "WAITING_FOR_EVIDENCE", list(authority["allowed_action_classes"])
            release = "VERIFIED" if release_receipt else "NOT_REQUIRED"
        elif fresh and not stop and row["phase"] == "local_action_active" and authority["status"] == "active":
            if authority["allowed_action_classes"]:
                state, actions = "LOCAL_ACTION_ACTIVE", list(authority["allowed_action_classes"])
            else:
                state, actions = "TERMINAL/UNKNOWN", None
            release = "PENDING" if row["input_active"] else ("VERIFIED" if release_receipt else "NOT_REQUIRED")

    return {
        "checkpoint_id": row["id"],
        "state": state,
        "permitted_next_action_classes": actions,
        "target_footprint": targets,
        "evidence_generation": generation,
        "lease_expiry_ms": expiry,
        "revocation_trigger": authority["revocation_trigger"] if identified else None,
        "physical_release_state": release,
        "effect_verified": effect,
        "source_receipt_sha256": hashlib.sha256(stable_json(row)).hexdigest(),
    }


def audit(fixture_path: Path, candidate_path: Path) -> dict[str, Any]:
    raw = fixture_path.read_bytes()
    fixture = json.loads(raw)
    result = json.loads(candidate_path.read_bytes())
    rows = fixture["checkpoints"]
    expected_ids = [r["id"] for r in rows]
    observed = result.get("displays")
    errors: list[str] = []
    if fixture.get("schema") != "autonomy-envelope-fixture-v1":
        errors.append("FIXTURE_SCHEMA")
    if result.get("schema") != "autonomy-envelope-candidate-v1":
        errors.append("CANDIDATE_SCHEMA")
    if result.get("fixture_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("FIXTURE_HASH")
    if result.get("checkpoint_count") != len(rows):
        errors.append("COUNT")
    if not isinstance(observed, list) or [d.get("checkpoint_id") for d in observed] != expected_ids:
        errors.append("ROW_IDENTITY_OR_ORDER")
    if len(set(expected_ids)) != len(expected_ids) or len(expected_ids) != 10:
        errors.append("FIXTURE_CARDINALITY")

    if isinstance(observed, list) and len(observed) == len(rows):
        for index, (row, got) in enumerate(zip(rows, observed)):
            want = expected_display(row)
            if got != want:
                errors.append(f"DISPLAY_MISMATCH:{index}:{row['id']}")

    return {
        "schema": "autonomy-envelope-audit-v1",
        "result": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "checkpoint_count": len(rows),
        "independently_reconstructed": len(rows) if not errors else None,
        "errors": errors,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixture.json"))
    parser.add_argument("--candidate", type=Path, default=Path("candidate.json"))
    parser.add_argument("--output", type=Path, default=Path("audit.json"))
    args = parser.parse_args()
    args.output.write_bytes(stable_json(audit(args.fixture, args.candidate)) + b"\n")


if __name__ == "__main__":
    main()
