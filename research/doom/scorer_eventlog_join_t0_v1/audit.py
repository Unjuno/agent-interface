"""Independent audit of the retained scorer/event join experiment."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "valid_file_join": "ADMISSION_BRACKETED_PROGRESS",
    "progress_only_before_first_input": "POST_CANCELLATION_COOCCURRENCE",
    "freshest_pre_input_baseline": "POST_CANCELLATION_COOCCURRENCE",
    "missing_pre_input_baseline": "POST_CANCELLATION_COOCCURRENCE",
    "missed_period_in_attribution_window": "POST_CANCELLATION_COOCCURRENCE",
    "malformed_sample_bracket": "POST_CANCELLATION_COOCCURRENCE",
    "ambiguous_intent_identity": "POST_CANCELLATION_COOCCURRENCE",
}


def audit():
    raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-eventlog-join-t0-raw-v1":
        errors.append("schema")
    if raw.get("clock_domain") != "synthetic_runtime_perf_counter_ns":
        errors.append("clock_domain")
    if raw.get("live_game_model_or_input_launched") is not False:
        errors.append("launch_scope")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        case_id = row.get("id")
        if case_id in seen or case_id not in EXPECTED:
            errors.append(f"unexpected_or_duplicate:{case_id}")
            continue
        seen.add(case_id)
        observed = row.get("observed")
        if row.get("expected") != EXPECTED[case_id]:
            errors.append(f"frozen_expectation:{case_id}")
        if not isinstance(observed, dict) or observed.get("decision") != EXPECTED[case_id]:
            errors.append(f"decision:{case_id}")
        if not isinstance(observed, dict) or observed.get("causal_attribution") is not False:
            errors.append(f"causal_scope:{case_id}")
        if case_id == "valid_file_join" and isinstance(observed, dict):
            if not (observed.get("accepted_ns") < observed.get("baseline_ns")
                    < observed.get("first_input_ns") < observed.get("positive_sample_ns")):
                errors.append("valid_boundary_order")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    return {"schema": "scorer-eventlog-join-t0-audit-v1", "pass": not errors,
            "errors": errors, "rows": len(rows),
            "admission_bracketed_rows": sum(row.get("observed", {}).get("decision") == "ADMISSION_BRACKETED_PROGRESS" for row in rows),
            "cooccurrence_rejections": sum(row.get("observed", {}).get("decision") == "POST_CANCELLATION_COOCCURRENCE" for row in rows),
            "claim_scope": "synthetic file-schema and event/scorer join construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
