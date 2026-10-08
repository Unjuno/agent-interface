import hashlib, json, pathlib, subprocess
root = pathlib.Path(__file__).resolve().parent
repo = root.parents[2]
freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
process = json.loads((root / "PROCESS_RESULTS.json").read_text(encoding="utf-8"))

def git(*args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert git("rev-parse", "HEAD") == freeze["main_sha"]
assert git("rev-parse", "origin/main") == freeze["main_sha"]
assert git("rev-parse", f"{freeze['main_sha']}:{freeze['controller_path']}") == freeze["controller_blob"]
assert git("rev-parse", f"{freeze['main_sha']}:{freeze['cleanup_path']}") == freeze["cleanup_blob"]
assert sha(root / "baseline_map01_overlap_controller_v39.py") == freeze["controller_sha256"]
assert sha(root / "baseline_doom_controller_failure_cleanup_v1.py") == freeze["cleanup_sha256"]
assert sha(root / "test_current_main_boundary.py") == freeze["harness_sha256"]

for mode in ("normal", "optimized"):
    assert process[mode]["exit_code"] == process[mode]["expected_exit_code"] == 0
    stderr = (root / f"test_{mode}.stderr.txt").read_text(encoding="utf-8")
    assert "Ran 1 test" in stderr and "OK" in stderr
    observed = json.loads((root / f"observed_{mode}.json").read_text(encoding="utf-8"))
    assert observed["mode"] == mode
    assert observed["initial_expected_sequence"] == 7
    assert observed["new_observation_sequence"] == 8
    assert observed["submitted_renewal_id"] == "cover-0-renew-1"
    assert observed["submission_response"] == {
        "event": "rejected", "id": "cover-0-renew-1",
        "reason": "latest observation sequence required before input"}
    assert observed["raised_exception"]["type"] == "RuntimeError"
    assert observed["monitor_observed_rows_during_submit"] == 0
    assert observed["planner_interrupt_count"] == 0
    timeline = observed["timeline"]
    assert timeline.index("stale_sequence_rejection_consumed") < timeline.index("planner_await_returned")
    assert timeline.index("planner_await_returned") < timeline.index("planner_closed")
    cleanup = observed["failure_cleanup"]
    assert cleanup["primary_error_type"] == "RuntimeError"
    assert cleanup["failed_stage"] == "planner_turn"
    assert cleanup["input_terminals_complete"] is True
    assert cleanup["input_releases_verified_empty"] is True
    assert cleanup["input_release_verified_empty"] is True
    assert cleanup["scorer_terminal_observed"] is False
    assert cleanup["score_file_present"] is False
    assert cleanup["owner_events_closed"] is False
    assert cleanup["cleanup_complete"] is False
assert process["py_compile"]["exit_code"] == process["py_compile"]["expected_exit_code"] == 0

manifest = root / "SHA256SUMS.txt"
expected = {}
for line in manifest.read_text(encoding="utf-8").splitlines():
    digest, rel = line.split("  ", 1)
    expected[rel] = digest
excluded = {manifest, root / "AUDIT.json", root / "RESULT.json"}
actual = {path.relative_to(root).as_posix(): sha(path)
          for path in root.rglob("*")
          if path.is_file() and path not in excluded and "__pycache__" not in path.parts}
assert actual.keys() == expected.keys(), (sorted(actual.keys() - expected.keys()),
                                           sorted(expected.keys() - actual.keys()))
assert all(actual[name] == digest for name, digest in expected.items())
summary = {
    "audit": "PASS",
    "checksums": "PASS",
    "current_main": freeze["main_sha"],
    "test_modes": {"normal": "1 characterization passed", "optimized": "1 characterization passed"},
    "observed": "stale renewal rejection raises RuntimeError before explicit planner interrupt",
    "failure_cleanup": "planner closed; previous accepted cover terminal/release verified empty; session cleanup incomplete",
    "scope": "synthetic frozen-source controller construction only",
}
(root / "AUDIT.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
result = {
    "schema": "v39-renewal-stale-sequence-boundary-a01-result-v1",
    "disposition": "CURRENT_MAIN_STALE_RENEWAL_REJECTION_REPRODUCED",
    "exact_exception": "RuntimeError({'event': 'rejected', 'id': 'cover-0-renew-1', 'reason': 'latest observation sequence required before input'})",
    "fresh_sequence": 8,
    "submitted_sequence": 7,
    "prior_release": "verified empty for previously accepted cover-0",
    "pending_planner": "await returned before failure cleanup closed planner; explicit interrupt count 0",
    "new_renewal": "rejected, not added to accepted IDs, no cancel sent",
    "cleanup": "input terminals complete and previous release verified empty; scorer terminal, score file and owner close absent; cleanup_complete false",
    "current_main": freeze["main_sha"],
    "remote_ci": "not applicable; no source change",
    "live_game_model_gui_native_input_container": False,
    "remaining": "integrated correction/review and separately assigned fresh V39 threat-exposure allocation with useful-feedback, bounded-recovery, and task-effect gates",
}
(root / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
