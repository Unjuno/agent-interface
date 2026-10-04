"""Audit the additive endpoint-type regression and retained local test logs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_PACKAGE_TESTS = (
    "test_boolean_tic_readback_fails_closed",
    "test_configured_variable_order_mismatch_fails_closed",
    "test_float_tic_readback_fails_closed",
    "test_multi_tic_ack_matches_snapshot_and_is_accepted",
    "test_no_op_update_fails_closed",
    "test_one_tic_ack_with_coherent_snapshot",
    "test_retained_async_spectator_counterexample_composes",
    "test_snapshot_mismatch_fails_closed",
    "test_tic_drift_during_read_fails_closed",
    "test_installs_snapshot_sampler_restores_and_binds_source_hashes",
    "test_restores_original_sampler_when_v15_session_raises",
    "test_boolean_snapshot_tic_fails_closed",
    "test_configured_order_is_used_to_find_kill_and_death",
    "test_duplicate_or_missing_required_counter_fails_closed",
    "test_endpoint_mismatch_never_publishes_sample",
    "test_fractional_counter_fails_closed",
    "test_retained_runtime_endpoint_composes_with_actual_v16_sampler_and_sink",
)
EXPECTED_V16_TESTS = (
    "test_cross_game_and_cross_thread_are_refused",
    "test_failed_update_is_recorded_without_retry",
    "test_multitic_update_reaches_real_sink_with_run_identity",
    "test_noop_never_returns_a_sample",
    "test_session_installs_sampler_and_restores_on_failure",
    "test_sink_exception_does_not_publish_sample_or_retry",
    "test_terminal_repeat_carries_ack_without_second_update",
)


def main():
    pins = json.loads((HERE / "FOLLOWUP_PINS.json").read_text(encoding="utf-8"))
    errors = []
    for name, expected in pins["files"].items():
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if actual != expected:
            errors.append("sha256:" + name)

    package_log = (HERE / "followup-test-output.txt").read_text(encoding="utf-8")
    v16_log = (HERE / "followup-v16-test-output.txt").read_text(encoding="utf-8")
    missing_package = [name for name in EXPECTED_PACKAGE_TESTS if name not in package_log]
    missing_v16 = [name for name in EXPECTED_V16_TESTS if name not in v16_log]
    if missing_package:
        errors.append("missing_package_tests:" + ",".join(missing_package))
    if missing_v16:
        errors.append("missing_v16_tests:" + ",".join(missing_v16))
    if "Ran 17 tests" not in package_log or not package_log.rstrip().endswith("OK"):
        errors.append("package_suite_not_green")
    if "Ran 7 tests" not in v16_log or not v16_log.rstrip().endswith("OK"):
        errors.append("v16_suite_not_green")

    report = {
        "schema": "scorer-endpoint-readback-type-followup-audit-v1",
        "pass": not errors,
        "errors": errors,
        "base_commit": pins["base_commit"],
        "package_test_count": len(EXPECTED_PACKAGE_TESTS) - len(missing_package),
        "v16_test_count": len(EXPECTED_V16_TESTS) - len(missing_v16),
        "scope": "candidate-only fake-game regression; no ViZDoom engine, live session, GUI, or input",
    }
    (HERE / "FOLLOWUP_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
