from fractions import Fraction

import audit
import oracle
from model import CASES, decide, evaluate
from runner import build_raw


def test_risk_budget_exact_threshold():
    assert decide("RISK_BUDGET", Fraction(1, 25))
    assert not decide("RISK_BUDGET", Fraction(1, 10))


def test_worst_case_and_budget_trade_availability():
    ps = [p for p, _ in CASES.values()]
    assert sum(decide("RISK_BUDGET", p) for p in ps) > sum(decide("WORST_CASE", p) for p in ps)
    assert all(not decide("RISK_BUDGET", p) or p <= Fraction(1, 20) for p in ps)


def test_expected_utility_threshold_is_independent_of_risk_budget():
    assert decide("EXPECTED_UTILITY", Fraction(3, 10))
    assert not decide("EXPECTED_UTILITY", Fraction(4, 5))
    assert not decide("RISK_BUDGET", Fraction(3, 10))


def test_misspecification_is_not_certified():
    row = evaluate("RISK_BUDGET", *CASES["misspecified_hazard"])
    assert row["admitted"] and row["misspecification_exposed"]
    assert Fraction(row["actual_unsafe_mass_if_admitted"]) == Fraction(1, 5)


def test_oracle_and_audit_match_full_replay():
    raw = build_raw()
    assert len(raw["rows"]) == 28
    assert audit.audit(raw) == []
    assert all(r["admitted"] == oracle.oracle_decision(r["policy"], Fraction(r["reported"])) for r in raw["rows"])


def test_no_authority_or_effect():
    assert all(not r["authority"] and not r["effect"] for r in build_raw()["rows"])
