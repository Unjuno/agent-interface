"""Read-only post-run reconciliation; does not import or execute candidate code."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text())
raw_path = HERE / "results/A06/RAW.jsonl"
cases = [json.loads(line) for line in raw_path.read_text().splitlines()]
by_name = {row["case"]: row for row in cases}
errors = []
if list(by_name) != ["normal", "drop_explicit_space_once", "cleanup_query_unavailable_once"]:
    errors.append("case_sequence_or_custody")
normal = by_name.get("normal", {})
dropped = by_name.get("drop_explicit_space_once", {})
unavailable = by_name.get("cleanup_query_unavailable_once", {})
if len([row for row in normal.get("release_rows", [])
        if row.get("event") == "input_release_transition"]) != 2:
    errors.append("normal_release_transition_count")
if normal.get("close_error") or normal.get("fake_keys_after_close") != []:
    errors.append("normal_cleanup")
drop_events = dropped.get("events", [])
release_keys = [row.get("keycode") for row in drop_events
                if row.get("event") == "key_up"]
if (sum(row.get("event") == "key_up_dropped_once" for row in drop_events) != 1
        or dropped.get("dropped_up_once") is not True
        or dropped.get("close_error") != "RuntimeError"
        or dropped.get("fake_keys_after_close") != [65]
        or release_keys != [38]):
    errors.append("one_shot_drop_observation")
release_record = next((row for row in dropped.get("owner_records", [])
                       if row.get("event") == "owner_release"), {})
if (release_record.get("verified") is not False
        or release_record.get("keys_down") != [65]):
    errors.append("owner_close_failed_to_reconcile_down_key")
if (unavailable.get("close_error") != "RuntimeError"
        or not any(row.get("event") == "query_keymap_unavailable"
                   for row in unavailable.get("events", []))):
    errors.append("query_failure_not_retained")
source_errors = [path for path, digest in freeze["source_sha256"].items()
                 if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest]
if source_errors:
    errors.extend("source_hash:" + path for path in source_errors)
result = {
    "status": "PASS_RAW_RECONCILIATION" if not errors else "FAIL_RAW_RECONCILIATION",
    "errors": errors,
    "candidate_hypothesis": "REJECTED: owner close detects the silently retained key but does not retry its KeyRelease",
    "candidate_invocation_exit": (HERE / "results/A06/candidate.exit.txt").read_text().strip(),
    "preregistered_auditor_status": json.loads(
        (HERE / "results/A06/AUDIT.json").read_text()).get("status"),
    "cases": list(by_name),
    "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "scope": "post-run raw/source reconciliation only; fake Xlib, no physical or application authority",
}
(HERE / "results/A06/POSTHOC_RECONCILIATION.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if not errors else 1)
