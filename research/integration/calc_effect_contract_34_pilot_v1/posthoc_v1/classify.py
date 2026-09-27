"""Pure post-hoc classification of retained Calc observations."""
from __future__ import annotations


def classify(raw: dict, audit: dict, expected_value: int = 7) -> dict:
    live = raw.get("cell_after_edit_live")
    persisted = audit.get("independently_reopened_A1")
    before, after = raw.get("source_sha256_before"), raw.get("source_sha256_after")
    independent = audit.get("source_sha256_independent")
    stable = bool(before and before == after == independent)
    saved = "UNKNOWN" if not stable or persisted is None else ("VERIFIED" if persisted == expected_value else "CONTRADICTED")
    return {"schema":"calc-effect-contract-posthoc-classification-v1", "scope":"retained construction row; not runtime policy execution", "expected_saved_value":expected_value, "harness_completion":"COMPLETED" if raw.get("program_completed") is True else "NOT_COMPLETED", "live_view_predicate":"MATCH" if live == expected_value else "NO_MATCH", "saved_effect":saved, "source_hash_stable":stable, "frozen_construction_gate":audit.get("disposition"), "errors":list(audit.get("errors") or [])}
