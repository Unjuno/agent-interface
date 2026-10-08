#!/usr/bin/env python3
"""Independent raw-only reconstruction; intentionally does not import candidate.py."""

import argparse
import json
from pathlib import Path


MODES = ("semantic_only", "reject_all_observations", "semantic_plus_resource")


def expected_row(case, policy, fixture):
    if case.get("semantic_effect") != "read(ui)":
        decision = "DENY_SEMANTIC_EFFECT"
    elif policy == "reject_all_observations":
        decision = "DENY_BLANKET"
    elif policy == "semantic_only":
        decision = "ADMIT"
    elif policy == "semantic_plus_resource":
        limit = case.get("declared_bound_ms")
        if limit is None:
            decision = "UNKNOWN_RESOURCE_ENVELOPE"
        else:
            finish_bound = max(0, fixture["read_start_ms"] + limit) + fixture["controller_service_ms"]
            decision = "DENY_RESOURCE_DEADLINE" if finish_bound > fixture["controller_deadline_ms"] else "ADMIT"
    else:
        decision = "INVALID_POLICY"

    accepted = decision == "ADMIT"
    finish = (
        max(0, fixture["read_start_ms"] + case["actual_service_ms"]) + fixture["controller_service_ms"]
        if accepted
        else fixture["controller_service_ms"]
    )
    return {
        "case_id": case["case_id"],
        "policy": policy,
        "semantic_effect": case["semantic_effect"],
        "resource": case["resource"],
        "declared_bound_ms": case["declared_bound_ms"],
        "decision": decision,
        "admitted": accepted,
        "controller_completion_ms": finish,
        "deadline_missed": finish > fixture["controller_deadline_ms"],
    }


def audit(fixture, raw):
    expected = [expected_row(c, p, fixture) for c in fixture["cases"] for p in MODES]
    actual = raw.get("rows", [])
    errors = []
    if raw.get("row_count") != len(expected):
        errors.append("row_count")
    if actual != expected:
        errors.append("exact_reconstruction")
    by_key = {(r.get("case_id"), r.get("policy")): r for r in actual}
    dual = [by_key.get((c["case_id"], "semantic_plus_resource"), {}) for c in fixture["cases"]]
    dual_map = {r.get("case_id"): r for r in dual}
    if not dual_map.get("fast-read", {}).get("admitted") or not dual_map.get("cache-hit", {}).get("admitted"):
        errors.append("benign_read_preservation")
    if dual_map.get("slow-read", {}).get("admitted") or dual_map.get("cache-miss", {}).get("admitted"):
        errors.append("over_budget_rejection")
    unknown = dual_map.get("unknown-envelope", {})
    if unknown.get("decision") != "UNKNOWN_RESOURCE_ENVELOPE" or unknown.get("admitted"):
        errors.append("unknown_must_not_authorize")
    if any(r.get("deadline_missed") for r in dual):
        errors.append("dual_policy_deadline")
    if any(r.get("semantic_effect") != "read(ui)" for r in dual):
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
