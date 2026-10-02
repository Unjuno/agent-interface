#!/usr/bin/env python3
"""Finite BOX / DBM / exhaustive comparison. Formal run is separately gated."""
import itertools
import json
import sys
from pathlib import Path

INF = 10**6


def add(dbm, left, right, bound):
    dbm[left][right] = min(dbm[left][right], bound)


def close(dbm):
    for k in range(len(dbm)):
        for i in range(len(dbm)):
            for j in range(len(dbm)):
                dbm[i][j] = min(dbm[i][j], dbm[i][k] + dbm[k][j])
    return dbm


def bound_var(dbm, idx, lo, hi):
    add(dbm, idx, 0, hi)
    add(dbm, 0, idx, -lo)


def eq_offset(dbm, value_idx, shift_idx, offset):
    add(dbm, value_idx, shift_idx, offset)
    add(dbm, shift_idx, value_idx, -offset)


def diff_interval(dbm, left, right):
    return [-dbm[right][left], dbm[left][right]]


def guard_reason(fixture, case):
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
    if "shift_bounds_override" in case and case["shift_bounds_override"][0] > case["shift_bounds_override"][1]:
        return "contradictory_zone"
    return None


def enumerate_states(fixture, case):
    if guard_reason(fixture, case):
        return []
    shifts, errors = fixture["shift_values"], case["error_values"]
    tx, ty = fixture["target"]["center"]
    fx, fy = case.get("forbidden_center", fixture["forbidden"]["center"])
    states = []
    for sx, sy, ex, ey in itertools.product(shifts, shifts, errors, errors):
        action_shifts = ((sx, sy),) if case["mode"] == "common" else itertools.product(shifts, shifts)
        for sax, say in action_shifts:
            target, action, forbidden = [tx + sx, ty + sy], [tx + sax + ex, ty + say + ey], [fx + sx, fy + sy]
            hit = all(abs(action[i] - target[i]) <= fixture["target"]["half_width"] for i in range(2))
            collision = all(abs(action[i] - forbidden[i]) <= fixture["forbidden"]["half_width"] for i in range(2))
            states.append({"target_id": fixture["target"]["id"], "target": target, "action": action,
                           "forbidden_id": fixture["forbidden"]["id"], "forbidden": forbidden,
                           "target_hit": hit, "forbidden_hit": collision, "safe": hit and not collision})
    return states


def box_bounds(fixture, case):
    slo, shi = min(fixture["shift_values"]), max(fixture["shift_values"])
    tx, ty = fixture["target"]["center"]
    fx, fy = case.get("forbidden_center", fixture["forbidden"]["center"])
    elo, ehi = min(case["error_values"]), max(case["error_values"])
    txb, tyb = [tx + slo, tx + shi], [ty + slo, ty + shi]
    axb, ayb = [tx + slo + elo, tx + shi + ehi], [ty + slo + elo, ty + shi + ehi]
    fxb, fyb = [fx + slo, fx + shi], [fy + slo, fy + shi]
    return {"action_minus_target_x": [axb[0]-txb[1], axb[1]-txb[0]],
            "action_minus_target_y": [ayb[0]-tyb[1], ayb[1]-tyb[0]],
            "action_minus_forbidden_x": [axb[0]-fxb[1], axb[1]-fxb[0]],
            "action_minus_forbidden_y": [ayb[0]-fyb[1], ayb[1]-fyb[0]]}


def dbm_bounds(fixture, case):
    ix = {"sx":1,"sa":2,"tx":3,"ax":4,"fx":5,"sy":6,"sb":7,"ty":8,"ay":9,"fy":10}
    d = [[0 if i == j else INF for j in range(11)] for i in range(11)]
    lo, hi = min(fixture["shift_values"]), max(fixture["shift_values"])
    for k in (ix["sx"],ix["sy"],ix["sa"],ix["sb"]): bound_var(d,k,lo,hi)
    if case["mode"] == "common":
        for a,b in (("sa","sx"),("sb","sy")):
            add(d,ix[a],ix[b],0); add(d,ix[b],ix[a],0)
    tx,ty=fixture["target"]["center"]; fx,fy=case.get("forbidden_center",fixture["forbidden"]["center"])
    for v,s,o in (("tx","sx",tx),("ty","sy",ty),("fx","sx",fx),("fy","sy",fy)):
        eq_offset(d,ix[v],ix[s],o)
    elo,ehi=min(case["error_values"]),max(case["error_values"])
    for a,s,o in (("ax","sa",tx),("ay","sb",ty)):
        add(d,ix[a],ix[s],o+ehi); add(d,ix[s],ix[a],-(o+elo))
    close(d)
    return {"action_minus_target_x":diff_interval(d,ix["ax"],ix["tx"]),
            "action_minus_target_y":diff_interval(d,ix["ay"],ix["ty"]),
            "action_minus_forbidden_x":diff_interval(d,ix["ax"],ix["fx"]),
            "action_minus_forbidden_y":diff_interval(d,ix["ay"],ix["fy"])}


def safe(bounds, target_half, forbidden_half):
    in_target = all(bounds[k][0] >= -target_half and bounds[k][1] <= target_half
                    for k in ("action_minus_target_x","action_minus_target_y"))
    separated = any(bounds[k][1] < -forbidden_half or bounds[k][0] > forbidden_half
                    for k in ("action_minus_forbidden_x","action_minus_forbidden_y"))
    return in_target and separated


def main(fixture_path, out_path):
    fixture=json.loads(Path(fixture_path).read_text(encoding="utf-8")); rows=[]
    for case in fixture["cases"]:
        reason=guard_reason(fixture,case)
        if reason:
            rows.append({"id":case["id"],"box_admit":False,"relational_admit":False,"exact_oracle_safe":False,
                         "reason":reason,"concrete_states":[],"box_bounds":None,"dbm_bounds":None,"first_counterexample":None})
            continue
        states=enumerate_states(fixture,case); exact=bool(states) and all(s["safe"] for s in states)
        box,rel=box_bounds(fixture,case),dbm_bounds(fixture,case)
        admit_box=safe(box,fixture["target"]["half_width"],fixture["forbidden"]["half_width"])
        admit_rel=safe(rel,fixture["target"]["half_width"],fixture["forbidden"]["half_width"])
        rows.append({"id":case["id"],"box_admit":admit_box,"relational_admit":admit_rel,"exact_oracle_safe":exact,
                     "reason":"relational_safe" if admit_rel else "unknown_geometry","concrete_state_count":len(states),
                     "concrete_states":states,"box_bounds":box,"dbm_bounds":rel,
                     "first_counterexample":next((s for s in states if not s["safe"]),None)})
    Path(out_path).write_text(json.dumps({"schema":"relational-coordinate-raw-v1","rows":rows},sort_keys=True,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv)!=3: raise SystemExit("usage: candidate.py FIXTURE.json RAW.json")
    main(sys.argv[1],sys.argv[2])
