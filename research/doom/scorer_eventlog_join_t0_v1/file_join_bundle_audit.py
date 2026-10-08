"""Independent raw-only audit for the run-bundle consumer controls."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FREEZE_PATH = ROOT / "FILE_JOIN_BUNDLE_FREEZE.json"
RAW_PATH = ROOT / "file_join_bundle_raw.json"


def audit():
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-eventlog-run-bundle-raw-v1":
        errors.append("schema")
    if raw.get("base_main") != freeze.get("base_main"):
        errors.append("base_main")
    if raw.get("stack_parent") != freeze.get("stack_parent"):
        errors.append("stack_parent")
    if raw.get("freeze_sha256") != hashlib.sha256(freeze_bytes).hexdigest():
        errors.append("freeze_hash")
    if raw.get("source_sha256") != freeze.get("required_source_sha256"):
        errors.append("source_hash_manifest")
    if raw.get("launch_scope") != freeze.get("launch_scope"):
        errors.append("launch_scope")

    expected = freeze.get("cases", {})
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(expected):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        case_id = row.get("id")
        if case_id not in expected or case_id in seen:
            errors.append(f"unexpected_or_duplicate:{case_id}")
            continue
        seen.add(case_id)
        result = row.get("observed")
        if row.get("expected") != expected[case_id]:
            errors.append(f"frozen_expectation:{case_id}")
        if not isinstance(result, dict) or result.get("decision") != expected[case_id]:
            errors.append(f"decision:{case_id}")
        if not isinstance(result, dict) or result.get("causal_attribution") is not False:
            errors.append(f"causal_scope:{case_id}")
        if not isinstance(result, dict):
            continue
        if case_id == "valid_bundle":
            if result.get("reason") != freeze["decision_gates"]["valid_bundle_reason"]:
                errors.append("valid_reason")
            if result.get("positive_sample_ns") != 130:
                errors.append("valid_positive_sample")
        else:
            if result.get("reason") != freeze["decision_gates"]["invalid_bundle_reason"]:
                errors.append(f"invalid_reason:{case_id}")
            if not isinstance(result.get("bundle_error"), str):
                errors.append(f"bundle_error_type:{case_id}")
    if seen != set(expected):
        errors.append("case_completeness")
    return {"schema": "scorer-eventlog-run-bundle-audit-v1",
            "pass": not errors, "errors": errors, "rows": len(rows),
            "claim_scope": "synthetic MAP01 run-bundle consumer construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "file_join_bundle_audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
