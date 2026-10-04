"""Independent saved-output and exact-source audit for callback integration A01."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
latest_result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
checks = {}

for rel, identity in freeze["source_paths"].items():
    data = (ROOT / rel).read_bytes()
    checks[f"source_sha256:{rel}"] = hashlib.sha256(data).hexdigest() == identity["sha256"]
    blob = subprocess.check_output(["git", "hash-object", str(ROOT / rel)], cwd=ROOT, text=True).strip()
    checks[f"source_git_blob:{rel}"] = blob == identity["git_blob"]
checks["exact_frozen_base"] = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == freeze["base_commit"]
checks["latest_result_matches_run03"] = (
    latest_result.get("run_id") == "run-03"
    and latest_result.get("candidate_exit_code") == 0
    and latest_result.get("pass") is True
)

semantic_release_rows = {}
for run_id in ("run-02", "run-03"):
    run = HERE / "raw" / run_id
    events_raw = (run / "events.jsonl").read_bytes()
    delivered_raw = (run / "delivered.jsonl").read_bytes()
    events = [json.loads(line) for line in events_raw.splitlines()]
    owner_events = json.loads((run / "owner-events.json").read_text(encoding="utf-8"))
    release = [row for row in events if row.get("event") == "input_release_transition"]
    owner_up = [row for row in owner_events if row.get("event") == "owner_explicit_keyup"]
    verified_empty = [row for row in owner_events
                      if row.get("event") == "owner_release" and row.get("verified") is True
                      and row.get("keys_down") == [] and row.get("buttons_down") == []]
    prefix = run_id + ":"
    checks[prefix + "one_release_transition"] = len(release) == 1
    checks[prefix + "nested_owner_keyup_receipt_preserved"] = (
        len(release) == 1
        and release[0].get("owner_thread_keyup_receipt", {}).get("event") == "owner_explicit_keyup"
        and release[0]["owner_thread_keyup_receipt"].get("owner_sync_returned_ns") == 230
        and release[0].get("owner_thread_keyup_verified") is True
    )
    checks[prefix + "release_batch_identity_preserved"] = (
        len(release) == 1 and release[0].get("release_batch_identifier") == "p1"
        and release[0].get("release_batch_step") == 0
    )
    checks[prefix + "session_emit_timestamp_added"] = len(release) == 1 and type(release[0].get("emit_ns")) is int
    checks[prefix + "events_and_delivered_byte_identical"] = events_raw == delivered_raw
    checks[prefix + "one_explicit_owner_keyup_record"] = (
        len(owner_up) == 1 and owner_up[0].get("intent_token") == "integration-a01"
        and owner_up[0].get("server_sync_completed") is True
        and owner_up[0].get("physical_verification_authoritative") is False
    )
    checks[prefix + "verified_empty_owner_cleanup_serialized"] = bool(verified_empty)
    checks[prefix + "raw_log_and_score_files_present"] = all(
        (run / name).is_file() for name in ("events.jsonl", "delivered.jsonl", "owner-events.json", "score.json")
    )
    if len(release) == 1:
        keep = ("event", "operation", "key", "owner_id", "intent_token", "release_batch_identifier",
                "release_batch_step", "owner_transition_verified", "owner_thread_keyup_verified")
        semantic_release_rows[run_id] = {key: release[0].get(key) for key in keep}

checks["run02_and_run03_release_semantics_match"] = (
    len(semantic_release_rows) == 2
    and semantic_release_rows["run-02"] == semantic_release_rows["run-03"]
)
checks["construction_scope_and_no_live_allocation"] = (
    freeze.get("allocation_id") is None and freeze.get("classification") == "construction-only"
    and latest_result.get("scope", "").startswith("exact session source with fake X11")
)

audit = {
    "schema": "map01-v39-session-callback-emission-audit-v1",
    "checks": checks,
    "pass": all(checks.values()),
    "scope": "saved-output/source audit; fake X11, VizDoom, executor and owner only",
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
print(f"{'PASS' if audit['pass'] else 'FAIL'} {sum(checks.values())}/{len(checks)} checks")
if not audit["pass"]:
    raise SystemExit(1)
