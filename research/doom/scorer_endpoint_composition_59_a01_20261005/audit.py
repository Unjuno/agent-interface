"""Independent audit of the retained endpoint-composition construction run."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_TESTS = (
    "test_boolean_snapshot_tic_fails_closed",
    "test_configured_variable_order_mismatch_fails_closed",
    "test_configured_order_is_used_to_find_kill_and_death",
    "test_duplicate_or_missing_required_counter_fails_closed",
    "test_endpoint_mismatch_never_publishes_sample",
    "test_fractional_counter_fails_closed",
    "test_multi_tic_ack_matches_snapshot_and_is_accepted",
    "test_no_op_update_fails_closed",
    "test_one_tic_ack_with_coherent_snapshot",
    "test_retained_async_spectator_counterexample_composes",
    "test_retained_runtime_endpoint_composes_with_actual_v16_sampler_and_sink",
    "test_installs_snapshot_sampler_restores_and_binds_source_hashes",
    "test_restores_original_sampler_when_v15_session_raises",
    "test_snapshot_mismatch_fails_closed",
    "test_tic_drift_during_read_fails_closed",
)


def audit():
    errors = []
    pins = json.loads((ROOT / "SOURCE_PINS.json").read_text(encoding="utf-8"))
    for item in pins.get("sources", []):
        path = REPO / item["path"]
        if not path.is_file():
            errors.append("missing_source:" + item["path"])
        elif hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            errors.append("source_hash:" + item["path"])

    raw_path = REPO / "research/doom/scorer_async_spectator_59_t0_a01_20261004/raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    update = raw.get("update", {})
    sample = raw.get("after_acknowledged_update", {})
    if (raw.get("status") != "PASS_COUNTEREXAMPLE_EXACT_ONE_TIC_GUARD" or
            update.get("episode_before") != 1 or update.get("episode_after") != 11 or
            sample.get("state_tic") != 11 or sample.get("state_variables") != [0.0, 0.0]):
        errors.append("retained_runtime_witness")

    output = (ROOT / "test-output.txt").read_text(encoding="utf-8")
    missing = [name for name in EXPECTED_TESTS if name not in output]
    if missing:
        errors.append("missing_test_case:" + ",".join(missing))
    expected_run_count = len(EXPECTED_TESTS)
    if f"Ran {expected_run_count} tests" not in output or not output.rstrip().endswith("OK"):
        errors.append("test_run_not_green")
    result = {
        "schema": "scorer-endpoint-composition-audit-v1",
        "pass": not errors,
        "errors": errors,
        "test_count": len(EXPECTED_TESTS) - len(missing),
        "retained_endpoint": [update.get("episode_before"), update.get("episode_after"), sample.get("state_tic")],
        "scope": "source-pin, retained-witness, and test-log audit; not an independent live-engine or runtime-controller audit",
    }
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
