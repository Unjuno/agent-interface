"""Versioned saved-record audit with normalized source-head labels."""
import hashlib
import json
import sys
from pathlib import Path


root = Path(__file__).resolve().parent
freeze = json.loads((root / "PRE-RUN.json").read_text(encoding="utf-8"))
raw = json.loads((root / "RAW.json").read_text(encoding="utf-8"))
hashes = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in freeze["source_sha256"]
}
b = raw["before_close"]
a = raw["after_close"]
checks = {
    "frozen_source_hashes_match": hashes == freeze["source_sha256"],
    "run_id_matches_freeze": raw["run_id"] == freeze["run_id"],
    "run_schema_matches": raw["schema"] == "admission-baseline-sink-compose-a02-v1",
    "candidate_and_comparison_heads_match":
        raw["candidate_source"].endswith(freeze["candidate_source"]) and
        raw["comparison_fix_source"].endswith(freeze["comparison_fix_source"]),
    "accepted_sink_exception_observed":
        raw["submit_error"] is not None and
        raw["submit_error"]["type"] == "RuntimeError" and
        "acknowledgement loss" in raw["submit_error"]["message"],
    "accepted_event_was_sink_visible_before_exception":
        len([e for e in b["events"] if e.get("event") == "accepted"]) == 1,
    "baseline_hook_not_called": b["baseline_calls"] == [],
    "no_worker_or_backend_step":
        b["worker_started"] is False and b["worker_alive"] is False and
        b["backend_execute_count"] == 0,
    "uncertain_admission_slot_and_id_retained":
        b["active_id"] == "sink-compose-1" and b["backend_lease_matches_active"] and
        b["used_id_retained"],
    "close_failure_reproduced":
        raw["close_error"] is not None and
        raw["close_error"]["type"] == "RuntimeError" and
        "cannot join thread before it is started" in raw["close_error"]["message"],
    "failed_close_leaves_stale_slot":
        a["active_id"] == "sink-compose-1" and a["backend_lease_retained"] and
        a["worker_started"] is False,
    "no_terminal_or_release_claim":
        not any(e.get("event") in ("terminal", "input_released", "input_release_unverified")
                for e in b["events"]),
}
result = {
    "schema": "admission-baseline-sink-compose-a02-audit-v2",
    "classification": "COMPOSITION_STOP_REPRODUCED" if all(checks.values())
                      else "AUDIT_HOLD",
    "checks": checks,
    "passed": all(checks.values()),
    "errors": [name for name, ok in checks.items() if not ok],
    "scope": "saved-record audit only; no game, model, X server, or physical input",
    "supersedes": "AUDIT-v1.json only for source-head label normalization; no candidate rerun",
}
(root / "AUDIT-v2.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, sort_keys=True))
sys.exit(0 if result["passed"] else 1)
