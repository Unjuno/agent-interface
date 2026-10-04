"""Independent raw-only audit of the JSONL consumer results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "valid": "ADMISSION_BRACKETED_PROGRESS",
    "stale_preinput": "POST_CANCELLATION_COOCCURRENCE",
    "missing_sample": "POST_CANCELLATION_COOCCURRENCE",
    "malformed": "POST_CANCELLATION_COOCCURRENCE",
}


def audit():
    raw = json.loads((ROOT / "file_join_raw.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-eventlog-jsonl-consumer-raw-v1":
        errors.append("schema")
    if raw.get("base_main") != "b47d4d0b053f6e7d88c37e24be81777aa28feb6a":
        errors.append("base_main")
    if raw.get("live_game_model_or_input_launched") is not False:
        errors.append("launch_scope")
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        case_id = row.get("id")
        if case_id not in EXPECTED or case_id in seen:
            errors.append(f"unexpected_or_duplicate:{case_id}")
            continue
        seen.add(case_id)
        result = row.get("observed")
        if row.get("expected") != EXPECTED[case_id]:
            errors.append(f"frozen_expectation:{case_id}")
        if not isinstance(result, dict) or result.get("decision") != EXPECTED[case_id]:
            errors.append(f"decision:{case_id}")
        if not isinstance(result, dict) or result.get("causal_attribution") is not False:
            errors.append(f"causal_scope:{case_id}")
        if case_id == "stale_preinput" and isinstance(result, dict):
            if result.get("reason") != "no_bounded_post_input_progress":
                errors.append("stale_preinput_reason")
        if case_id in ("missing_sample", "malformed") and isinstance(result, dict):
            if result.get("reason") != "invalid_or_missing_runtime_jsonl":
                errors.append(f"file_failure_reason:{case_id}")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    return {"schema": "scorer-eventlog-jsonl-consumer-audit-v1",
            "pass": not errors, "errors": errors,
            "rows": len(rows),
            "claim_scope": "synthetic MAP01 v15 JSONL consumer construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "file_join_audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
