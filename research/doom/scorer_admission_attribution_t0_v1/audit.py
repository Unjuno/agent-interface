"""Independent structural and decision audit of the retained T0 raw record."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "same_observation_pre_or_during_recovery": "POST_CANCELLATION_COOCCURRENCE",
    "bracketed_bounded_positive": "ADMISSION_BRACKETED_PROGRESS",
    "missing_pre_input_baseline": "POST_CANCELLATION_COOCCURRENCE",
    "positive_sample_gap_exceeded": "POST_CANCELLATION_COOCCURRENCE",
    "missed_poll_period": "POST_CANCELLATION_COOCCURRENCE",
}


def audit():
    raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-admission-attribution-t0-raw-v1":
        errors.append("schema")
    if raw.get("clock_domain") != "synthetic_single_monotonic_ns":
        errors.append("clock_domain")
    if raw.get("live_game_model_or_input_launched") is not False:
        errors.append("launch_scope")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        key = row.get("id")
        if key in seen or key not in EXPECTED:
            errors.append(f"unexpected_or_duplicate:{key}")
            continue
        seen.add(key)
        observed = row.get("observed")
        if row.get("expected") != EXPECTED[key]:
            errors.append(f"frozen_expectation:{key}")
        if not isinstance(observed, dict) or observed.get("decision") != EXPECTED[key]:
            errors.append(f"decision:{key}")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    return {"schema": "scorer-admission-attribution-t0-audit-v1", "pass": not errors, "errors": errors,
            "rows": len(rows), "cooccurrence_rejections": sum(row.get("observed", {}).get("decision") == "POST_CANCELLATION_COOCCURRENCE" for row in rows),
            "admission_bracketed_rows": sum(row.get("observed", {}).get("decision") == "ADMISSION_BRACKETED_PROGRESS" for row in rows),
            "claim_scope": "synthetic scorer-attribution policy construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
