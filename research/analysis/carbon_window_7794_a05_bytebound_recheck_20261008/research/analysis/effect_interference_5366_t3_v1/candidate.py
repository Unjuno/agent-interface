#!/usr/bin/env python3
"""One-shot candidate for the frozen resource-envelope freshness fixture."""

import argparse
import json
from pathlib import Path


POLICIES = ("semantic_only", "resource_bound_only", "generation_bound_resource")


def decide(policy, case, read_start_ms, controller_service_ms, deadline_ms):
    if case["semantic_effect"] != "read(ui)":
        return "DENY_SEMANTIC_EFFECT"
    if policy == "semantic_only":
        return "ADMIT"
    bound = case["declared_bound_ms"]
    if bound is None:
        return "UNKNOWN_RESOURCE_ENVELOPE"
    if policy == "generation_bound_resource" and case["envelope_generation"] != case["current_generation"]:
        return "UNKNOWN_STALE_RESOURCE_ENVELOPE"
    if policy not in ("resource_bound_only", "generation_bound_resource"):
        raise ValueError(f"unknown policy: {policy}")
    completion_bound = max(0, bound + read_start_ms) + controller_service_ms
    return "DENY_RESOURCE_DEADLINE" if completion_bound > deadline_ms else "ADMIT"


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for policy in POLICIES:
            decision = decide(policy, case, fixture["read_start_ms"], fixture["controller_service_ms"], fixture["controller_deadline_ms"])
            admitted = decision == "ADMIT"
            completion = (
                max(0, case["actual_service_ms"] + fixture["read_start_ms"]) + fixture["controller_service_ms"]
                if admitted else fixture["controller_service_ms"]
            )
            rows.append({
                "case_id": case["case_id"],
                "policy": policy,
                "semantic_effect": case["semantic_effect"],
                "declared_bound_ms": case["declared_bound_ms"],
                "envelope_generation": case["envelope_generation"],
                "current_generation": case["current_generation"],
                "decision": decision,
                "admitted": admitted,
                "controller_completion_ms": completion,
                "deadline_missed": completion > fixture["controller_deadline_ms"],
            })
    return {"row_count": len(rows), "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run(json.loads(args.fixture.read_text()))
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"row_count": result["row_count"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
