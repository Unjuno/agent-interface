"""Raw-result audit for #5674; never imports or calls the candidate program."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path


RESULT = Path(__file__).with_name("result.json")
if not RESULT.exists():
    RESULT = Path(__file__).with_name("issue5674_result.json")
raw = json.loads(RESULT.read_text())
assert raw["horizon"] == 3

# Independently stated transition matrices. Index 0=fresh, 1=recovery.
matrices = (((9, 10), (1, 10), (1, 2), (1, 2)),
            ((3, 5), (2, 5), (1, 4), (3, 4)))


def risk(terms):
    ff, fr, rf, rr = map(lambda pair: Fraction(*pair), terms)
    assert ff + fr == rf + rr == 1
    total = Fraction(0)
    count = 0
    for path in product((0, 1), repeat=3):
        if path[-1] != 1:
            continue
        prior = 0
        weight = Fraction(1)
        for state in path:
            weight *= ((ff, fr), (rf, rr))[prior][state]
            prior = state
        total += weight
        count += 1
    assert count == 4
    return total


a, b = [risk(m) for m in matrices]
expected = {
    "path_count_per_route": 8,
    "a_recovery_probability": str(a),
    "b_recovery_probability": str(b),
    "a_weighted_b_burden": str(a),
    "direct_b_burden": str(b),
    "difference": str(b - a),
    "null_equal_kernel_difference": "0",
}
assert all(raw[key] == value for key, value in expected.items())
assert raw["scope"] == "finite construction only; no GUI/model or live route effect"
assert raw["recurrence_enumeration_agree"] is True and raw["all_pass"] is True

def accepted(record):
    return all(record.get(key) == value for key, value in expected.items()) and (
        record.get("scope") == raw["scope"] and
        record.get("recurrence_enumeration_agree") is True and
        record.get("all_pass") is True)


bad_gap = dict(raw, difference="0")
bad_scope = dict(raw, scope="empirical GUI PASS")
bad_null = dict(raw, null_equal_kernel_difference="1/10")
assert not accepted(bad_gap)
assert not accepted(bad_scope)
assert not accepted(bad_null)
print(json.dumps({"audit": "RAW_ONLY_SCOPED_PASS",
                  "candidate_imported": False,
                  "independent_path_enumeration": True,
                  "corruption_controls_rejected": 3,
                  "empirical_hypothesis": "UNTESTED"}, indent=2))

