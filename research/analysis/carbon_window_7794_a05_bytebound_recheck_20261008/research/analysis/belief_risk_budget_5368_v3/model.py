"""Finite action-conditioned belief policy models; synthetic arithmetic only."""
from fractions import Fraction

RISK_BUDGET = Fraction(1, 20)
SAFE_PAYOFF = 10
UNSAFE_PAYOFF = -20

CASES = {
    "certain_safe": (Fraction(0), Fraction(0)),
    "rare_hazard": (Fraction(1, 100), Fraction(1, 100)),
    "near_budget": (Fraction(1, 25), Fraction(1, 25)),
    "dangerous_minority": (Fraction(1, 10), Fraction(1, 10)),
    "ambiguous": (Fraction(3, 10), Fraction(3, 10)),
    "mostly_unsafe": (Fraction(4, 5), Fraction(4, 5)),
    "misspecified_hazard": (Fraction(1, 25), Fraction(1, 5)),
}


def decide(policy: str, reported_unsafe: Fraction) -> bool:
    if policy == "MAP":
        return reported_unsafe < Fraction(1, 2)
    if policy == "WORST_CASE":
        return reported_unsafe == 0
    if policy == "RISK_BUDGET":
        return reported_unsafe <= RISK_BUDGET
    if policy == "EXPECTED_UTILITY":
        return (1 - reported_unsafe) * SAFE_PAYOFF + reported_unsafe * UNSAFE_PAYOFF > 0
    raise ValueError(f"unknown policy: {policy}")


def fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def evaluate(policy: str, reported: Fraction, actual: Fraction) -> dict:
    admitted = decide(policy, reported)
    expected_utility = (1 - reported) * SAFE_PAYOFF + reported * UNSAFE_PAYOFF
    actual_unsafe_mass = actual if admitted else Fraction(0)
    return {
        "policy": policy,
        "admitted": admitted,
        "reported_unsafe_mass": fraction_text(reported),
        "actual_unsafe_mass_if_admitted": fraction_text(actual_unsafe_mass),
        "model_expected_utility_if_admitted": fraction_text(expected_utility) if admitted else "0/1",
        "misspecification_exposed": actual != reported,
    }
