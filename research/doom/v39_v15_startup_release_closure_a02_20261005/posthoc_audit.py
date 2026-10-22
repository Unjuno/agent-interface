"""Post-hoc audit of captured A02 output; never starts the candidate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
lines = (ROOT / "RUNNER_OUTPUT.json").read_text(encoding="utf-8-sig").splitlines()
record = json.loads(next(line for line in reversed(lines) if line.startswith("{")))
raw = record["raw"]
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
trace = raw["trace"]
rows = raw["release_rows"]
ups = [row for row in trace if row.get("kind") == "xtest_key_up"]
up_positions = [i for i, row in enumerate(trace) if row.get("kind") == "xtest_key_up"]
query_positions = [i for i, row in enumerate(trace) if row.get("kind") == "query_keymap"]
receipts = [row.get("owner_thread_keyup_receipt") for row in rows]
v15_keys = [key for key in freeze["session_manifest_sha256"]
            if key not in ("live_control/executor_v3.py", "live_control/executor_v11.py")]
source_hashes_match = all(
    hashlib.sha256((REPO / path).read_bytes()).hexdigest() == expected
    for path, expected in freeze["source_sha256"].items())
checks = {
    "frozen_source_closure_matches": source_hashes_match,
    "v15_selected_release_batch_backend": raw["selection"].get("backend") ==
        "doom_owner_thread_release_batch_backend_v1.Backend",
    "v15_selected_executor_v13": raw["selection"].get("executor") == "executor_v13.Executor",
    "v15_manifest_matches_declared_source_list": all(
        raw["session_source_hashes"].get(key) == freeze["session_manifest_sha256"][key]
        for key in v15_keys)
        and len(raw["session_source_hashes"]) == len(v15_keys),
    "two_reverse_order_up_injections": len(ups) == 2 and
        [row.get("keycode") for row in ups] == [31, 30],
    "no_inter_up_keymap_query": len(up_positions) == 2 and not any(
        up_positions[0] < pos < up_positions[1] for pos in query_positions),
    "two_identity_bound_receipts": len(rows) == len(receipts) == 2 and all(
        isinstance(receipt, dict) and receipt.get("key") == row.get("key")
        and receipt.get("keycode") == {"b": 31, "a": 30}.get(row.get("key"))
        and receipt.get("owner_id") == row.get("owner_id")
        and receipt.get("intent_token") == row.get("intent_token")
        for row, receipt in zip(rows, receipts)),
    "verified_empty_batch": len(rows) == 2 and all(
        row.get("release_batch_complete") is True
        and row.get("owner_transition_verified") is True
        and row.get("owner_thread_keyup_verified") is True
        and row.get("owned_keycodes_after_batch") == [] for row in rows)
        and raw.get("final_fake_keys") == [],
    "no_real_io_claimed": raw.get("claims") == {
        "real_x11": False, "real_input": False, "application": False,
        "game": False, "model": False},
}
frozen_failed = [key for key, passed in record["audit"]["checks"].items() if not passed]
result = {
    "schema": "v39-v15-startup-release-closure-a02-posthoc-audit-v1",
    "status": ("RAW_COMPOSITION_CONFIRMED_AUDITOR_SCOPE_MISMATCH"
               if all(checks.values()) and frozen_failed == ["v15_recorded_exact_source_manifest"]
               else "POSTHOC_CHECK_FAILURE"),
    "source": "Captured RUNNER_OUTPUT.json only; candidate was not rerun.",
    "checks": checks,
    "frozen_auditor_status": record["audit"]["status"],
    "frozen_auditor_failed_checks": frozen_failed,
    "failure_explanation": (
        "The freeze pins executor_v3 and executor_v11 as import dependencies; V15's "
        "declared sources.json manifest omits those two paths. All paths declared by "
        "V15 match their frozen hashes."
    ),
    "runner_output_sha256": hashlib.sha256(
        (ROOT / "RUNNER_OUTPUT.json").read_bytes()).hexdigest(),
}
(ROOT / "POSTHOC_AUDIT.json").write_text(
    json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
