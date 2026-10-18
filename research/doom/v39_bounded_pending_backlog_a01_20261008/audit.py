from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FREEZE = "6ea1269defb6d48a607f13b08f1aa2d223ba06e9"
EXPECTED_BASE_BLOBS = {
    "research/doom/map01_overlap_controller_v39.py":
        "f7b66279d87ebc3704ccef1b6a5ce646611c890b",
    "research/live_control/executor_v12.py":
        "7e9bb6286d5f674108688ba092300a8ad2421ba9",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    require(git("cat-file", "-t", FREEZE) == "commit", "frozen commit is unavailable")
    actual_base_blobs = {
        path: git("rev-parse", f"{FREEZE}:{path}")
        for path in EXPECTED_BASE_BLOBS
    }
    require(actual_base_blobs == EXPECTED_BASE_BLOBS, "frozen baseline source blobs changed")

    result = json.loads((HERE / "baseline_result.json").read_text(encoding="utf-8"))
    require(result["main_commit"] == FREEZE, "baseline result commit mismatch")
    require(result["status"] == (
        "REPRODUCED_STALE_ANSWER_REACHES_EXECUTOR_REJECTION_WITHOUT_REPLAN"),
        "baseline result status mismatch")
    require(result["drain"]["latest_sequence_used"] == 11, "baseline latest sequence mismatch")
    require(result["drain"]["hard_crossing_sequence_left_queued"] == 12,
            "baseline queued crossing sequence mismatch")
    require(result["executor"]["outcome"] == "rejected", "baseline stale action was not rejected")
    require(result["executor"]["reason"] == (
        "latest observation sequence required before input"), "baseline rejection reason mismatch")

    controller_path = ROOT / "research/doom/map01_overlap_controller_v39.py"
    controller = controller_path.read_text(encoding="utf-8")
    ast.parse(controller)
    require("MAX_PENDING_OBSERVATION_EVENTS = 256" in controller, "event bound missing")
    require("MAX_PENDING_OBSERVATION_RECOVERY_BATCHES = 4" in controller,
            "recovery batch bound missing")
    require('elif drained["pending_events"]:' in controller, "pending-event branch missing")
    require("recovery = recover_pending_observation_backlog(" in controller,
            "bounded recovery call missing")
    require('"pending_observation_recovery":recovery' in controller,
            "recovery receipt wiring missing")

    test_path = ROOT / "research/doom/test_map01_v39_pending_observation_drain.py"
    test_source = test_path.read_text(encoding="utf-8")
    ast.parse(test_source)
    required_cases = (
        "test_boundary_hard_crossing_is_processed_before_answer_reuse",
        "test_drain_stops_at_fixed_budget_and_reports_remaining_backlog",
        "test_continuous_backlog_recovery_exhausts_a_finite_budget",
        "test_stale_executor_rejection_recovers_then_admits_fresh_sequence",
    )
    require(all(case in test_source for case in required_cases),
            "one or more bounded-recovery regression cases are missing")

    manifest = json.loads((HERE / "sha256.json").read_text(encoding="utf-8"))
    for relative_path, expected in manifest.items():
        path = ROOT / relative_path
        require(sha256(path) == expected, f"manifest hash mismatch: {relative_path}")

    # The merged A01 tree omitted the original 48-test log even though its
    # expected digest was listed in sha256.json. Keep that historical custody
    # gap explicit; never substitute the current-main run for that old result.
    gap = json.loads((HERE / "historical_artifact_gap.json").read_text(encoding="utf-8"))
    require(gap["artifact"] == "unittest.log", "historical gap names wrong artifact")
    require(gap["expected_sha256"] == (
        "d51642c47c687fac66271eb9d83107e3a8d8540587b8dc0628109a74edd7b499"
    ), "historical missing-log digest changed")
    require(not (HERE / "unittest.log").exists(),
            "historical log appeared; disposition must be re-evaluated")

    revalidation = json.loads(
        (HERE / "current_main_revalidation.json").read_text(encoding="utf-8"))
    commit = revalidation["main_commit"]
    require(git("cat-file", "-t", commit) == "commit", "current-main revalidation commit missing")
    for path, pins in revalidation["source_files"].items():
        actual_blob = git("rev-parse", f"{commit}:{path}")
        require(actual_blob == pins["git_blob"], f"current-main Git blob mismatch: {path}")
        actual_bytes = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{commit}:{path}"])
        require(hashlib.sha256(actual_bytes).hexdigest() == pins["sha256"],
                f"current-main source hash mismatch: {path}")

    current_log_path = HERE / revalidation["log_path"]
    current_log = current_log_path.read_text(encoding="utf-8")
    match = re.search(r"Ran (\d+) tests in ([0-9.]+)s", current_log)
    require(match is not None and match.group(1) == "12" and current_log.rstrip().endswith("OK"),
            "current-main regression log is not a complete 12-test pass")
    require(sha256(current_log_path) == revalidation["log_sha256"],
            "current-main regression log hash mismatch")

    replay_path = HERE / revalidation["package_overlay_replay_log_path"]
    replay_log = replay_path.read_text(encoding="utf-8")
    replay_match = re.search(r"Ran (\d+) tests in ([0-9.]+)s", replay_log)
    require(replay_match is not None and replay_match.group(1) == "12" and
            replay_log.rstrip().endswith("OK"),
            "packaged overlay replay log is not a complete 12-test pass")
    require(sha256(replay_path) == revalidation["package_overlay_replay_log_sha256"],
            "packaged overlay replay log hash mismatch")

    # The overlay contains only files absent from the worker's sparse checkout;
    # each is pinned to the exact current-main Git blob and byte hash.
    overlay_lines = (HERE / "current_main_import_sources.sha256").read_text(
        encoding="utf-8").splitlines()
    require(len(overlay_lines) == 12, "current-main import overlay source count mismatch")
    for line in overlay_lines:
        expected_sha, relative_path = line.split("  ", 1)
        source = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative_path}"])
        require(hashlib.sha256(source).hexdigest() == expected_sha,
                f"current-main overlay source hash mismatch: {relative_path}")
        overlay_file = HERE / "current_main_import_overlay" / Path(relative_path).name
        require(sha256(overlay_file) == expected_sha,
                f"packaged overlay hash mismatch: {relative_path}")

    print(json.dumps({
        "status": "AUDIT_HOLD_HISTORICAL_LOG_MISSING_CURRENT_MAIN_REGRESSION_PASS",
        "freeze": FREEZE,
        "base_blobs": actual_base_blobs,
        "historical_test_log": "MISSING; expected 48-test raw is not reconstructed",
        "current_main_tests": int(match.group(1)),
        "elapsed_seconds": float(match.group(2)),
        "packaged_overlay_replay_tests": int(replay_match.group(1)),
        "checked_hashes": len(manifest) + len(overlay_lines) + len(revalidation["source_files"]),
        "scope": "provenance, pinned baseline outcome, bounded-recovery wiring, and current-main deterministic regression; original 48-test raw is missing and no live runtime audit was performed",
    }, indent=2))


if __name__ == "__main__":
    main()
