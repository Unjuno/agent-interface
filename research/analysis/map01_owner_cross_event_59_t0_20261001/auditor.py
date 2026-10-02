"""Independent oracle for at-most-one entry across all events for one allocation."""
from __future__ import annotations


def audit(fixture: dict, candidate: dict) -> dict:
    expected = fixture["runs"]
    observed = candidate.get("rows", [])
    errors = []
    expected_ids = [row["id"] for row in expected]
    observed_ids = [row.get("current_run_id") for row in observed]
    if observed_ids != expected_ids:
        errors.append("candidate-row-identity-or-order-mismatch")
    if candidate.get("workflow_path") != fixture["workflow_path"]:
        errors.append("workflow-path-mismatch")
    if candidate.get("allocation_id") != fixture["allocation_id"]:
        errors.append("allocation-id-mismatch")
    if len({row["event"] for row in expected}) < 2:
        errors.append("fixture-does-not-cross-event-types")
    if len({row["path"] for row in expected}) != 1:
        errors.append("fixture-workflow-path-not-fixed")

    admitted = [
        row.get("current_run_id")
        for row in observed
        if row.get("may_enter_formal_step") is True
    ]
    if len(admitted) > 1:
        errors.append("multiple-events-admitted-for-one-versioned-allocation")
    return {
        "schema": "map01-cross-event-owner-independent-audit-v1",
        "allocation_id": fixture["allocation_id"],
        "workflow_path": fixture["workflow_path"],
        "candidate_run_count": len(observed),
        "admitted_run_ids": admitted,
        "admitted_count": len(admitted),
        "safety_invariant": "at_most_one_admitted_across_all_events_for_the_versioned_workflow_path",
        "errors": errors,
        "error_count": len(errors),
        "disposition": "PASS_ALLOCATION_GLOBAL" if not errors else "FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER",
    }


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--candidate", type=Path, default=Path(__file__).with_name("candidate_output.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        json.loads(args.fixture.read_text(encoding="utf-8")),
        json.loads(args.candidate.read_text(encoding="utf-8")),
    )
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.out.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    raise SystemExit(0 if result["error_count"] == 0 else 1)
