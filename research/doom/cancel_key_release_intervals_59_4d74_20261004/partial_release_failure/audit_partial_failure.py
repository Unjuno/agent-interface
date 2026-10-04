"""Independent audit of the retained partial-release failure experiment."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
freeze = json.loads((ROOT / "FREEZE.json").read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

green = json.loads((ROOT / "green.stdout.txt").read_text())
verify = json.loads((ROOT / "verify.stdout.txt").read_text())
failed = green["before_close"]["owner_release_records"]
v13 = green["v13_unverified_publication"]
checks = {
    "baseline_source_sha256": sha(ROOT / "baseline/input_owner_v12.py") == freeze["baseline_source_sha256"],
    "candidate_source_sha256": sha(ROOT / "candidate/input_owner_v12.py") == freeze["candidate_source_sha256"],
    "candidate_test_sha256": sha(REPO / freeze["candidate_test_path"]) == freeze["candidate_test_sha256"],
    "experiment_script_sha256": sha(ROOT / "characterize_sync_failure.py") == freeze["experiment_script_sha256"],
    "audit_script_sha256": sha(ROOT / "audit_partial_failure.py") == freeze["audit_script_sha256"],
    "suite_output_sha256": sha(ROOT / "suite.stderr.txt") == freeze["suite_stderr_sha256"],
    "suite_runner_sha256": sha(ROOT / "run_ordered_suite.py") == freeze["suite_runner_sha256"],
    "red_failure_preserved": ((ROOT / "red.exit.txt").read_text().strip() == "1" and
        "failed cancellation must publish one unverified owner_release" in
        (ROOT / "red.stderr.txt").read_text() and
        str(ROOT / "baseline/input_owner_v12.py") in
        (ROOT / "red.stderr.txt").read_text() and
        sha(ROOT / "red.stderr.txt") == freeze["red_stderr_sha256"]),
    "verification_red_failure_preserved": ((ROOT / "verify-red.exit.txt").read_text().strip() == "1" and
        "failed cancellation must publish one unverified owner_release" in
        (ROOT / "verify-red.stderr.txt").read_text() and
        str(ROOT / "baseline/input_owner_v12.py") in
        (ROOT / "verify-red.stderr.txt").read_text() and
        sha(ROOT / "verify-red.stderr.txt") == freeze["verify_red_stderr_sha256"]),
    "green_result_hash": sha(ROOT / "green.stdout.txt") == freeze["green_stdout_sha256"],
    "verification_result_hash": sha(ROOT / "verify.stdout.txt") == freeze["verify_stdout_sha256"],
    "verification_exit_zero": (ROOT / "verify.exit.txt").read_text().strip() == "0",
    "green_loaded_candidate_source": str(REPO / "research/live_control/input_owner_v12.py") == green["loaded_source"],
    "green_exit_zero": (ROOT / "green.exit.txt").read_text().strip() == "0",
    "unverified_cancellation_receipt": (green["injected_request_accepted_then_raised"] is True and
        len(failed) == 1 and failed[0]["reason"] == "cancelled" and
        failed[0]["verified"] is False and
        failed[0]["keys_down"] == [65, 87] and
        failed[0]["key_release_intervals_ns"] == [] and
        len(green["before_close"]["interruptions"]) == 1),
    "v13_fails_closed": (v13["event"] == "input_release_unverified" and
        v13["owner_release"] == failed[0] and
        v13["grants_input_authority"] is False),
    "post_sync_verification_failure_preserves_bounds": (
        verify["failure_phase"] == "verify" and
        len(verify["before_close"]["owner_release_records"]) == 1 and
        verify["before_close"]["owner_release_records"][0]["verified"] is False and
        len(verify["before_close"]["owner_release_records"][0]["key_release_intervals_ns"]) == 2 and
        verify["v13_unverified_publication"]["event"] == "input_release_unverified" and
        verify["v13_unverified_publication"]["grants_input_authority"] is False),
    "later_cleanup_verified_separately": (
        len(green["after_close_owner_release_records"]) == 2 and
        green["after_close_owner_release_records"][0]["verified"] is False and
        green["after_close_owner_release_records"][1]["reason"] == "close" and
        green["after_close_owner_release_records"][1]["verified"] is True),
    "harness_stop_preserved": ((ROOT / "setup-stop.exit.txt").read_text().strip() == "1" and
        "AttributeError" in (ROOT / "setup-stop.stderr.txt").read_text() and
        "root_x" in (ROOT / "setup-stop.stderr.txt").read_text()),
    "ordered_suite_import_stop_preserved": ((ROOT / "setup-stop-suite.exit.txt").read_text().strip() == "1" and
        "ModuleNotFoundError" in (ROOT / "setup-stop-suite.stderr.txt").read_text() and
        "test_release_backend_v3_actual_composition" in
            (ROOT / "setup-stop-suite.stderr.txt").read_text()),
    "ordered_adjacent_suite_pass": ((ROOT / "suite.exit.txt").read_text().strip() == "0" and
        "Ran 20 tests" in (ROOT / "suite.stderr.txt").read_text() and
        "OK" in (ROOT / "suite.stderr.txt").read_text()),
}
result = {"schema": "partial-release-failure-audit-v1", "checks": checks,
          "pass": all(checks.values())}
print(json.dumps(result, indent=2, sort_keys=True))
if not result["pass"]:
    raise SystemExit(1)
