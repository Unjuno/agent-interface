"""Audit #12 retained finite output without importing the construction source."""

from fractions import Fraction
import json
from pathlib import Path


RESULT = Path(__file__).with_name("result.json")
if not RESULT.exists():
    RESULT = Path(__file__).with_name("issue12_tail_result.json")
raw = json.loads(RESULT.read_text())


def tail_sum(failures, severity, n=100, k=10):
    # For f identical positive losses s and 100-f zeroes, the worst k sum
    # contains exactly min(f,k) copies of s.
    assert 0 <= failures <= n and severity >= 0 and 0 < k <= n
    return Fraction(min(failures, k) * severity, k)


expected = {
    "scope": "authored finite losses, not observed GUI safety",
    "samples_per_route": 100,
    "tail_count": 10,
    "binary_a_failure_rate": "5/100",
    "binary_b_failure_rate": "2/100",
    "binary_a_tail_loss": str(tail_sum(5, 1)),
    "binary_b_tail_loss": str(tail_sum(2, 1)),
    "severity_b_tail_loss": str(tail_sum(2, 10)),
    "binary_monotonic_pairs_checked": sum(1 for a in range(101)
                                            for b in range(a, 101)),
    "all_pass": True,
}


def accepted(record):
    return (set(record) == set(expected) and
            all(type(record[key]) is type(value) and record[key] == value
                for key, value in expected.items()))


assert accepted(raw)
assert tail_sum(5, 1) > tail_sum(2, 1)
assert tail_sum(2, 10) > tail_sum(5, 1)
for a in range(101):
    for b in range(a, 101):
        assert tail_sum(a, 1) <= tail_sum(b, 1)

mutations = [
    dict(raw, binary_a_tail_loss="0"),
    dict(raw, severity_b_tail_loss="1/5"),
    dict(raw, binary_monotonic_pairs_checked=5150),
    dict(raw, scope="empirical GUI safety"),
    dict(raw, all_pass=1),
]
assert all(not accepted(m) for m in mutations)
print(json.dumps({"audit": "RAW_ONLY_ARITHMETIC_PASS",
                  "candidate_imported": False,
                  "binary_pairs_independently_checked": 5151,
                  "corruption_controls_rejected": len(mutations),
                  "empirical_result": "UNTESTED"}, indent=2))

