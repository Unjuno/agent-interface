"""Recompute the frozen bundle result checks from raw output and pinned files."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "valid": ("ADMISSION_BRACKETED_PROGRESS", "bounded_independent_progress_observed_after_first_input"),
    "source_hash_changed": ("POST_CANCELLATION_COOCCURRENCE", "source_manifest_mismatch"),
    "source_entry_unexpected": ("POST_CANCELLATION_COOCCURRENCE", "source_manifest_mismatch"),
    "summary_count_changed": ("POST_CANCELLATION_COOCCURRENCE", "scorer_summary_sample_count_mismatch"),
    "summary_schema_changed": ("POST_CANCELLATION_COOCCURRENCE", "invalid_scorer_summary"),
    "controller_visible": ("POST_CANCELLATION_COOCCURRENCE", "invalid_scorer_summary"),
    "summary_missing": ("POST_CANCELLATION_COOCCURRENCE", "invalid_or_missing_runtime_metadata"),
}


def audit():
    errors = []
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    policy_bytes = (ROOT / "SOURCE_POLICY.json").read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest() != freeze.get("expected_source_policy_sha256"):
        errors.append("source_policy_hash")
    policy = json.loads(policy_bytes)
    if policy.get("schema") != "map01-v15-source-policy-v1":
        errors.append("source_policy_schema")
    sources = policy.get("sources")
    if not isinstance(sources, dict) or not sources or any(
            not isinstance(name, str) or not isinstance(digest, str) or
            re.fullmatch(r"[0-9a-f]{64}", digest) is None for name, digest in sources.items()):
        errors.append("source_policy_map")
    raw = json.loads((ROOT / "RAW.json").read_text(encoding="utf-8"))
    if raw.get("schema") != "scorer-run-bundle-raw-v1":
        errors.append("raw_schema")
    if raw.get("base_main") != "31ce02c0a148aed9650b58ef31a8746d5e85e091":
        errors.append("base_main")
    if raw.get("live_game_model_or_input_launched") is not False:
        errors.append("launch_scope")
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        case = row.get("id") if isinstance(row, dict) else None
        if case not in EXPECTED or case in seen:
            errors.append(f"unexpected_or_duplicate:{case}")
            continue
        seen.add(case)
        decision, reason = EXPECTED[case]
        observed = row.get("observed")
        if row.get("expected_decision") != decision or row.get("expected_reason") != reason:
            errors.append(f"frozen_expectation:{case}")
        if not isinstance(observed, dict) or (observed.get("decision"), observed.get("reason")) != (decision, reason):
            errors.append(f"result:{case}")
        if not isinstance(observed, dict) or observed.get("causal_attribution") is not False:
            errors.append(f"causal_scope:{case}")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    return {"schema": "scorer-run-bundle-audit-v1", "pass": not errors,
            "errors": errors, "rows": len(rows),
            "claim_scope": "synthetic co-located metadata and scorer/event bundle construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "AUDIT.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
