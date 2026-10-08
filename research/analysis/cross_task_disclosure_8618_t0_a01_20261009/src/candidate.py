#!/usr/bin/env python3
"""Finite synthetic recipient-bound declassification candidate for Issue #8618."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _trusted_provenance(case: dict[str, Any], protocol: dict[str, Any]) -> bool:
    action = case.get("proposed_action") or {}
    provenance = action.get("provenance")
    secret = case.get("secret") or {}
    return bool(
        secret.get("present") is True
        and isinstance(provenance, dict)
        and provenance.get("status") == protocol["required_provenance_status"]
        and provenance.get("signed_by") == protocol["trusted_authorities"]["provenance"]
        and provenance.get("signature_valid") is True
        and provenance.get("secret_id") == secret.get("secret_id")
        and provenance.get("source_surface") == secret.get("source_surface")
        and provenance.get("recipient_surface") == case.get("recipient_surface")
        and provenance.get("dependency_secret_id") == secret.get("secret_id")
        and action.get("payload_secret_id") == secret.get("secret_id")
        and action.get("payload") == secret.get("value")
        and action.get("recipient_surface") == case.get("recipient_surface")
        and action.get("data_classification") == "SECRET"
    )


def _matching_grant(case: dict[str, Any], protocol: dict[str, Any]) -> bool:
    grant = case.get("declassification_grant")
    secret = case.get("secret") or {}
    return bool(
        isinstance(grant, dict)
        and grant.get("signed_by") == protocol["trusted_authorities"]["declassification"]
        and grant.get("signature_valid") is True
        and grant.get("secret_id") == secret.get("secret_id")
        and grant.get("source_surface") == secret.get("source_surface")
        and grant.get("recipient_surface") == case.get("recipient_surface")
        and grant.get("purpose") == protocol["required_purpose"]
        and grant.get("task_id") == case.get("task_id")
    )


def _equivalent_general(case: dict[str, Any], protocol: dict[str, Any]) -> bool:
    action = case.get("general_action")
    cert = case.get("equivalence_certificate")
    return bool(
        isinstance(action, dict)
        and isinstance(cert, dict)
        and action.get("data_classification") == "PUBLIC"
        and action.get("payload_secret_id") is None
        and action.get("recipient_surface") == case.get("recipient_surface")
        and action.get("secret_independent") is True
        and cert.get("status") == protocol["required_certificate_status"]
        and cert.get("signed_by") == protocol["trusted_authorities"]["equivalence"]
        and cert.get("signature_valid") is True
        and cert.get("task_id") == case.get("task_id")
        and cert.get("action_id") == action.get("action_id")
        and cert.get("recipient_surface") == case.get("recipient_surface")
        and cert.get("secret_independent") is True
    )


def _effect(action: dict[str, Any] | None) -> dict[str, Any] | None:
    if action is None:
        return None
    # This records the request visible to the synthetic recipient. The audit
    # determines secret-specific semantics from the fixture/oracle, not this tag.
    return {
        "action_id": action.get("action_id"),
        "payload": action.get("payload"),
        "recipient_surface": action.get("recipient_surface"),
    }


def decide(case: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    capability = case.get("action_capability") == protocol["required_action_capability"]
    secret = case.get("secret") or {}
    proposed = case.get("proposed_action")

    # Matched instruction-only baseline: it respects the tool capability but
    # has no information-release admission check.
    baseline_action = None
    if capability and isinstance(proposed, dict):
        if secret.get("present") is True and case.get("instruction_mode") == "USE_SECRET_WHEN_AVAILABLE":
            baseline_action = proposed
        elif secret.get("present") is not True and proposed.get("data_classification") == "PUBLIC":
            baseline_action = proposed

    gated_action = None
    if capability and isinstance(proposed, dict):
        if secret.get("present") is not True:
            if (
                proposed.get("data_classification") == "PUBLIC"
                and proposed.get("payload_secret_id") is None
                and proposed.get("recipient_surface") == case.get("recipient_surface")
                and isinstance(proposed.get("provenance"), dict)
                and proposed["provenance"].get("status") == protocol["required_provenance_status"]
                and proposed["provenance"].get("signed_by") == protocol["trusted_authorities"]["provenance"]
                and proposed["provenance"].get("signature_valid") is True
            ):
                gated_action = proposed
        elif _trusted_provenance(case, protocol) and _matching_grant(case, protocol):
            gated_action = proposed
        elif _equivalent_general(case, protocol):
            gated_action = case["general_action"]

    if not capability:
        disposition = "ASK_NO_ACTION_CAPABILITY"
    elif gated_action is None:
        disposition = "ASK_NO_VERIFIED_RELEASE_OR_EQUIVALENT_ROUTE"
    elif gated_action.get("data_classification") == "SECRET":
        disposition = "ALLOW_SCOPED_SECRET_RELEASE"
    elif secret.get("present") is True:
        disposition = "ALLOW_EQUIVALENT_GENERAL_ACTION"
    else:
        disposition = "ALLOW_PUBLIC_ACTION"

    return {
        "case_id": case["case_id"],
        "action_capability": case.get("action_capability"),
        "baseline_effect": _effect(baseline_action),
        "gate_disposition": disposition,
        "gated_effect": _effect(gated_action),
    }


def run(protocol_path: Path, policy_path: Path) -> list[dict[str, Any]]:
    protocol = json.loads(protocol_path.read_text())
    policy = json.loads(policy_path.read_text())
    if policy.get("protocol_id") != protocol.get("protocol_id"):
        raise ValueError("protocol_id mismatch")
    rows = [decide(case, protocol) for case in policy["cases"]]
    if len({row["case_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate case_id")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = run(args.protocol, args.policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(json.dumps({"rows": len(rows), "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
