"""Independent audit of the retained current-head startup-selection outputs."""
from __future__ import annotations
import base64
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "bundled-run"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    checks: dict[str, bool] = {}
    files = manifest["files"]
    checks["source_count_56"] = len(files) == freeze["source_count"] == 56
    checks["source_commit_matches_freeze"] = manifest.get("source_commit") == freeze["candidate_head"]
    source_failures = []
    git_failures = []
    for rel, pin in files.items():
        path = ROOT / "source-snapshots" / pin.get("snapshot_path", rel + ".txt")
        if not path.is_file():
            source_failures.append(rel)
            continue
        encoded = path.read_bytes()
        data = base64.b64decode(encoded) if pin.get("snapshot_encoding") == "base64" else encoded
        if len(data) != pin["bytes"] or sha(data) != pin["sha256"]:
            source_failures.append(rel)
        try:
            candidate = subprocess.check_output(
                ["git", "show", f"{freeze['candidate_head']}:{rel}"],
                cwd=ROOT, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            git_failures.append(rel)
            continue
        if candidate != data:
            git_failures.append(rel)
    checks["all_source_snapshot_hashes"] = not source_failures
    checks["all_source_bytes_match_candidate_commit"] = not git_failures
    checks["no_manifest_fallbacks"] = json.loads((ROOT / "manifest-fallbacks.json").read_text()).get("fallback_to_previous_snapshot") == []
    current_recheck = json.loads((ROOT / "CURRENT_MAIN_RECHECK.json").read_text())
    current_base = current_recheck["main_base_for_candidate"]
    current_main = current_recheck["current_main_commit"]
    changed_current_closure = []
    shared_current_paths = []
    missing_current_paths = []
    for rel in files:
        try:
            base_bytes = subprocess.check_output(["git", "show", f"{current_base}:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            try:
                subprocess.check_output(["git", "show", f"{freeze['candidate_head']}:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL)
                missing_current_paths.append(rel)
            except subprocess.CalledProcessError:
                changed_current_closure.append(rel)
            continue
        try:
            main_bytes = subprocess.check_output(["git", "show", f"{current_main}:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing_current_paths.append(rel)
            continue
        shared_current_paths.append(rel)
        if base_bytes != main_bytes:
            changed_current_closure.append(rel)
    checks["current_main_shared_closure_unchanged"] = (
        current_recheck.get("result") == "PASS_SHARED_CLOSURE_UNCHANGED" and
        len(shared_current_paths) == 55 and not changed_current_closure)
    checks["only_candidate_helper_missing_from_current_main"] = (
        missing_current_paths == ["research/doom/v39_measurement_backend_selection_v1.py"] and
        current_recheck.get("candidate_only_paths") == missing_current_paths)

    latest_candidate = json.loads((ROOT / "LATEST_CANDIDATE_RECHECK.json").read_text())
    latest_head = latest_candidate.get("latest_candidate_head", "")
    latest_candidate_changed = []
    latest_candidate_missing = []
    for rel in files:
        try:
            frozen_bytes = subprocess.check_output(
                ["git", "show", f"{freeze['candidate_head']}:{rel}"], cwd=ROOT,
                stderr=subprocess.DEVNULL)
            latest_bytes = subprocess.check_output(
                ["git", "show", f"{latest_head}:{rel}"], cwd=ROOT,
                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            latest_candidate_missing.append(rel)
            continue
        if frozen_bytes != latest_bytes:
            latest_candidate_changed.append(rel)
    checks["latest_candidate_record_matches_manifest"] = (
        latest_candidate.get("candidate_pr") == 8065 and
        latest_candidate.get("frozen_candidate_head") == freeze["candidate_head"] and
        latest_candidate.get("manifest_paths") == len(files) == 56 and
        latest_candidate.get("unchanged_paths") == 56 and
        latest_candidate.get("changed_paths") == [] and
        latest_candidate.get("missing_paths") == [] and
        latest_candidate.get("result") == "PASS_SOURCE_CLOSURE_UNCHANGED")
    checks["latest_candidate_56_source_bytes_match_frozen_head"] = (
        not latest_candidate_changed and not latest_candidate_missing)

    status = json.loads((RESULTS / "run-status.json").read_text())
    expected_routes = {"v12-perkey", "v15-default", "v15-perkey"}
    checks["all_three_routes_exit_zero"] = {row["route"] for row in status} == expected_routes and all(row["exit_code"] == 0 for row in status)
    outcomes = {}
    for route in sorted(expected_routes):
        folder = RESULTS / route
        result_bytes = (folder / "result.json").read_bytes()
        result = json.loads(result_bytes)
        stdout = json.loads((folder / "stdout.txt").read_text())
        checks[f"{route}_stdout_matches_result"] = stdout == result
        checks[f"{route}_stderr_empty"] = (folder / "stderr.txt").read_bytes() == b""
        checks[f"{route}_stopped_before_session_and_owner"] = (
            result.get("source_selection_finished") is True and
            result.get("session_started") is False and
            result.get("owner_instantiated") is False and
            result.get("forbidden_calls") == [])
        outcomes[route] = result

    v12 = outcomes["v12-perkey"]
    default = outcomes["v15-default"]
    perkey = outcomes["v15-perkey"]
    checks["v12_perkey_selects_archived_owner"] = (
        v12.get("owner_matches_a01") is True and
        v12.get("owner_file") == v12.get("expected_a01_owner_file") and
        v12.get("owner_sha256") == v12.get("expected_a01_owner_sha256"))
    checks["v15_default_selects_current_transition_wrapper"] = (
        default.get("owner_file") == "research/live_control/input_transition_owner_v4.py" and
        default.get("owner_matches_a01") is False)
    checks["v15_perkey_selects_current_raw_owner"] = (
        perkey.get("owner_file") == "research/live_control/input_owner_v12.py" and
        perkey.get("owner_matches_a01") is False and
        perkey.get("cached_owner_file") == "research/live_control/input_owner_v12.py")
    checks["v15_perkey_manifest_actual_identity_mismatch"] = (
        perkey.get("recorded_a01_owner_sha256") == perkey.get("expected_a01_owner_sha256") and
        perkey.get("owner_sha256") != perkey.get("recorded_a01_owner_sha256"))

    stop = ROOT / "results" / "system-python-stop"
    stop_text = (stop / "stderr.txt").read_text()
    checks["initial_missing_pillow_stop_preserved"] = (
        "ModuleNotFoundError: No module named 'PIL'" in stop_text and
        json.loads((stop / "run-status.json").read_text())[0]["exit_code"] == 1)
    result = {
        "schema": "v15-perkey-owner-identity-recheck-audit-v1",
        "disposition": "PASS_REPRODUCED_SOURCE_SELECTION_DEFECT" if all(checks.values()) else "FAIL_AUDIT",
        "passed": sum(checks.values()),
        "total": len(checks),
        "checks": checks,
        "source_failures": source_failures,
        "candidate_commit_mismatches": git_failures,
        "classification": "local source-selection construction only",
        "live_or_physical_release_claim": False,
    }
    output = ROOT / "results" / "AUDIT.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
