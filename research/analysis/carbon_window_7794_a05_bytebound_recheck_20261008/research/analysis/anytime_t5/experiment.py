#!/usr/bin/env python3
"""Exact T5 enumeration for Issue #5446; no sampling or external dependencies."""
from fractions import Fraction
from itertools import product
import json

HORIZON = 4
BRANCHES = 3
THRESHOLD = Fraction(2)
RHO_VALUES = (Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(1))


def step_vectors(rho):
    """Return (three-bit vector, exact mass) for the shared/private null."""
    out = []
    for bits in product((0, 1), repeat=BRANCHES):
        # Shared component contributes rho/2 to each all-equal vector.
        # Independent component contributes (1-rho)/8 to every vector.
        mass = ((rho * Fraction(1, 2) if len(set(bits)) == 1 else Fraction(0))
                + (1 - rho) * Fraction(1, 2**BRANCHES))
        if mass:
            out.append((bits, mass))
    return out


def wealth_update(value, bit):
    return value * (Fraction(3, 2) if bit else Fraction(1, 2))


def crossing(path, branch):
    wealth = Fraction(1)
    for row in path:
        wealth = wealth_update(wealth, row[branch])
        if wealth >= THRESHOLD:
            return True
    return False


def predictable_adaptive_crossing(path):
    """Choose each branch from history alone; move +1 after success, +2 after failure."""
    wealth = Fraction(1)
    branch = 0
    for row in path:
        bit = row[branch]
        wealth = wealth_update(wealth, bit)
        if wealth >= THRESHOLD:
            return True
        branch = (branch + (1 if bit else 2)) % BRANCHES
    return False


def summarize(rho):
    vectors = step_vectors(rho)
    results = {name: Fraction(0) for name in (
        "fixed_A_anytime", "posthoc_max_branch_anytime", "fixed_equal_mixture_anytime",
        "predictable_adaptive_branch_anytime", "fixed_A_final_only",
    )}
    total = Fraction(0)
    for choices in product(vectors, repeat=HORIZON):
        path = tuple(item[0] for item in choices)
        mass = Fraction(1)
        for _, p in choices:
            mass *= p
        total += mass
        branch_cross = [crossing(path, b) for b in range(BRANCHES)]
        # A fixed convex mixture of valid branch wealth martingales is itself a
        # martingale. Test its running value, not a post-hoc max of branch wealths.
        mixture = [Fraction(1)] * BRANCHES
        mixture_hit = False
        for row in path:
            mixture = [wealth_update(w, bit) for w, bit in zip(mixture, row)]
            if sum(mixture, Fraction(0)) / BRANCHES >= THRESHOLD:
                mixture_hit = True
        results["fixed_A_anytime"] += mass * branch_cross[0]
        results["posthoc_max_branch_anytime"] += mass * any(branch_cross)
        results["fixed_equal_mixture_anytime"] += mass * mixture_hit
        results["predictable_adaptive_branch_anytime"] += mass * predictable_adaptive_crossing(path)
        final_a = Fraction(1)
        for row in path:
            final_a = wealth_update(final_a, row[0])
        results["fixed_A_final_only"] += mass * (final_a >= THRESHOLD)
    assert total == 1
    return {
        "rho": f"{rho.numerator}/{rho.denominator}",
        "path_count_positive_mass": len(vectors) ** HORIZON,
        "total_probability": str(total),
        "false_commit_probability": {key: f"{value.numerator}/{value.denominator}" for key, value in results.items()},
        "false_commit_decimal": {key: float(value) for key, value in results.items()},
    }


def main():
    print(json.dumps({
        "experiment": "issue-5446-anytime-validity-t5",
        "null": "time-independent shared/private Bernoulli(1/2), exact rational enumeration",
        "horizon": HORIZON,
        "branches": BRANCHES,
        "threshold": str(THRESHOLD),
        "rho_values": [summarize(rho) for rho in RHO_VALUES],
        "scope": "synthetic null only; no real verifier or semantic action claim",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
