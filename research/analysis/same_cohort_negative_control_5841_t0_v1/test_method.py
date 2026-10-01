import json
from pathlib import Path

import pytest

from candidate import analyze
from audit import audit_result


HERE = Path(__file__).parent
FIXTURE = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((HERE / "EXPECTED.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def result():
    return analyze(FIXTURE)


@pytest.mark.parametrize(
    ("case", "delta", "deck", "disposition"),
    [
        ("clean_null", 0.0, "PASS", "NO_CONTROL_SIGNAL"),
        ("primary_benefit", 0.5, "PASS", "NO_CONTROL_SIGNAL"),
        ("route_missingness", 0.75, "PASS", "ASCERTAINMENT_HOLD"),
        ("foreign_join", 0.75, "PASS", "JOIN_INTEGRITY_HOLD"),
        ("export_drift", 0.5, "HOLD", "ORACLE_DRIFT_HOLD"),
        ("real_collateral", 0.5, "PASS", "COLLATERAL_FAIL"),
    ],
)
def test_each_frozen_case_has_its_hand_derived_disposition(result, case, delta, deck, disposition):
    row = next(item for item in result["cases"] if item["id"] == case)
    assert row["primary_only_guarded_minus_direct"] == pytest.approx(delta)
    assert row["reference_deck"] == deck
    assert row["disposition"] == disposition


def test_all_assigned_control_rows_are_retained(result):
    assert all(len(row["ledger"]) == 8 for row in result["cases"])


def test_independent_auditor_rejects_hidden_control_row(result):
    changed = json.loads(json.dumps(result))
    changed["cases"][2]["ledger"].pop()
    audit = audit_result(changed, FIXTURE, EXPECTED)
    assert "CONTROL_DENOMINATOR_MISMATCH:route_missingness" in audit["errors"]


def test_independent_auditor_rejects_swapped_seal(result):
    changed = json.loads(json.dumps(result))
    changed["cases"][3]["ledger"][0]["assigned_seal"] = "wrong-seal"
    audit = audit_result(changed, FIXTURE, EXPECTED)
    assert "ASSIGNMENT_SEAL_MISMATCH:foreign_join:direct:e1" in audit["errors"]


def test_equal_missing_counts_on_different_episodes_are_still_asymmetric():
    changed_fixture = json.loads(json.dumps(FIXTURE))
    case = next(row for row in changed_fixture["scenarios"] if row["id"] == "route_missingness")
    case["missing"] = [
        {"route": "direct", "episode": "e2"},
        {"route": "guarded", "episode": "e3"},
    ]
    row = next(item for item in analyze(changed_fixture)["cases"] if item["id"] == "route_missingness")
    assert row["control_flags"]["route_specific_missingness"] is True
    assert row["disposition"] == "ASCERTAINMENT_HOLD"


def test_shared_missing_hard_outcome_still_holds_the_cohort():
    changed_fixture = json.loads(json.dumps(FIXTURE))
    case = next(row for row in changed_fixture["scenarios"] if row["id"] == "route_missingness")
    case["missing"] = [
        {"route": "direct", "episode": "e2"},
        {"route": "guarded", "episode": "e2"},
    ]
    row = next(item for item in analyze(changed_fixture)["cases"] if item["id"] == "route_missingness")
    assert row["control_flags"]["any_primary_outcome_missing"] is True
    assert row["control_flags"]["route_specific_missingness"] is False
    assert row["disposition"] == "ASCERTAINMENT_HOLD"
