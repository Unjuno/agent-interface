import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = HERE / "map01_recovery_cover_mechanism_v3_prereg.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_identity_and_scope():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    assert plan["allocation_id"] == "map01-recovery-cover-mechanism-live-v3-01"
    assert plan["fixed_condition"]["model_calls"] == 0
    assert "not frontier-model efficacy" in plan["claim_scope"]
    assert plan["stop_rule"].endswith("no retry under this allocation ID")


def test_mechanism_thresholds_frozen():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    acceptance = plan["acceptance"]
    assert acceptance["pair_count"] == 3
    assert acceptance["all_three_pairs_continuity_improved"] is True
    assert acceptance["paired_median_no_input_upper_reduction_fraction_min"] == 0.10
    assert acceptance["recovery_negative_event_count"] == 0


def test_new_source_hashes():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    pins = plan["source_pins"]
    assert sha256(HERE / "map01_recovery_cover_mechanism_v3_runner.py") == pins["research/doom/map01_recovery_cover_mechanism_v3_runner.py_sha256"]
    assert sha256(HERE / "audit_map01_recovery_cover_mechanism_v3.py") == pins["research/doom/audit_map01_recovery_cover_mechanism_v3.py_sha256"]


def test_required_dependencies_are_current_evidence():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    deps = plan["dependencies"]
    assert deps["protocol_valid_measurement_live04_commit"].startswith("1cceae7c")
    assert deps["real_map01_recovery_dev02_result_commit"].startswith("9e6d5ecd")
    assert deps["workflow_path_global_owner_commit"].startswith("fdfdd282")


if __name__ == "__main__":
    tests = [
        test_identity_and_scope,
        test_mechanism_thresholds_frozen,
        test_new_source_hashes,
        test_required_dependencies_are_current_evidence,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} mechanism-v3 preregistration tests")
