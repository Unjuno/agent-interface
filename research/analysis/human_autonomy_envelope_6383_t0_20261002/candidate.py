"""Observation-only, receipt-bound envelope renderer for frozen T0 fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def render(receipt: dict[str, Any]) -> dict[str, Any]:
    auth = receipt["authority"]
    evidence = receipt["evidence"]
    generation_current = evidence["current"] and evidence["generation"] == auth["generation"]
    source_known = evidence["actor_known"] and evidence["footprint_known"]
    lease_live = auth["status"] == "active" and receipt["now_ms"] < auth["expires_at_ms"]
    invalidated = auth["status"] in {"revoked", "closed"} or not lease_live or receipt["cancel_requested"]

    if not source_known:
        state = "TERMINAL/UNKNOWN"
        actions = None
        targets = None
        expiry = None
        release_state = "UNKNOWN"
        effect_verified = None
    elif not generation_current:
        state = "WAITING_FOR_EVIDENCE"
        actions = []
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        release_state = "PENDING" if receipt["input_active"] else "UNVERIFIED"
        effect_verified = None
    elif receipt["phase"] == "terminal" and evidence["effect_status"] == "verified" and receipt["release_verified"] and receipt["release_receipt_id"] and receipt["obligations_complete"]:
        state = "TERMINAL"
        actions = []
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        release_state = "VERIFIED"
        effect_verified = True
    elif invalidated:
        if receipt["release_verified"] and receipt["release_receipt_id"]:
            state = "YIELDING"
            release_state = "VERIFIED"
        else:
            state = "RELEASE_VERIFYING"
            release_state = "PENDING" if receipt["input_active"] or receipt["cancel_requested"] or auth["status"] == "revoked" else "UNVERIFIED"
        actions = []
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        effect_verified = evidence["effect_status"] == "verified"
    elif receipt["phase"] == "model_deciding":
        state = "MODEL_DECIDING"
        actions = list(auth["allowed_action_classes"])
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        release_state = "VERIFIED" if receipt["release_verified"] and receipt["release_receipt_id"] else "NOT_REQUIRED"
        effect_verified = evidence["effect_status"] == "verified"
    elif receipt["phase"] == "waiting_for_evidence":
        state = "WAITING_FOR_EVIDENCE"
        actions = list(auth["allowed_action_classes"])
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        release_state = "VERIFIED" if receipt["release_verified"] and receipt["release_receipt_id"] else "NOT_REQUIRED"
        effect_verified = evidence["effect_status"] == "verified"
    elif receipt["phase"] == "local_action_active" and auth["allowed_action_classes"]:
        state = "LOCAL_ACTION_ACTIVE"
        actions = list(auth["allowed_action_classes"])
        targets = list(auth["targets"])
        expiry = auth["expires_at_ms"]
        release_state = "PENDING" if receipt["input_active"] else ("VERIFIED" if receipt["release_verified"] and receipt["release_receipt_id"] else "NOT_REQUIRED")
        effect_verified = evidence["effect_status"] == "verified"
    else:
        state = "TERMINAL/UNKNOWN"
        actions = None
        targets = None
        expiry = None
        release_state = "UNKNOWN"
        effect_verified = None

    return {
        "checkpoint_id": receipt["id"],
        "state": state,
        "permitted_next_action_classes": actions,
        "target_footprint": targets,
        "evidence_generation": evidence["generation"] if source_known and generation_current else None,
        "lease_expiry_ms": expiry,
        "revocation_trigger": auth["revocation_trigger"] if source_known else None,
        "physical_release_state": release_state,
        "effect_verified": effect_verified,
        "source_receipt_sha256": hashlib.sha256(canonical_bytes(receipt)).hexdigest(),
    }


def run(fixture_path: Path, output_path: Path) -> None:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    displays = [render(row) for row in fixture["checkpoints"]]
    result = {
        "schema": "autonomy-envelope-candidate-v1",
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "checkpoint_count": len(displays),
        "displays": displays,
    }
    output_path.write_bytes(canonical_bytes(result) + b"\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixture.json"))
    parser.add_argument("--output", type=Path, default=Path("candidate.json"))
    args = parser.parse_args()
    run(args.fixture, args.output)
