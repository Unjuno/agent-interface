"""Independent consistency audit for the retained construction outputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text())
checks = {}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

candidate_root = ROOT.parents[2]
checks["initial_candidate_source_sha256"] = (
    sha(ROOT / "partial_release_failure" / "baseline" / "input_owner_v12.py")
    == freeze["candidate_source_sha256"]
)
checks["initial_candidate_test_sha256"] = (
    sha(ROOT / "module_cache_isolation" / "pre-review-test.py")
    == freeze["candidate_test_sha256"]
)
checks["baseline_source_sha256"] = (
    sha(ROOT / "baseline" / "input_owner_v12.py")
    == freeze["baseline_source_sha256"]
)
stop = (ROOT / "baseline" / "out-01.stderr.txt").read_text()
checks["initial_staging_stop"] = (
    (ROOT / "baseline" / "out-01.exit.txt").read_text().strip() == "1"
    and "ModuleNotFoundError: No module named 'lease'" in stop
)
baseline = (ROOT / "baseline" / "out-02.stderr.txt").read_text()
checks["baseline_missing_interval_failure"] = (
    (ROOT / "baseline" / "out-02.exit.txt").read_text().strip() == "1"
    and "KeyError: 'key_release_intervals_ns'" in baseline
)
candidate_err = (ROOT / "candidate.stderr.txt").read_text()
checks["candidate_16_tests_pass"] = (
    (ROOT / "candidate.exit.txt").read_text().strip() == "0"
    and "Ran 16 tests" in candidate_err
    and "OK" in candidate_err
)
followup = json.loads((ROOT / "module_cache_isolation" / "FREEZE.json").read_text())
checks["followup_candidate_test_sha256"] = (
    sha(candidate_root / followup["candidate_test_path"])
    == followup["candidate_test_sha256"]
)
checks["followup_adjacent_test_sha256"] = (
    sha(candidate_root / followup["adjacent_test_path"])
    == followup["adjacent_test_sha256"]
)
checks["followup_runner_sha256"] = (
    sha(ROOT / "module_cache_isolation" / "run_test_order_followup.py")
    == followup["runner_sha256"]
)
isolation_red = (ROOT / "module_cache_isolation" / "pre_fix.stderr.txt").read_text()
checks["module_cache_bug_reproduced"] = (
    (ROOT / "module_cache_isolation" / "pre_fix.exit.txt").read_text().strip() == "1"
    and "pre-existing input_owner_v12 cache entry was discarded" in isolation_red
)
isolation_dir = ROOT / "module_cache_isolation"
checks["ordered_runner_import_stop_preserved"] = (
    (isolation_dir / "setup-stop-ordered.exit.txt").read_text().strip() == "1"
    and "ModuleNotFoundError: No module named 'research'" in
        (isolation_dir / "setup-stop-ordered.stderr.txt").read_text()
)
ordered_err = (ROOT / "module_cache_isolation" / "ordered.stderr.txt").read_text()
checks["ordered_18_test_suite_pass"] = (
    (ROOT / "module_cache_isolation" / "ordered.exit.txt").read_text().strip() == "0"
    and "Ran 18 tests" in ordered_err
    and "OK" in ordered_err
)
checks["ordered_runner_matches_freeze"] = (
    sha(isolation_dir / "run_test_order_followup.py") == followup["runner_sha256"]
)
checks["adjacent_test_matches_freeze"] = (
    sha(candidate_root / followup["adjacent_test_path"])
    == followup["adjacent_test_sha256"]
)
partial_root = ROOT / "partial_release_failure"
partial_freeze = json.loads((partial_root / "FREEZE.json").read_text())
partial_result_path = partial_root / "audit.json"
partial_result = json.loads(partial_result_path.read_text())
checks["partial_failure_candidate_source_sha256"] = (
    sha(partial_root / "candidate" / "input_owner_v12.py")
    == partial_freeze["candidate_source_sha256"]
)
checks["partial_failure_candidate_test_sha256"] = (
    sha(candidate_root / partial_freeze["candidate_test_path"])
    == partial_freeze["candidate_test_sha256"]
)
checks["partial_failure_experiment_script_sha256"] = (
    sha(partial_root / "characterize_sync_failure.py")
    == partial_freeze["experiment_script_sha256"]
)
checks["partial_failure_audit_script_sha256"] = (
    sha(partial_root / "audit_partial_failure.py")
    == partial_freeze["audit_script_sha256"]
)
checks["partial_failure_suite_sha256"] = (
    sha(partial_root / "suite.stderr.txt")
    == partial_freeze["suite_stderr_sha256"]
)
checks["partial_failure_audit_result"] = (
    partial_result.get("pass") is True
    and sha(partial_result_path) == partial_freeze["audit_result_sha256"]
)
keymap_root = ROOT / "keymap_epoch_stability"
keymap_freeze = json.loads((keymap_root / "FREEZE.json").read_text())
keymap_audit_path = keymap_root / "AUDIT.json"
keymap_audit = json.loads(keymap_audit_path.read_text())
checks["keymap_epoch_probe_sha256"] = (
    sha(keymap_root / "probe.py") == keymap_freeze["probe_sha256"]
)
checks["keymap_epoch_audit_result"] = (
    keymap_audit.get("pass") is True
    and sha(keymap_audit_path) == keymap_freeze["audit_result_sha256"]
)
explicit_root = ROOT / "explicit_keyup_remap"
explicit_freeze = json.loads((explicit_root / "FREEZE.json").read_text())
explicit_audit_path = explicit_root / "AUDIT.json"
explicit_audit = json.loads(explicit_audit_path.read_text())
checks["explicit_keyup_remap_audit_result"] = (
    explicit_audit.get("pass") is True
    and sha(explicit_audit_path) == explicit_freeze["audit_result_sha256"]
)
explicit_audit_v2_path = explicit_root / "AUDIT_v2.json"
explicit_audit_v2 = json.loads(explicit_audit_v2_path.read_text())
checks["explicit_keyup_remap_archived_source_reaudit"] = (
    explicit_audit_v2.get("pass") is True
    and sha(explicit_root / "candidate" / "input_owner_v12.py")
        == explicit_freeze["candidate_source_sha256"]
)
alias_root = ROOT / "unmatched_keyup_alias"
alias_freeze = json.loads((alias_root / "FREEZE.json").read_text())
alias_audit_path = alias_root / "AUDIT.json"
alias_audit = json.loads(alias_audit_path.read_text())
checks["unmatched_keyup_alias_candidate_source_sha256"] = (
    sha(alias_root / "candidate" / "input_owner_v12.py")
    == alias_freeze["candidate_source_sha256"]
)
checks["unmatched_keyup_alias_audit_result"] = (
    alias_audit.get("pass") is True
    and sha(alias_audit_path) == alias_freeze["audit_result_sha256"]
)
alias_audit_v2 = json.loads((alias_root / "AUDIT_v2.json").read_text())
checks["unmatched_keyup_alias_archived_source_reaudit"] = (
    alias_audit_v2.get("pass") is True
)
eviction_root = ROOT / "keymap_eviction"
eviction_freeze = json.loads((eviction_root / "FREEZE.json").read_text())
eviction_audit_path = eviction_root / "AUDIT.json"
eviction_audit = json.loads(eviction_audit_path.read_text())
checks["keyup_after_keysym_removal_candidate_source_sha256"] = (
    sha(candidate_root / eviction_freeze["source_path"])
    == eviction_freeze["candidate_source_sha256"]
)
checks["keyup_after_keysym_removal_audit_result"] = (
    eviction_audit.get("pass") is True
    and sha(eviction_audit_path) == eviction_freeze["audit_result_sha256"]
)
manifest = (ROOT / "FILES.sha256").read_text().splitlines()
manifest_results = []
for line in manifest:
    expected, rel = line.split("  ", 1)
    manifest_results.append(sha(ROOT / rel) == expected)
checks["manifest_members"] = bool(manifest_results) and all(manifest_results)
checks["manifest_member_count"] = len(manifest_results)
result = {"schema": "cancel-key-release-intervals-audit-v1", "checks": checks,
          "pass": all(value for key, value in checks.items()
                       if key != "manifest_member_count")}
print(json.dumps(result, indent=2))
if not result["pass"]:
    raise SystemExit(1)
