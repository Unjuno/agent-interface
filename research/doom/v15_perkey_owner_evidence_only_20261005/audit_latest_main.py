"""Compare the frozen owner-selection finding with the latest main source closure."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = "11445a7ca200404ddc80bf7ebb1dbef86eb059de"
MAIN = "b6907899f11b036f2af572e8d4794ebb4b7e5c83"
LATEST_CANDIDATE = "6591b5703862c73d375a6646374ad82a26505bcb"
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())
MANIFEST = json.loads((ROOT / "source-manifest.json").read_text())

def git_bytes(rev, path):
    p = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.stdout if p.returncode == 0 else None

def sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None

changed, missing, shared = [], [], []
candidate_changed, candidate_missing = [], []
for path in MANIFEST["files"]:
    before, now = git_bytes(BASE, path), git_bytes(MAIN, path)
    frozen, latest = git_bytes(FREEZE["candidate_head"], path), git_bytes(LATEST_CANDIDATE, path)
    if frozen is None or latest is None:
        candidate_missing.append(path)
    elif frozen != latest:
        candidate_changed.append(path)
    if before is None:
        if git_bytes(FREEZE["candidate_head"], path) is not None and now is None:
            missing.append(path)
        else:
            changed.append({"path": path, "status": "missing_from_candidate_base_or_main"})
    elif now is None:
        missing.append(path)
    else:
        shared.append(path)
        if before != now:
            changed.append({"path": path, "status": "bytes_changed",
                            "base_sha256": sha(before), "current_main_sha256": sha(now)})
expected_owner = "research/live_control/input_owner_v12.py"
selector = "research/doom/session_map01_v15.py"
owner_result = json.loads((ROOT / "results/bundled-run/v15-perkey/result.json").read_text())
expected_archive_sha = owner_result["expected_a01_owner_sha256"]
current_owner_sha = sha(git_bytes(MAIN, expected_owner))
checks = {
    "manifest_has_56_frozen_sources": len(MANIFEST["files"]) == 56,
    "55_paths_shared_with_candidate_base": len(shared) == 55,
    "only_current_main_source_delta_is_owner_v12": [item["path"] for item in changed] == [expected_owner],
    "candidate_selection_helper_remains_absent_from_main": missing == ["research/doom/v39_measurement_backend_selection_v1.py"],
    "v15_selector_source_unchanged_since_candidate_base": git_bytes(BASE, selector) == git_bytes(MAIN, selector),
    "56_frozen_sources_unchanged_on_latest_candidate_head": not candidate_changed and not candidate_missing,
    "frozen_v15_perkey_result_still_records_owner_identity_mismatch": (
        owner_result["owner_file"] == expected_owner and
        owner_result["owner_sha256"] != expected_archive_sha and
        owner_result["owner_instantiated"] is False and
        owner_result["session_started"] is False),
    "latest_main_owner_bytes_still_differ_from_archived_a01_identity": current_owner_sha != expected_archive_sha,
}
report = {
    "schema": "v15-perkey-latest-main-source-identity-audit-v1",
    "candidate_head": FREEZE["candidate_head"],
    "candidate_base": BASE,
    "current_main_commit": MAIN,
    "latest_candidate_head": LATEST_CANDIDATE,
    "latest_candidate_changed_paths": candidate_changed,
    "latest_candidate_missing_paths": candidate_missing,
    "manifest_paths": len(MANIFEST["files"]),
    "shared_path_count": len(shared),
    "shared_paths_changed": changed,
    "candidate_only_paths": missing,
    "latest_main_owner_sha256": current_owner_sha,
    "archived_a01_owner_sha256": expected_archive_sha,
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "disposition": "PASS_FROZEN_SELECTION_WITH_CANDIDATE_AND_MAIN_STATIC_REFRESHES" if all(checks.values()) else "FAIL_OR_REVIEW",
    "classification": "frozen candidate source-selection only; latest-main static identity comparison; no candidate rerun",
    "live_or_physical_release_claim": False,
}
(ROOT / "CURRENT_MAIN_RECHECK_LATEST.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
(ROOT / "LATEST_CANDIDATE_RECHECK.json").write_text(json.dumps({
    "candidate_pr": 8065,
    "comparison": "git show <frozen_head>:<path> byte-for-byte against git show <latest_head>:<path>",
    "frozen_candidate_head": FREEZE["candidate_head"],
    "latest_candidate_head": LATEST_CANDIDATE,
    "manifest_paths": len(MANIFEST["files"]),
    "unchanged_paths": len(MANIFEST["files"]) - len(candidate_changed) - len(candidate_missing),
    "changed_paths": candidate_changed,
    "missing_paths": candidate_missing,
    "result": "PASS_SOURCE_CLOSURE_UNCHANGED" if not candidate_changed and not candidate_missing else "FAIL_OR_REVIEW",
    "schema": "v15-perkey-latest-candidate-source-closure-v1",
    "source_manifest": "source-manifest.json",
    "source_ref_read": "refs/pull/8065/head",
}, indent=2, sort_keys=True) + "\n")
(ROOT / "results/AUDIT_LATEST_MAIN.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
