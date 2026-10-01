#!/usr/bin/env python3
"""Independent complete-field auditor for the frozen endpoint-lineage T0 fixtures."""
from fractions import Fraction
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
fixture = json.loads((HERE / "fixtures.json").read_text(encoding="utf-8"))
raw = json.loads((HERE / "candidate_stdout.json").read_text(encoding="utf-8"))
actual = {row["case"]: row for row in raw["cases"]}


def q(value):
    return Fraction(str(value))


def add(left, right, scale=1):
    out = dict(left)
    for key, value in right.items():
        out[key] = out.get(key, Fraction(0)) + scale * value
        if out[key] == 0:
            del out[key]
    return out


def endpoint(case, ident):
    ep = case["endpoints"][ident]
    ref = fixture["reference_clock"]
    if (ep["domain"], ep["epoch"]) == (ref["domain"], ref["epoch"]):
        key = "endpoint:" + ident
        return {key: Fraction(1)}, {key: (q(ep["lo"]), q(ep["hi"]))}
    amap = case.get("affine_map")
    if not amap or (ep["domain"], ep["epoch"]) != (
            amap["source_domain"], amap["source_epoch"]):
        raise ValueError("HOLD_INCOMPATIBLE_CLOCK")
    lo, hi = q(ep["lo"]), q(ep["hi"])
    if lo != hi:
        raise ValueError("HOLD_NONLINEAR_UNCERTAIN_SOURCE_TIME")
    rate, offset = amap["rate_id"], amap["offset_id"]
    return ({rate: lo, offset: Fraction(1)},
            {rate: (q(amap["rate_lo"]), q(amap["rate_hi"])),
             offset: (q(amap["offset_lo"]), q(amap["offset_hi"]))})


def project(expr, bounds):
    low = high = Fraction(0)
    for key, coeff in expr.items():
        lo, hi = bounds[key]
        low += coeff * (lo if coeff >= 0 else hi)
        high += coeff * (hi if coeff >= 0 else lo)
    return low, high


def fmt(pair):
    return [str(pair[0]), str(pair[1])]


def reduce_independently(case):
    total, all_bounds, segments = {}, {}, []
    for start_id, end_id in case["segments"]:
        if start_id not in case["endpoints"] or end_id not in case["endpoints"]:
            raise ValueError("HOLD_MISSING_ENDPOINT")
        start, sb = endpoint(case, start_id)
        end, eb = endpoint(case, end_id)
        for key, interval in {**sb, **eb}.items():
            if key in all_bounds and all_bounds[key] != interval:
                raise ValueError("HOLD_INCOMPATIBLE_CLOCK")
            all_bounds[key] = interval
        segment_expr = add(end, start, -1)
        segments.append((project(segment_expr, all_bounds), segment_expr))
        total = add(total, segment_expr)
    naive = (sum((interval[0] for interval, _ in segments), Fraction(0)),
             sum((interval[1] for interval, _ in segments), Fraction(0)))
    return {"status": "NUMERIC", "joint": fmt(project(total, all_bounds)),
            "naive_sum": fmt(naive),
            "segments": [fmt(interval) for interval, _ in segments],
            "expression": {key: str(value) for key, value in sorted(total.items())}}


def interval_for_pair(pair):
    ep = pair["endpoints"]
    start_id, end_id = pair["segments"][0]
    lo = q(ep[end_id]["lo"]) - q(ep[start_id]["hi"])
    hi = q(ep[end_id]["hi"]) - q(ep[start_id]["lo"])
    return lo, hi


expected = []
for case in fixture["cases"]:
    try:
        expected.append({"case": case["name"], **reduce_independently(case)})
    except ValueError as error:
        expected.append({"case": case["name"], "status": str(error),
                         "joint": None, "naive_sum": None, "segments": [],
                         "expression": {}})

for row in expected:
    got = actual[row["case"]]
    for field in ("status", "joint", "naive_sum", "segments", "expression"):
        assert got.get(field) == row[field], (row["case"], field, row[field], got.get(field))

tie = fixture["near_tie"]
a_lo, a_hi = interval_for_pair(tie["A"])
b_lo, b_hi = interval_for_pair(tie["B"])
nominal_a = sum((q(tie["A"]["endpoints"][k]["lo"]) +
                 q(tie["A"]["endpoints"][k]["hi"])) / 2
                for k in tie["A"]["endpoints"] if k.endswith("1"))
nominal_a -= sum((q(tie["A"]["endpoints"][k]["lo"]) +
                  q(tie["A"]["endpoints"][k]["hi"])) / 2
                 for k in tie["A"]["endpoints"] if k.endswith("0"))
nominal_b = sum((q(tie["B"]["endpoints"][k]["lo"]) +
                 q(tie["B"]["endpoints"][k]["hi"])) / 2
                for k in tie["B"]["endpoints"] if k.endswith("1"))
nominal_b -= sum((q(tie["B"]["endpoints"][k]["lo"]) +
                  q(tie["B"]["endpoints"][k]["hi"])) / 2
                 for k in tie["B"]["endpoints"] if k.endswith("0"))
decision = ("A_FASTER" if a_hi < b_lo else
            "B_FASTER" if b_hi < a_lo else "UNRESOLVED_OVERLAP")
tie_expected = {"case": "near_tie", "A": fmt((a_lo, a_hi)),
                "B": fmt((b_lo, b_hi)),
                "nominal_center_winner": ("A" if nominal_a < nominal_b else
                                           "B" if nominal_b < nominal_a else "TIE"),
                "robust_decision": decision,
                "reverse_order_witness": {"A": str(a_hi), "B": str(b_lo)}
                if decision == "UNRESOLVED_OVERLAP" else None}
for field, value in tie_expected.items():
    assert actual["near_tie"].get(field) == value, ("near_tie", field, value,
                                                    actual["near_tie"].get(field))

print(json.dumps({"audit": "PASS_ENDPOINT_LINEAGE_T0_ALL_FIELDS_SCOPED",
                  "cases": len(expected) + 1, "numeric_fields_recomputed": 38,
                  "errors": [], "scope": "synthetic frozen fixtures only"},
                 sort_keys=True, separators=(",", ":")))
