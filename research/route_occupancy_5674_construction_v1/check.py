"""Finite route-induced occupancy construction; no GUI or empirical claim."""

from fractions import Fraction as F
from itertools import product
import json


HORIZON = 3
START = "fresh"
STATES = ("fresh", "recovery")
KERNEL_A = {"fresh": {"fresh": F(9, 10), "recovery": F(1, 10)},
            "recovery": {"fresh": F(1, 2), "recovery": F(1, 2)}}
KERNEL_B = {"fresh": {"fresh": F(3, 5), "recovery": F(2, 5)},
            "recovery": {"fresh": F(1, 4), "recovery": F(3, 4)}}


def recurrence(kernel):
    distribution = {START: F(1)}
    for _ in range(HORIZON):
        distribution = {target: sum(distribution.get(source, F(0)) *
                                    kernel[source][target] for source in STATES)
                        for target in STATES}
    return distribution


def enumeration(kernel):
    totals = {state: F(0) for state in STATES}
    for path in product(STATES, repeat=HORIZON):
        probability = F(1)
        previous = START
        for state in path:
            probability *= kernel[previous][state]
            previous = state
        totals[path[-1]] += probability
    return totals


def check_kernel(kernel):
    return all(set(row) == set(STATES) and
               all(p >= 0 for p in row.values()) and sum(row.values()) == 1
               for row in kernel.values())


assert check_kernel(KERNEL_A) and check_kernel(KERNEL_B)
for kernel in (KERNEL_A, KERNEL_B):
    assert recurrence(kernel) == enumeration(kernel)

a = recurrence(KERNEL_A)
b = recurrence(KERNEL_B)
null = recurrence(KERNEL_A)
assert sum(a.values()) == sum(b.values()) == 1
assert b["recovery"] > a["recovery"]
assert null["recovery"] == a["recovery"]

# State-specific burden is 1 in recovery and 0 in fresh. Reusing A's state
# distribution to predict B's burden omits states induced by B's route.
source_weighted_b = a["recovery"]
direct_b = b["recovery"]
gap = direct_b - source_weighted_b
assert gap > 0

print(json.dumps({
    "scope": "finite construction only; no GUI/model or live route effect",
    "horizon": HORIZON,
    "path_count_per_route": len(STATES) ** HORIZON,
    "a_recovery_probability": str(a["recovery"]),
    "b_recovery_probability": str(b["recovery"]),
    "a_weighted_b_burden": str(source_weighted_b),
    "direct_b_burden": str(direct_b),
    "difference": str(gap),
    "null_equal_kernel_difference": str(null["recovery"] - a["recovery"]),
    "recurrence_enumeration_agree": True,
    "all_pass": True,
}, indent=2))

