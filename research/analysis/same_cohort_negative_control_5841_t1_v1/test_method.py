import json
from pathlib import Path

from candidate import evaluate


def test_path_specific_faults_show_incremental_and_escaped_detection():
    fixture = json.loads((Path(__file__).parent / "fixture.json").read_text())
    result = evaluate(fixture)

    by_case = {row["case_id"]: row for row in result["cases"]}
    assert by_case["clean_null"]["disposition"] == "NO_SIGNAL"
    assert by_case["clean_null"]["all_attempt"] == "PASS_COMPLETE"
    assert by_case["clean_null"]["negative_control_shift"] is False
    assert by_case["true_primary_benefit"]["disposition"] == "NO_SIGNAL"
    assert by_case["true_primary_benefit"]["observed_primary_rates"] == {"A": 0.5, "B": 1.0}
    assert by_case["shared_export_fault"]["disposition"] == "SHARED_PATH_HOLD"
    assert by_case["shared_export_fault"]["all_attempt"] == "PASS_COMPLETE"
    assert by_case["shared_export_fault"]["observed_sentinel_rates"] == {"A": 0.0, "B": 0.25}
    assert by_case["primary_only_fault"]["disposition"] == "OUT_OF_SCOPE_UNDETECTED"
    assert by_case["primary_only_fault"]["all_attempt"] == "PASS_COMPLETE"
    assert by_case["primary_only_fault"]["observed_sentinel_rates"] == {"A": 0.0, "B": 0.0}
    assert by_case["missing_terminal"]["all_attempt"] == "HOLD_MISSING"
    assert by_case["foreign_join"]["all_attempt"] == "HOLD_IDENTITY"
    assert by_case["true_collateral"]["disposition"] == "COLLATERAL_FAIL"
    assert by_case["true_collateral"]["negative_control_shift"] is True
    assert result["incremental_shared_faults_detected"] == 1
    assert result["primary_only_false_all_clear"] == 1
