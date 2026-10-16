"""Saved-result audit for the A03 synthetic Executor admission composition."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
A02 = json.loads((HERE / "A02_RESULT.json").read_text(encoding="utf-8"))
checks = {}

for path, wanted in FREEZE["sources"].items():
    if isinstance(wanted, dict):
        actual = hashlib.sha256((HERE / wanted["path"]).read_bytes()).hexdigest()
        checks["prior_a02_result_hash"] = actual == wanted["sha256"]
    else:
        actual = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", f"HEAD:{path}"], text=True).strip()
        checks[f"current_source_{Path(path).name}"] = actual == wanted

checks["prior_a02_is_candidate_pair_result"] = (
    A02.get("disposition") == "PASS_CANDIDATE_COMPOSITION" and
    A02.get("trigger", {}).get("typed_and_full_sequence") == 2 and
    A02.get("trigger", {}).get("typed_and_full_frame_hash_match") is True)
checks["experiment_disposition_scoped"] = (
    RESULT.get("disposition") == "PASS_SYNTHETIC_FRESH_ANSWER_ADMISSION_BOUNDARY" and
    "synthetic" in RESULT.get("scope", "").lower() and
    "game" not in RESULT.get("scope", "").lower())
checks["physical_input_not_claimed"] = RESULT["fresh_sequence_2"].get("physical_input") is False
stale = RESULT["stale_sequence_1"]
fresh = RESULT["fresh_sequence_2"]
drift = RESULT["second_drift_sequence_3"]
checks["stale_seq1_rejected_before_validation_or_acceptance"] = (
    stale["reason"] == "latest observation sequence required before input" and
    stale["submit_attempts"] == 1 and stale["accepted_events"] == 0 and
    stale["backend_validation_calls"] == 0 and stale["worker_starts"] == 0)
checks["old_action_not_retried"] = stale["old_plan_retried_after_rejection"] is False
expected_fresh = [{"op": "hold", "keys": ["Down", "space"], "duration_ms": 300}]
checks["exact_controller_compiler_fresh_program"] = fresh["compiled_steps"] == expected_fresh
checks["fresh_turn_uses_bound_frame_and_hud"] = (
    fresh["turn_count"] == 2 and fresh["health"] == 86 and fresh["ammo"] == 12 and
    len(fresh["image_rgb_sha256"]) == 64)
accepted = fresh["accepted_events"]
checks["fresh_seq2_admitted_once"] = (
    len(accepted) == 1 and accepted[0].get("event") == "accepted" and
    accepted[0].get("id") == "fresh-seq-2" and
    fresh["backend_validation_calls"] == 1 and
    fresh["worker_started_inertly"] is True)
encoded = json.dumps(expected_fresh, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
checks["accepted_program_hash_matches_exact_compilation"] = (
    accepted[0].get("program_sha256") == hashlib.sha256(encoded).hexdigest())
checks["second_drift_refused_before_acceptance_or_worker"] = (
    drift["expected_sequence"] == 2 and drift["backend_sequence"] == 3 and
    drift["reason"] == "latest observation sequence required before input" and
    drift["accepted_events"] == 0 and drift["backend_validation_calls"] == 0 and
    drift["worker_starts"] == 0)
checks["normal_optimized_results_match"] = (
    (HERE / "normal.RESULT.json").read_bytes() == (HERE / "RESULT.json").read_bytes())
checks["normal_optimized_stdout_match"] = (
    (HERE / "normal.stdout.txt").read_bytes() == (HERE / "optimized.stdout.txt").read_bytes())
checks["both_runner_exits_zero"] = all(
    (HERE / name).read_text(encoding="ascii").strip() == "0"
    for name in ("normal.exit.txt", "optimized.exit.txt"))

manifest = {}
for line in (HERE / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
    digest, name = line.split("  ", 1)
    manifest[name] = digest
files = {path.name for path in HERE.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"}
checks["checksum_inventory_complete"] = set(manifest) == files
checks["package_hashes_match"] = checks["checksum_inventory_complete"] and all(
    hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
    for name, digest in manifest.items())
summary = {"status": "PASS_AUDIT" if all(checks.values()) else "FAIL_AUDIT",
           "checks": checks, "all_checks_pass": all(checks.values()),
           "scope": RESULT["scope"]}
(HERE / "AUDIT.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
