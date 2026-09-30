"""Independent exact-rational decision and branch-enumeration oracle."""
from fractions import Fraction


def oracle_decision(policy: str, p: Fraction) -> bool:
    if policy == "MAP":
        return 2 * p < 1
    if policy == "WORST_CASE":
        return p == 0
    if policy == "RISK_BUDGET":
        return 20 * p <= 1
    if policy == "EXPECTED_UTILITY":
        return 10 - 30 * p > 0
    raise AssertionError(policy)


def branch_masses(p: Fraction) -> dict[str, str]:
    safe = 1 - p
    return {
        "safe": f"{safe.numerator}/{safe.denominator}",
        "unsafe": f"{p.numerator}/{p.denominator}",
    }


def expected_utility(p: Fraction) -> Fraction:
    return 10 * (1 - p) - 20 * p
