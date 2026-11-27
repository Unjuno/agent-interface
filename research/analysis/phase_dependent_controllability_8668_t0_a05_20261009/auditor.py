"""Independent raw-only auditor. Does not import candidate.py."""

import copy
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "8668-a05-raw-v1"
PRE_EMIT = {"PROPOSED", "QUEUED"}


def _reference(view, active, refine_phase):
    expected_request_kind = {"CANCEL_ACK": "CANCEL_REQUEST",
                             "EFFECT_ACK": "EFFECT_REQUEST"}
    accepted_kinds = []
    for receipt in sorted(view.get("receipts", []),
                          key=lambda item: item.get("arrival_order", 0)):
        expected_kind = expected_request_kind.get(receipt.get("kind"))
        if expected_kind is None:
            continue
        for request in view.get("requests", []):
            identity_matches = (
                request.get("request_id") == receipt.get("request_id") and
                request.get("kind") == expected_kind and
                request.get("operation_id") == receipt.get("operation_id") == active.get("operation_id") and
                request.get("attempt") == receipt.get("attempt") == active.get("attempt")
            )
            if identity_matches:
                accepted_kinds.append(receipt["kind"])
                break
    distinct = set(accepted_kinds)
    phase = view.get("observed_phase")
    if len(distinct) > 1:
        state = "UNKNOWN"
    elif distinct == {"CANCEL_ACK"}:
        state = "CANCELLED_NO_EFFECT" if (not refine_phase or phase in PRE_EMIT) else "UNKNOWN"
    elif distinct == {"EFFECT_ACK"}:
        state = "EFFECT_CONFIRMED" if (not refine_phase or phase == "CONSUMED") else "UNKNOWN"
    elif refine_phase and phase not in PRE_EMIT:
        state = "UNKNOWN"
    else:
        state = "PENDING"
    return {"status": state,
            "retry_eligible": bool(view.get("retry_requested") and
                                    state == "CANCELLED_NO_EFFECT")}


def _core_errors(raw, design, candidate_input):
    errors = []
    cases = design["cases"]
    expected_input = {
        "schema": "8668-a05-input-v1",
        "allocation": design["allocation"],
        "base_commit": design["base_commit"],
        "active": design["active"],
        "cases": [{"id": case["id"], "view": case["view"]} for case in cases],
    }
    if candidate_input != expected_input:
        errors.append("candidate_input")
    if (type(raw) is not dict or raw.get("schema") != SCHEMA or
            raw.get("allocation") != design["allocation"] or
            raw.get("base_commit") != design["base_commit"]):
        return ["identity"]
    rows = raw.get("rows")
    if type(rows) is not list or len(rows) != len(cases) or raw.get("row_count") != len(rows):
        return ["coverage"]
    for index, (row, case) in enumerate(zip(rows, cases)):
        if type(row) is not dict or row.get("case_id") != case["id"]:
            errors.append(f"case:{index}")
            continue
        view = case["view"]
        if row.get("view") != view or "actual_effect_committed" in row:
            errors.append(f"visible_input:{case['id']}")
        if row.get("phase_refined") != _reference(view, design["active"], True):
            errors.append(f"phase_refined:{case['id']}")
        if row.get("phase_blind_request_bound") != _reference(view, design["active"], False):
            errors.append(f"phase_blind:{case['id']}")
    return errors


def audit(raw, design, candidate_input):
    errors = _core_errors(raw, design, candidate_input)
    rows = raw.get("rows", []) if type(raw) is dict else []
    cases = design.get("cases", [])
    row_by_id = {row.get("case_id"): row for row in rows if type(row) is dict}
    case_by_id = {case["id"]: case for case in cases}
    phase_false = phase_unsafe = blind_false = blind_unsafe = 0
    for case in cases:
        row = row_by_id.get(case["id"], {})
        truth = case["actual_effect_committed"]
        phase_result = row.get("phase_refined", {})
        blind_result = row.get("phase_blind_request_bound", {})
        phase_false += phase_result.get("status") == "CANCELLED_NO_EFFECT" and truth
        phase_unsafe += phase_result.get("retry_eligible") is True and truth
        blind_false += blind_result.get("status") == "CANCELLED_NO_EFFECT" and truth
        blind_unsafe += blind_result.get("retry_eligible") is True and truth
    pair_ids = ("emitted_ack_effect_absent", "emitted_ack_effect_committed")
    identical_pair = case_by_id[pair_ids[0]]["view"] == case_by_id[pair_ids[1]]["view"]
    pair_unknown = identical_pair and all(
        row_by_id.get(identifier, {}).get("phase_refined") ==
        {"status": "UNKNOWN", "retry_eligible": False} for identifier in pair_ids)
    queued_positive = row_by_id.get("queued_cancel_positive_control", {}).get("phase_refined") == {
        "status": "CANCELLED_NO_EFFECT", "retry_eligible": True}
    blind_witness = (
        row_by_id.get("emitted_ack_effect_committed", {}).get("phase_blind_request_bound") ==
        {"status": "CANCELLED_NO_EFFECT", "retry_eligible": True} and
        case_by_id["emitted_ack_effect_committed"]["actual_effect_committed"] is True
    )
    mutations = []
    mutation_specs = (
        ("phase_changed", lambda item: item["rows"][1]["view"].__setitem__("observed_phase", "QUEUED")),
        ("status_changed", lambda item: item["rows"][2]["phase_refined"].__setitem__("retry_eligible", True)),
        ("row_removed", lambda item: item["rows"].pop()),
    )
    for name, change in mutation_specs:
        altered = copy.deepcopy(raw)
        change(altered)
        mutations.append({"name": name,
                          "rejected": bool(_core_errors(altered, design, candidate_input))})
    valid = (
        not errors and phase_false == 0 and phase_unsafe == 0 and pair_unknown and
        queued_positive and blind_witness and all(item["rejected"] for item in mutations)
    )
    return {
        "valid": valid,
        "errors": errors,
        "case_count": len(cases),
        "phase_refined_false_no_effect_count": phase_false,
        "phase_refined_unsafe_retry_count": phase_unsafe,
        "phase_blind_false_no_effect_count": blind_false,
        "phase_blind_unsafe_retry_count": blind_unsafe,
        "identical_emitted_views_remain_unknown": pair_unknown,
        "queued_positive_control": queued_positive,
        "phase_blind_committed_effect_witness": blind_witness,
        "mutation_controls": {"rejected": sum(item["rejected"] for item in mutations),
                              "total": len(mutations), "results": mutations},
    }


def main():
    root = Path(__file__).resolve().parent
    freeze = json.loads((root / "FREEZE.json").read_text())
    if freeze.get("base_commit") != "a6343bb76e4dc0a4afa32a29c8a485a617faeff8":
        raise ValueError("unexpected base commit")
    for name, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("frozen source mismatch: " + name)
    raw = json.loads((root / "results" / "candidate_raw.json").read_text())
    design = json.loads((root / "design.json").read_text())
    candidate_input = json.loads((root / "candidate_input.json").read_text())
    result = audit(raw, design, candidate_input)
    result["schema"] = "8668-a05-audit-v1"
    result["allocation"] = freeze["allocation"]
    result["status"] = "PASS_METHOD_SCOPED" if result["valid"] else "FAIL_METHOD"
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
