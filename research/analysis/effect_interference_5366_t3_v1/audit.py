#!/usr/bin/env python3
"""Independent raw-only reconstruction; does not import candidate.py."""

import argparse
import json
from pathlib import Path


POLICIES = ("semantic_only", "resource_bound_only", "generation_bound_resource")


def reconstruct(case, policy, fixture):
    if case.get("semantic_effect") != "read(ui)":
        status = "DENY_SEMANTIC_EFFECT"
    elif policy == "semantic_only":
        status = "ADMIT"
    elif case.get("declared_bound_ms") is None:
        status = "UNKNOWN_RESOURCE_ENVELOPE"
    elif policy == "generation_bound_resource" and case.get("envelope_generation") != case.get("current_generation"):
        status = "UNKNOWN_STALE_RESOURCE_ENVELOPE"
    else:
        finish_bound = max(0, case["declared_bound_ms"] + fixture["read_start_ms"]) + fixture["controller_service_ms"]
        status = "DENY_RESOURCE_DEADLINE" if finish_bound > fixture["controller_deadline_ms"] else "ADMIT"

    permit = status == "ADMIT"
    finish = (
        max(0, case["actual_service_ms"] + fixture["read_start_ms"]) + fixture["controller_service_ms"]
        if permit else fixture["controller_service_ms"]
    )
    return {
        "case_id": case["case_id"],
        "policy": policy,
        "semantic_effect": case["semantic_effect"],
        "declared_bound_ms": case["declared_bound_ms"],
        "envelope_generation": case["envelope_generation"],
        "current_generation": case["current_generation"],
        "decision": status,
        "admitted": permit,
        "controller_completion_ms": finish,
        "deadline_missed": finish > fixture["controller_deadline_ms"],
    }


def audit(fixture, raw):
    expected = [reconstruct(c, p, fixture) for c in fixture["cases"] for p in POLICIES]
    errors = []
    actual = raw.get("rows", [])
    if raw.get("row_count") != 12 or len(expected) != 12:
        errors.append("row_count")
    if actual != expected:
        errors.append("exact_reconstruction")
    keyed = {(r.get("case_id"), r.get("policy")): r for r in actual}
    current_low = keyed.get(("current-low", "generation_bound_resource"), {})
    stale = keyed.get(("stale-low", "generation_bound_resource"), {})
    over = keyed.get(("current-overbudget", "generation_bound_resource"), {})
    unknown = keyed.get(("current-unknown", "generation_bound_resource"), {})
    if not current_low.get("admitted"):
        errors.append("current_low_must_remain_available")
    if stale.get("decision") != "UNKNOWN_STALE_RESOURCE_ENVELOPE" or stale.get("admitted"):
        errors.append("stale_generation_must_not_authorize")
    if over.get("decision") != "DENY_RESOURCE_DEADLINE" or over.get("admitted"):
        errors.append("current_overbudget_must_refuse")
    if unknown.get("decision") != "UNKNOWN_RESOURCE_ENVELOPE" or unknown.get("admitted"):
        errors.append("unknown_bound_must_not_authorize")
    fresh_rows = [keyed.get((c["case_id"], "generation_bound_resource"), {}) for c in fixture["cases"]]
    if any(r.get("deadline_missed") for r in fresh_rows):
        errors.append("freshness_policy_deadline")
    if any(r.get("semantic_effect") != "read(ui)" for r in fresh_rows):
        errors.append("semantic_resource_separation")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows_reconstructed": len(expected), "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.fixture.read_text()), json.loads(args.raw.read_text()))
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
