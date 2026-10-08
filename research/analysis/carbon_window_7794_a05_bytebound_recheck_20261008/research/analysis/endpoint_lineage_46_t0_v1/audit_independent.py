#!/usr/bin/env python3
"""Independent vertex-enumeration auditor; does not import reducer.py."""

from fractions import Fraction
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
fixture = json.loads((HERE / "fixtures.json").read_text())
raw = json.loads((HERE / "candidate_stdout.json").read_text())
raw_cases = {row["case"]: row for row in raw["cases"]}


def ticks(item):
    lo, hi = Fraction(item["lo"]), Fraction(item["hi"])
    return sorted({lo, hi})


def same_clock_vertices(case):
    ids = sorted(case["endpoints"])
    domains = [ticks(case["endpoints"][key]) for key in ids]
    values = []
    for row in itertools.product(*domains):
        ts = dict(zip(ids, row))
        total = sum((ts[end] - ts[start] for start, end in case["segments"]), Fraction(0))
        values.append(total)
    return min(values), max(values)


def cross_clock_vertices(case):
    ep = case["endpoints"]
    amap = case["affine_map"]
    projected = []
    for rate, offset in itertools.product(
            (Fraction(amap["rate_lo"]), Fraction(amap["rate_hi"])),
            (Fraction(amap["offset_lo"]), Fraction(amap["offset_hi"]))):
        t0 = Fraction(ep["t0"]["lo"])
        local_middle = Fraction(ep["t1_src"]["lo"])
        t1_ref = rate * local_middle + offset
        t2 = Fraction(ep["t2"]["lo"])
        total = (t1_ref - t0) + (t2 - t1_ref)
        projected.append(total)
    return min(projected), max(projected)


expected = {
    "shared_same_clock_boundary": (Fraction(19), Fraction(21), 2),
    "independent_middle_measurements": (Fraction(17), Fraction(23), 2),
    "cross_clock_shared_affine_map": (Fraction(60), Fraction(60), 2),
}
for case in fixture["cases"][:3]:
    bounds = cross_clock_vertices(case) if "affine_map" in case else same_clock_vertices(case)
    exp_lo, exp_hi, segment_count = expected[case["name"]]
    assert bounds == (exp_lo, exp_hi), (case["name"], bounds)
    row = raw_cases[case["name"]]
    assert row["status"] == "NUMERIC"
    assert tuple(map(Fraction, row["joint"])) == bounds
    assert len(row["segments"]) == segment_count
    assert all(Fraction(segment[0]) <= Fraction(segment[1]) for segment in row["segments"])

for name, status in (("incompatible_epoch", "HOLD_INCOMPATIBLE_CLOCK"),
                     ("missing_endpoint", "HOLD_MISSING_ENDPOINT")):
    row = raw_cases[name]
    assert row["status"] == status and row["joint"] is None and row["naive_sum"] is None

a = raw_cases["near_tie"]["A"]
b = raw_cases["near_tie"]["B"]
a_bounds, b_bounds = tuple(map(Fraction, a)), tuple(map(Fraction, b))
def endpoint_pair_vertices(pair):
    ids = sorted(pair["endpoints"])
    domains = [ticks(pair["endpoints"][key]) for key in ids]
    results = []
    for row in itertools.product(*domains):
        ts = dict(zip(ids, row))
        results.append(ts[pair["segments"][0][1]] - ts[pair["segments"][0][0]])
    return min(results), max(results), len(results)

expected_a = endpoint_pair_vertices(fixture["near_tie"]["A"])
expected_b = endpoint_pair_vertices(fixture["near_tie"]["B"])
assert a_bounds == expected_a[:2] == (Fraction(9), Fraction(12))
assert b_bounds == expected_b[:2] == (Fraction(10), Fraction(14))
assert raw_cases["near_tie"]["nominal_center_winner"] == "A"
assert raw_cases["near_tie"]["robust_decision"] == "UNRESOLVED_OVERLAP"
assert Fraction(raw_cases["near_tie"]["reverse_order_witness"]["A"]) == 12
assert Fraction(raw_cases["near_tie"]["reverse_order_witness"]["B"]) == 10

print(json.dumps({"audit": "PASS_ENDPOINT_LINEAGE_T0_SCOPED", "cases": 6,
                  "vertices_checked": 8 + 16 + 4 + expected_a[2] + expected_b[2], "mismatches": 0,
                  "errors": [], "scope": "synthetic exact finite method only"},
                 sort_keys=True, separators=(",", ":")))
