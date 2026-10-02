"""Construction regressions for the independent raw-only arithmetic checker."""
from __future__ import annotations
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_raw


def fixture():
    rows = [
        {
            "pair_index": pair,
            "arm": arm,
            "planner_window": {
                "start_ns": 1_000_000_000,
                "end_ns": 1_600_000_000,
                "duration_ns": 600_000_000,
                "end_boundary_phase": audit_raw.PHASE,
            },
        }
        for pair in audit_raw.PAIRS for arm in audit_raw.ARMS
    ]
    return {
        "arm_summaries": rows,
        "v6_audit_clean": {
            "decision": "PASS_MECHANISM_ONLY",
            "valid_experiment": True,
            "promotable_mechanism_result": True,
            "planner_boundary_failures": [],
        },
    }


def test_truthful_fixture_and_six_isolated_mutations():
    payload = fixture()
    result = audit_raw.inspect(payload)
    assert result["decision"] == "PASS_WINDOW_ARITHMETIC_AUDIT_SCOPED", result
    assert result["single_arm_duration_mutations_rejected"] == 6
    assert result["mutation_failures"] == []
    for index in range(6):
        mutant = copy.deepcopy(payload)
        mutant["arm_summaries"][index]["planner_window"]["duration_ns"] += 1
        errors = audit_raw.row_errors(mutant["arm_summaries"][index])
        row = mutant["arm_summaries"][index]
        assert errors == [
            f"pair{row['pair_index']}:{row['arm']}:planner_window_duration_mismatch"
        ], errors


def test_rejects_type_endpoint_and_phase_faults():
    cases = [
        ("end_ns", True, "planner_window_integer_fields"),
        ("end_ns", 999_999_999, "planner_window_nonpositive"),
        ("duration_ns", "600000000", "planner_window_integer_fields"),
        ("duration_ns", 600_000_001, "planner_window_duration_mismatch"),
        ("end_boundary_phase", "after_cleanup", "planner_end_phase"),
    ]
    for field, value, expected in cases:
        row = fixture()["arm_summaries"][0]
        row["planner_window"][field] = value
        assert any(error.endswith(expected) for error in audit_raw.row_errors(row))


def test_self_consistent_long_window_is_explicitly_outside_claim():
    result = audit_raw.inspect(fixture())
    probe = result["self_consistent_3_6s_probe"]
    assert probe["passes_narrow_arithmetic_predicate"] is True
    assert probe["arithmetic_errors"] == []
    assert probe["disposition"] == "OUTSIDE_CLAIM_NO_UPPER_DURATION_BOUND"


if __name__ == "__main__":
    tests = [test_truthful_fixture_and_six_isolated_mutations,
             test_rejects_type_endpoint_and_phase_faults,
             test_self_consistent_long_window_is_explicitly_outside_claim]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS total {len(tests)}")
