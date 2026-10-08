#!/usr/bin/env python3
"""Independent raw-only recipient-effect audit for Issue #8618."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def expected_gated_effect(case: dict[str, Any], protocol: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    cap_ok = case.get("action_capability") == protocol["required_action_capability"]
    target = case.get("recipient_surface")
    secret = case.get("secret") or {}
    action = case.get("proposed_action")
    if not cap_ok:
        return None, "ASK_NO_ACTION_CAPABILITY"
    if not isinstance(action, dict):
        return None, "ASK_NO_VERIFIED_RELEASE_OR_EQUIVALENT_ROUTE"

    if secret.get("present") is not True:
        proof = action.get("provenance")
        ok = bool(
            action.get("data_classification") == "PUBLIC"
            and action.get("payload_secret_id") is None
            and action.get("recipient_surface") == target
            and isinstance(proof, dict)
            and proof.get("status") == protocol["required_provenance_status"]
            and proof.get("signed_by") == protocol["trusted_authorities"]["provenance"]
            and proof.get("signature_valid") is True
        )
        if ok:
            return visible(action), "ALLOW_PUBLIC_ACTION"
        return None, "ASK_NO_VERIFIED_RELEASE_OR_EQUIVALENT_ROUTE"

    proof = action.get("provenance")
    grant = case.get("declassification_grant")
    provenance_ok = bool(
        isinstance(proof, dict)
        and proof.get("status") == protocol["required_provenance_status"]
        and proof.get("signed_by") == protocol["trusted_authorities"]["provenance"]
        and proof.get("signature_valid") is True
        and proof.get("secret_id") == secret.get("secret_id")
        and proof.get("source_surface") == secret.get("source_surface")
        and proof.get("recipient_surface") == target
        and proof.get("dependency_secret_id") == secret.get("secret_id")
        and action.get("payload_secret_id") == secret.get("secret_id")
        and action.get("payload") == secret.get("value")
        and action.get("recipient_surface") == target
        and action.get("data_classification") == "SECRET"
    )
    grant_ok = bool(
        isinstance(grant, dict)
        and grant.get("signed_by") == protocol["trusted_authorities"]["declassification"]
        and grant.get("signature_valid") is True
        and grant.get("secret_id") == secret.get("secret_id")
        and grant.get("source_surface") == secret.get("source_surface")
        and grant.get("recipient_surface") == target
        and grant.get("purpose") == protocol["required_purpose"]
        and grant.get("task_id") == case.get("task_id")
    )
    if provenance_ok and grant_ok:
        return visible(action), "ALLOW_SCOPED_SECRET_RELEASE"

    general = case.get("general_action")
    cert = case.get("equivalence_certificate")
    equivalent = bool(
        isinstance(general, dict)
        and isinstance(cert, dict)
        and general.get("data_classification") == "PUBLIC"
        and general.get("payload_secret_id") is None
        and general.get("recipient_surface") == target
        and general.get("secret_independent") is True
        and cert.get("status") == protocol["required_certificate_status"]
        and cert.get("signed_by") == protocol["trusted_authorities"]["equivalence"]
        and cert.get("signature_valid") is True
        and cert.get("task_id") == case.get("task_id")
        and cert.get("action_id") == general.get("action_id")
        and cert.get("recipient_surface") == target
        and cert.get("secret_independent") is True
    )
    if equivalent:
        return visible(general), "ALLOW_EQUIVALENT_GENERAL_ACTION"
    return None, "ASK_NO_VERIFIED_RELEASE_OR_EQUIVALENT_ROUTE"


def visible(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_id": action.get("action_id"),
        "payload": action.get("payload"),
        "recipient_surface": action.get("recipient_surface"),
    }


def secret_effect(effect: Any, case: dict[str, Any], truth: dict[str, Any]) -> bool:
    proposed = case.get("proposed_action") or {}
    return bool(
        isinstance(effect, dict)
        and truth.get("secret_present") is True
        and effect.get("action_id") == proposed.get("action_id")
        and effect.get("payload") == truth.get("secret_value")
        and effect.get("recipient_surface") == truth.get("recipient_surface")
    )


def audit(protocol_path: Path, policy_path: Path, oracle_path: Path, raw_path: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text())
    policy = json.loads(policy_path.read_text())
    oracle = json.loads(oracle_path.read_text())
    if not (policy.get("protocol_id") == oracle.get("protocol_id") == protocol.get("protocol_id")):
        raise ValueError("protocol_id mismatch")
    cases = {row["case_id"]: row for row in policy["cases"]}
    truths = {row["case_id"]: row for row in oracle["cases"]}
    raw_rows = load_jsonl(raw_path)
    ids = [row.get("case_id") for row in raw_rows]
    if len(ids) != len(set(ids)) or set(ids) != set(cases) or set(cases) != set(truths):
        raise ValueError("case identity/count mismatch")

    errors: list[str] = []
    unauthorized_baseline = 0
    unauthorized_gated = 0
    authorized_secret_releases = 0
    general_completions = 0
    all_nonrelease_equivalent_completed = 0
    ask_cases: list[str] = []
    public_control_pass = False
    capability_denial_pass = False
    for row in raw_rows:
        cid = row["case_id"]
        case = cases[cid]
        truth = truths[cid]
        if row.get("action_capability") != case.get("action_capability"):
            errors.append(f"{cid}: capability not preserved")
        if case.get("action_capability") != protocol["required_action_capability"] and (
            row.get("baseline_effect") is not None or row.get("gated_effect") is not None
        ):
            errors.append(f"{cid}: effect emitted without capability")

        baseline_secret = secret_effect(row.get("baseline_effect"), case, truth)
        gated_secret = secret_effect(row.get("gated_effect"), case, truth)
        if baseline_secret and not truth.get("release_authorized"):
            unauthorized_baseline += 1
        if gated_secret and not truth.get("release_authorized"):
            unauthorized_gated += 1
        if gated_secret and truth.get("release_authorized"):
            authorized_secret_releases += 1

        expected_effect, expected_disposition = expected_gated_effect(case, protocol)
        if row.get("gated_effect") != expected_effect:
            errors.append(f"{cid}: gated recipient effect mismatch")
        if row.get("gate_disposition") != expected_disposition:
            errors.append(f"{cid}: gate disposition mismatch")

        effect = row.get("gated_effect")
        correct = bool(effect and effect.get("action_id") in truth.get("task_correct_actions", []))
        if effect and not correct:
            errors.append(f"{cid}: recipient-visible effect not task-correct")
        if effect and truth.get("general_action_equivalent") and effect.get("action_id", "").startswith("general-"):
            general_completions += 1
        if (
            truth.get("general_action_equivalent")
            and case.get("action_capability") == protocol["required_action_capability"]
            and not (truth.get("release_authorized") and secret_effect(effect, case, truth))
        ):
            if correct:
                all_nonrelease_equivalent_completed += 1
            else:
                errors.append(f"{cid}: equivalent non-release route did not complete")
        if effect is None:
            ask_cases.append(cid)
        if cid == "public_no_secret":
            public_control_pass = bool(effect and effect.get("action_id") == truth.get("public_secret_independent_action") and correct)
        if cid == "capability_absent":
            capability_denial_pass = effect is None and row.get("gate_disposition") == "ASK_NO_ACTION_CAPABILITY"

    # Two distinct values must each be releasable only under an exact grant.
    released_values = {
        truths[row["case_id"]]["secret_value"]
        for row in raw_rows
        if secret_effect(row.get("gated_effect"), cases[row["case_id"]], truths[row["case_id"]])
        and truths[row["case_id"]].get("release_authorized")
    }
    expected_general_denials = {
        cid for cid, truth in truths.items()
        if truth.get("secret_present") and not truth.get("general_action_equivalent")
    }
    if not expected_general_denials.issubset(set(ask_cases)):
        errors.append("non-equivalent secret paths did not fail closed")
    if unauthorized_gated:
        errors.append("unauthorized secret-specific recipient effect observed")
    if unauthorized_baseline == 0:
        errors.append("instruction-only positive leakage control did not leak")
    if len(released_values) < 2:
        errors.append("matching grants did not release both distinct secret values")
    if general_completions < 7 or all_nonrelease_equivalent_completed < 7:
        errors.append("equivalent general routes failed to complete expected cases")
    if not public_control_pass:
        errors.append("public no-secret control was blocked or altered")
    if not capability_denial_pass:
        errors.append("action capability denial control failed")

    return {
        "allocation_id": protocol["allocation_id"],
        "protocol_id": protocol["protocol_id"],
        "case_count": len(raw_rows),
        "unauthorized_baseline_secret_effects": unauthorized_baseline,
        "unauthorized_gated_secret_effects": unauthorized_gated,
        "authorized_secret_release_count": authorized_secret_releases,
        "authorized_secret_values": sorted(released_values),
        "equivalent_general_completions": general_completions,
        "equivalent_nonrelease_completions": all_nonrelease_equivalent_completed,
        "public_control_pass": public_control_pass,
        "action_capability_denial_pass": capability_denial_pass,
        "ask_cases": sorted(ask_cases),
        "errors": errors,
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL",
        "scope": protocol["scope"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--oracle", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.protocol, args.policy, args.oracle, args.raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"disposition": result["disposition"], "errors": len(result["errors"]), "output": str(args.output)}, sort_keys=True))
    if result["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
