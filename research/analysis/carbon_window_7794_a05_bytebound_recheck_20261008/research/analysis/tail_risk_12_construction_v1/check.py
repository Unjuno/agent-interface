"""Finite CVaR construction for Issue #12; not empirical GUI evidence."""

from fractions import Fraction
import json


def worst_tail_mean(losses, tail_count):
    assert len(losses) == 100 and 0 < tail_count <= len(losses)
    assert all(x >= 0 for x in losses)
    return Fraction(sum(sorted(losses, reverse=True)[:tail_count]), tail_count)


def closed_form_binary(failure_count, tail_count):
    assert 0 <= failure_count <= 100
    return Fraction(min(failure_count, tail_count), tail_count)


tail_count = 10
binary_a = [1] * 5 + [0] * 95
binary_b = [1] * 2 + [0] * 98
severe_b = [10] * 2 + [0] * 98

assert worst_tail_mean(binary_a, tail_count) == closed_form_binary(5, tail_count)
assert worst_tail_mean(binary_b, tail_count) == closed_form_binary(2, tail_count)
assert worst_tail_mean(binary_a, tail_count) > worst_tail_mean(binary_b, tail_count)
assert worst_tail_mean(severe_b, tail_count) > worst_tail_mean(binary_a, tail_count)

# Exhaustive binary control: CVaR at fixed tail mass never reverses failure-rate
# ordering, including the saturated region where all tail entries are failures.
for count_a in range(101):
    for count_b in range(count_a, 101):
        assert closed_form_binary(count_a, tail_count) <= closed_form_binary(
            count_b, tail_count)

print(json.dumps({
    "scope": "authored finite losses, not observed GUI safety",
    "samples_per_route": 100,
    "tail_count": tail_count,
    "binary_a_failure_rate": "5/100",
    "binary_b_failure_rate": "2/100",
    "binary_a_tail_loss": str(worst_tail_mean(binary_a, tail_count)),
    "binary_b_tail_loss": str(worst_tail_mean(binary_b, tail_count)),
    "severity_b_tail_loss": str(worst_tail_mean(severe_b, tail_count)),
    "binary_monotonic_pairs_checked": 5151,
    "all_pass": True,
}, indent=2))

