#!/usr/bin/env python3
"""Independent raw-only finite-state auditor; does not import candidate code."""
import itertools
import json
import sys
from pathlib import Path


def expected_reason(fixture, case):
    if case.get("mutation") == "relation_sign":
        return "relation_sign_invalid"
    if case.get("action_units", fixture["units"]) != fixture["units"]:
        return "unit_mismatch"
    if case.get("action_frame_id", fixture["frame_id"]) != fixture["frame_id"]:
        return "frame_mismatch"
    if case.get("action_epoch", fixture["source_epoch"]) != fixture["source_epoch"]:
        return "stale_epoch"
    if case.get("action_target_id", fixture["target"]["id"]) != fixture["target"]["id"]:
        return "target_identity_mismatch"
    if "shift_bounds_override" in case:
        lo, hi = case["shift_bounds_override"]
        if lo > hi:
            return "contradictory_zone"
    return None


def enumerate_oracle(fixture, case):
    if expected_reason(fixture, case):
        return []
    shifts = fixture["shift_values"]
    errors = case["error_values"]
    tx, ty = fixture["target"]["center"]
    fx, fy = case.get("forbidden_center", fixture["forbidden"]["center"])
    common = case["mode"] == "common"
    states = []
    for sx, sy, ex, ey in itertools.product(shifts, shifts, errors, errors):
        action_shifts = ((sx, sy),) if common else itertools.product(shifts, shifts)
        for sax, say in action_shifts:
            target = [tx + sx, ty + sy]
            action = [tx + sax + ex, ty + say + ey]
            forbidden = [fx + sx, fy + sy]
            hit = all(abs(action[i] - target[i]) <= fixture["target"]["half_width"] for i in range(2))
            collision = all(abs(action[i] - forbidden[i]) <= fixture["forbidden"]["half_width"] for i in range(2))
            states.append({"target_id": fixture["target"]["id"], "target": target,
                           "action": action, "forbidden_id": fixture["forbidden"]["id"],
                           "forbidden": forbidden, "target_hit": hit,
                           "forbidden_hit": collision, "safe": hit and not collision})
    return states


def inside(actual, claimed):
    return claimed is not None and claimed[0] <= actual <= claimed[1]


def audit(fixture, truth, raw):
    assert raw.get("schema") == "relational-coordinate-raw-v1", "raw schema mismatch"
    cases = fixture["cases"]
    rows = raw.get("rows")
    assert isinstance(rows, list), "rows missing"
    assert [r.get("id") for r in rows] == [c["id"] for c in cases], "row roster/order mismatch"
    expected = truth["expected"]
    assert set(expected) == {c["id"] for c in cases}, "truth roster mismatch"
    findings = []
    for case, row in zip(cases, rows):
        ident = case["id"]
        oracle = enumerate_oracle(fixture, case)
        oracle_safe = bool(oracle) and all(s["safe"] for s in oracle)
        first_bad = next((s for s in oracle if not s["safe"]), None)
        assert row.get("concrete_states") == oracle, f"{ident}: concrete state mismatch"
        if oracle:
            assert row.get("concrete_state_count") == len(oracle), f"{ident}: concrete count mismatch"
            assert row.get("first_counterexample") == first_bad, f"{ident}: counterexample mismatch"
            for state in oracle:
                dx_t = state["action"][0] - state["target"][0]
                dy_t = state["action"][1] - state["target"][1]
                dx_f = state["action"][0] - state["forbidden"][0]
                dy_f = state["action"][1] - state["forbidden"][1]
                for field, value in (("action_minus_target_x", dx_t), ("action_minus_target_y", dy_t),
                                     ("action_minus_forbidden_x", dx_f), ("action_minus_forbidden_y", dy_f)):
                    assert inside(value, row.get("dbm_bounds", {}).get(field)), f"{ident}: DBM unsound {field}"
        reason = expected_reason(fixture, case)
        wanted = expected[ident]
        assert oracle_safe == wanted["oracle_safe"], f"{ident}: independent oracle disagrees with truth"
        assert row.get("box_admit") is wanted["box_admit"], f"{ident}: BOX truth mismatch"
        assert row.get("relational_admit") is wanted["relational_admit"], f"{ident}: relational truth mismatch"
        actual_reason = reason or ("relational_safe" if row.get("relational_admit") else "unknown_geometry")
        assert row.get("reason") == actual_reason == wanted["reason"], f"{ident}: reason mismatch"
        if row.get("box_admit") or row.get("relational_admit"):
            assert oracle_safe, f"{ident}: false admission"
        findings.append({"id": ident, "state_count": len(oracle), "oracle_safe": oracle_safe,
                         "box_admit": row["box_admit"], "relational_admit": row["relational_admit"],
                         "result": "PASS"})
    return {"schema": "relational-coordinate-audit-v1", "result": "PASS_METHOD_SCOPED",
            "audited_rows": len(findings), "findings": findings}


def main(fixture_path, truth_path, raw_path, audit_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    truth = json.loads(Path(truth_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    result = audit(fixture, truth, raw)
    Path(audit_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit.py FIXTURE.json TRUTH.json RAW.json AUDIT.json")
    main(*sys.argv[1:])
