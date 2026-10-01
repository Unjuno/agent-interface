"""Independent finite oracle for workflow query/helper owner composition."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
CASES = HERE / "cases.json"
RAW = HERE / "candidate.raw.json"
OUT = HERE / "audit.raw.json"


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    spec = json.loads(CASES.read_text(encoding="utf-8"))
    raw_bytes = RAW.read_bytes()
    result = json.loads(raw_bytes)
    errors = []
    matrix = {r.get("case_id"): r for r in result.get("matrix", [])}
    if set(matrix) != {c["case_id"] for c in spec["matrix"]}:
        errors.append("MATRIX_CASE_SET_MISMATCH")
    if result.get("source_commit") != fixture["source_commit"]:
        errors.append("SOURCE_COMMIT_MISMATCH")
    if result.get("api_workflow_file") != Path(fixture["workflow_path"]).name:
        errors.append("WORKFLOW_PATH_MISMATCH")
    if result.get("api_query_params", {}).get("event") != ["$GITHUB_EVENT_NAME"]:
        errors.append("EVENT_FILTER_NOT_REPRODUCED")
    cross_event_admissions = []
    for c in spec["matrix"]:
        row = matrix.get(c["case_id"], {})
        cross = c["current_event"] != c["prior_event"]
        expected_scoped = "PASS_CANONICAL_GLOBAL_OWNER" if cross else "FAIL_ALLOCATION_ALREADY_OWNED"
        expected_scoped_admit = cross
        if row.get("scoped_result") != expected_scoped or row.get("scoped_may_enter") is not expected_scoped_admit:
            errors.append(f"{c['case_id']}:SCOPED_RESULT_MISMATCH")
        if row.get("complete_result") != "FAIL_ALLOCATION_ALREADY_OWNED" or row.get("complete_may_enter") is not False:
            errors.append(f"{c['case_id']}:COMPLETE_HISTORY_ORACLE_MISMATCH")
        if cross and row.get("scoped_may_enter") is True:
            cross_event_admissions.append(c["case_id"])
    first = result.get("first_run_control", {})
    if first.get("scoped_result") != "PASS_CANONICAL_GLOBAL_OWNER" or first.get("scoped_may_enter") is not True:
        errors.append("FIRST_RUN_CONTROL_MISMATCH")
    truncated = result.get("truncated_control", {})
    if truncated.get("result_class") != "UNCERTAIN_TRUNCATED_API_VIEW" or truncated.get("may_enter") is not False:
        errors.append("TRUNCATED_CONTROL_NOT_FAIL_CLOSED")
    disposition = "FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER" if len(cross_event_admissions) == 4 else "PASS_OWNER_SCOPE_INVARIANT" if not cross_event_admissions else "FAIL_UNEXPECTED_OWNER_ESCAPE_COUNT"
    if errors:
        disposition = "FAIL_AUDIT_INTEGRITY"
    report = {
        "schema": "map01-global-owner-event-head-audit-v1",
        "status": disposition,
        "source_commit": fixture["source_commit"],
        "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "matrix_cases": len(spec["matrix"]),
        "cross_event_admissions": cross_event_admissions,
        "independent_errors": errors,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
