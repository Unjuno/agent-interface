import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
run = json.loads((ROOT / "RUN.json").read_text(encoding="utf-8"))
raw = (ROOT / run["raw_path"]).read_text(encoding="utf-8")
data = json.loads((ROOT / run["structured_path"]).read_text(encoding="utf-8"))
observations = data["observations"]
checks = {}
for row in manifest["files"]:
    content = (ROOT / row["path"]).read_bytes()
    checks["source:" + row["path"]] = (
        row["exact_git_blob_match"]
        and hashlib.sha256(content).hexdigest() == row["sha256"]
        and len(content) == row["bytes"]
    )
checks["run_exit_zero"] = run["exit_code"] == 0
checks["five_cases_pass"] = data["tests_run"] == 5 and not data["failures"] and not data["errors"]
checks["saved_unittest_output_passes"] = "Ran 5 tests" in raw and "OK" in raw
checks["candidate_cancel_cleanup_inside_bracket_fails_closed"] = any(
    o.get("candidate") is True and o.get("cause") == "cancelled"
    and o.get("owner_release_reason") == "cancelled"
    and o.get("owner_release_verified") is True
    and type(o.get("owner_release_verified_ns")) is int
    and type(o.get("release_call_started_ns")) is int
    and type(o.get("release_call_returned_ns")) is int
    and o["release_call_started_ns"] <= o["owner_release_verified_ns"] <= o["release_call_returned_ns"]
    and o.get("owner_cleanup_overlapped_release_call") is True
    and o.get("ordinary_release_candidate") is False
    and o.get("owner_transition_verified") is False
    for o in observations
)
checks["candidate_expiry_cleanup_inside_bracket_fails_closed"] = any(
    o.get("candidate") is True and o.get("cause") == "expired"
    and o.get("owner_release_reason") == "expired"
    and o.get("owner_release_verified") is True
    and type(o.get("owner_release_verified_ns")) is int
    and type(o.get("release_call_started_ns")) is int
    and type(o.get("release_call_returned_ns")) is int
    and o["release_call_started_ns"] <= o["owner_release_verified_ns"] <= o["release_call_returned_ns"]
    and o.get("owner_cleanup_overlapped_release_call") is True
    and o.get("ordinary_release_candidate") is False
    and o.get("owner_transition_verified") is False
    for o in observations
)
for cause in ("cancelled", "expired"):
    checks["parent_false_positive:" + cause] = any(
        o.get("candidate") is False and o.get("cause") == cause
        and o.get("owner_release_reason") == cause
        and o.get("owner_release_verified") is True
        and type(o.get("owner_release_verified_ns")) is int
        and type(o.get("release_call_started_ns")) is int
        and type(o.get("release_call_returned_ns")) is int
        and o["release_call_started_ns"] <= o["owner_release_verified_ns"] <= o["release_call_returned_ns"]
        and o.get("ordinary_release_candidate") is True
        and o.get("owner_transition_verified") is True
        for o in observations
    )
checks["candidate_no_cleanup_positive"] = any(
    o.get("candidate") is True and o.get("cause") == "none"
    and o.get("owner_cleanup_records_available") is True
    and o.get("owner_cleanup_overlapped_release_call") is False
    and o.get("ordinary_release_candidate") is True
    and o.get("owner_transition_verified") is True
    for o in observations
)
checks["all_scenarios_have_one_press_and_one_cleanup_release"] = all(
    o.get("xlib_event_count") == 2 and o.get("xlib_event_kinds") == [2, 3]
    for o in observations
)
checks["no_live_claim"] = "No physical input" in (ROOT / "README.md").read_text(encoding="utf-8")
audit = {
    "schema": "map01-v39-release-cleanup-owner-queue-composition-audit-v1",
    "checks": checks,
    "pass": all(checks.values()),
    "scope": "saved-source and saved-output audit; fake Xlib only",
}
(ROOT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print("PASS_OWNER_QUEUE_COMPOSITION" if audit["pass"] else "FAIL_OWNER_QUEUE_COMPOSITION")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["pass"]:
    raise SystemExit(1)
