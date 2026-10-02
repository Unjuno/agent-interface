#!/usr/bin/env python3
"""Candidate exact endpoint-lineage interval reducer for Issue #46 T0."""

from fractions import Fraction
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def F(value):
    return Fraction(str(value))


def add_expr(left, right, scale=1):
    result = dict(left)
    for key, value in right.items():
        result[key] = result.get(key, Fraction(0)) + scale * value
        if result[key] == 0:
            del result[key]
    return result


def endpoint_expr(endpoint_id, endpoint, affine_map):
    if endpoint["domain"] == "mono-ref" and endpoint["epoch"] == "epoch-r":
        return {"endpoint:" + endpoint_id: Fraction(1)}, {
            "endpoint:" + endpoint_id: (F(endpoint["lo"]), F(endpoint["hi"]))}
    if not affine_map:
        raise ValueError("HOLD_INCOMPATIBLE_CLOCK")
    if (endpoint["domain"], endpoint["epoch"]) != (
            affine_map["source_domain"], affine_map["source_epoch"]):
        raise ValueError("HOLD_INCOMPATIBLE_CLOCK")
    local_lo, local_hi = F(endpoint["lo"]), F(endpoint["hi"])
    if local_lo != local_hi:
        raise ValueError("HOLD_NONLINEAR_UNCERTAIN_SOURCE_TIME")
    terms = {affine_map["rate_id"]: local_lo,
             affine_map["offset_id"]: Fraction(1)}
    bounds = {affine_map["rate_id"]: (F(affine_map["rate_lo"]), F(affine_map["rate_hi"])),
              affine_map["offset_id"]: (F(affine_map["offset_lo"]), F(affine_map["offset_hi"]))}
    return terms, bounds


def project(expr, bounds):
    low = high = Fraction(0)
    for variable, coefficient in expr.items():
        lo, hi = bounds[variable]
        low += coefficient * (lo if coefficient >= 0 else hi)
        high += coefficient * (hi if coefficient >= 0 else lo)
    return low, high


def reduce_case(case):
    total, bounds, segment_intervals = {}, {}, []
    try:
        for start_id, end_id in case["segments"]:
            if start_id not in case["endpoints"] or end_id not in case["endpoints"]:
                raise ValueError("HOLD_MISSING_ENDPOINT")
            start = case["endpoints"][start_id]
            end = case["endpoints"][end_id]
            if (start["domain"], start["epoch"]) == (end["domain"], end["epoch"]):
                for endpoint_id in (start_id, end_id):
                    ep = case["endpoints"][endpoint_id]
                    expr = {"endpoint:" + endpoint_id: Fraction(1)}
                    bounds["endpoint:" + endpoint_id] = (F(ep["lo"]), F(ep["hi"]))
                    if endpoint_id == start_id:
                        start_expr = expr
                    else:
                        end_expr = expr
            else:
                start_expr, start_bounds = endpoint_expr(start_id, start, case.get("affine_map"))
                end_expr, end_bounds = endpoint_expr(end_id, end, case.get("affine_map"))
                bounds.update(start_bounds)
                bounds.update(end_bounds)
            interval_expr = add_expr(end_expr, start_expr, -1)
            lo, hi = project(interval_expr, bounds)
            segment_intervals.append((lo, hi))
            total = add_expr(total, interval_expr)
        joint = project(total, bounds)
        naive = (sum((x[0] for x in segment_intervals), Fraction(0)),
                 sum((x[1] for x in segment_intervals), Fraction(0)))
        return {"status": "NUMERIC", "joint": joint, "naive_sum": naive,
                "segments": segment_intervals, "expression": total}
    except ValueError as error:
        return {"status": str(error), "joint": None, "naive_sum": None,
                "segments": segment_intervals, "expression": None}


def fmt_interval(value):
    if value is None:
        return None
    return [str(value[0]), str(value[1])]


def run():
    fixture = json.loads((HERE / "fixtures.json").read_text())
    cases = []
    for case in fixture["cases"]:
        result = reduce_case(case)
        cases.append({"case": case["name"], "status": result["status"],
                      "joint": fmt_interval(result["joint"]),
                      "naive_sum": fmt_interval(result["naive_sum"]),
                      "segments": [fmt_interval(x) for x in result["segments"]],
                      "expression": {k: str(v) for k, v in sorted((result["expression"] or {}).items())}})
    a = reduce_case(fixture["near_tie"]["A"])
    b = reduce_case(fixture["near_tie"]["B"])
    a_mid = sum(a["joint"], Fraction(0)) / 2
    b_mid = sum(b["joint"], Fraction(0)) / 2
    if a["joint"][1] < b["joint"][0]:
        decision = "A_FASTER"
    elif b["joint"][1] < a["joint"][0]:
        decision = "B_FASTER"
    else:
        decision = "UNRESOLVED_OVERLAP"
    cases.append({"case": "near_tie", "A": fmt_interval(a["joint"]), "B": fmt_interval(b["joint"]),
                  "nominal_center_winner": "A" if a_mid < b_mid else "B" if b_mid < a_mid else "TIE",
                  "robust_decision": decision,
                  "reverse_order_witness": {"A": str(a["joint"][1]), "B": str(b["joint"][0])}
                  if decision == "UNRESOLVED_OVERLAP" else None})
    print(json.dumps({"schema": "endpoint-lineage-46-t0-result-v1", "cases": cases},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    run()
