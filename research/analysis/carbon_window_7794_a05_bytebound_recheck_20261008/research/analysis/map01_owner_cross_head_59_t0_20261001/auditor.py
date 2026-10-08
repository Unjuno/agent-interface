"""Independent invariant oracle; does not import candidate or owner-helper code."""
import json
import sys
from pathlib import Path


def audit(fixture: dict, output: dict) -> dict:
    expected_ids = [row["id"] for row in fixture["runs"]]
    rows = output.get("rows", [])
    errors = []
    if len(rows) != len(expected_ids):
        errors.append("candidate-row-count")
    observed_ids = [row.get("current_run_id") for row in rows]
    if observed_ids != expected_ids:
        errors.append("candidate-run-order")
    admitted = [row.get("current_run_id") for row in rows if row.get("may_enter_formal_step") is True]
    if len(admitted) > 1:
        errors.append("multiple-runs-admitted-for-one-versioned-allocation")
    return {
        "auditor": "workflow-path-global-owner-invariant-v1",
        "allocation_id": fixture["allocation_id"],
        "distinct_runs": len(expected_ids),
        "distinct_head_shas": len({run["head_sha"] for run in fixture["runs"]}),
        "admitted_run_ids": admitted,
        "admitted_count": len(admitted),
        "safety_invariant": "at_most_one_admitted_across_all_heads_for_the_versioned_workflow_path",
        "errors": errors,
        "error_count": len(errors),
        "disposition": "PASS_INVARIANT" if not errors else "FAIL_GUARD_NOT_WORKFLOW_PATH_GLOBAL",
    }


if __name__ == "__main__":
    root = Path(__file__).parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    output = json.loads((root / "candidate_output.json").read_text(encoding="utf-8"))
    result = audit(fixture, output)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["error_count"]:
        raise SystemExit(1)
