"""Independent raw-ledger and sealed-truth reconstruction; does not import candidate."""
from __future__ import annotations

def audit(fixture: dict, truth: dict, rows: list[dict]) -> dict:
    errors = []
    expected = {(b, d, o["stimulus"]) for b in fixture["blocks"] for d in fixture["displays"] for o in fixture["opportunities_per_block"]}
    actual = {(r.get("block"), r.get("display"), r.get("stimulus")) for r in rows}
    if len(rows) != len(expected) or actual != expected:
        errors.append("opportunity_denominator_or_factor_mismatch")
    tokens = {}
    for row in rows:
        forbidden = {"truth", "oracle_truth", "scorer_label", "expected_response", "correct_action"}
        if forbidden.intersection(row):
            errors.append("forbidden_oracle_field")
        stimulus = row.get("stimulus")
        expected_truth = truth["truth_by_class"].get(stimulus)
        if expected_truth is None:
            errors.append("unknown_class")
            continue
        token = row.get("opportunity_token")
        if not isinstance(token, str) or len(token) != 12:
            errors.append("invalid_token")
        tokens.setdefault(token, set()).add((row.get("display"), row.get("block")))
        fixture_stimulus = next((x for x in fixture["opportunities_per_block"] if x["stimulus"] == stimulus), {})
        if row.get("display_visibility") != fixture_stimulus.get("display_visibility") or (row.get("display_visibility") == "visible") != (expected_truth["visibility"] == "visible"):
            errors.append("visibility_mismatch")
        if row.get("available_evidence") != fixture_stimulus.get("available_evidence"):
            errors.append("evidence_not_source_bound")
        if row.get("human_response") is not None:
            errors.append("synthetic_row_contains_human_response")
        if row.get("display") not in fixture["displays"]:
            errors.append("unknown_display")
        if row.get("checkpoint") != (row.get("display") == "MATCHED_CHECKPOINT"):
            errors.append("checkpoint_flag_mismatch")
        if row.get("machine_hard_stop") != truth["hard_stop"] or truth["hard_stop"].get("suppressed"):
            errors.append("machine_hard_stop_changed")
    if any(len(v) != 3 for v in tokens.values()) or len(tokens) != 12:
        errors.append("matched_display_opportunity_identity_mismatch")
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "rows": len(rows),
        "unique_opportunities": len(tokens),
        "expected_rows": len(expected),
        "block_counts": {b: sum(1 for r in rows if r.get("block") == b) for b in fixture["blocks"]},
        "scorer_truth_classes": sorted({v["label"] for v in truth["truth_by_class"].values()}),
        "human_responses_present": any(r.get("human_response") is not None for r in rows),
        "hard_stop_preserved": all(r.get("machine_hard_stop") == truth["hard_stop"] for r in rows),
        "errors": sorted(set(errors)),
    }
