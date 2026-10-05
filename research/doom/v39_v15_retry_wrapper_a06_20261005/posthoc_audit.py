"""Audit the captured A06 runner record without rerunning its candidate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
runner_bytes = (ROOT / "RUNNER_OUTPUT.json").read_bytes()
lines = runner_bytes.decode("utf-8-sig").splitlines()
record = json.loads(next(line for line in reversed(lines) if line.startswith("{")))
raw = record["raw"]
trace = raw["trace"]
rows = raw["release_rows"]
edges = [row for row in trace if row.get("kind") in ("xtest_key_up_dropped", "xtest_key_up")]
edge_positions = [i for i, row in enumerate(trace)
                  if row.get("kind") in ("xtest_key_up_dropped", "xtest_key_up")]
query_positions = [i for i, row in enumerate(trace) if row.get("kind") == "query_keymap"]
by_key = {"a": 30, "b": 31}
receipts = [row.get("owner_thread_keyup_receipt") for row in rows]
checks = {
    "drop_then_retry": (len(edges) == 3 and edges[0].get("kind") == "xtest_key_up_dropped"
                        and edges[1].get("kind") == "xtest_key_up"
                        and edges[0].get("keycode") == edges[1].get("keycode") == 31),
    "remaining_keyup_completed": (len(edges) == 3 and edges[2].get("kind") == "xtest_key_up"
                                  and edges[2].get("keycode") == 30),
    "querymap_between_up_injections": (bool(edge_positions) and any(
        edge_positions[0] < position < edge_positions[-1] for position in query_positions)),
    "release_rows_match_key_identity": (len(rows) == 2 and len(receipts) == 2 and all(
        isinstance(receipt, dict) and receipt.get("key") == row.get("key")
        and receipt.get("keycode") == by_key.get(row.get("key"))
        and receipt.get("owner_id") == row.get("owner_id")
        and receipt.get("intent_token") == row.get("intent_token")
        for row, receipt in zip(rows, receipts))),
    "retry_attempts_verified": (len(receipts) == 2
        and receipts[0].get("server_keyup_attempt_count") == 2
        and receipts[0].get("server_keyup_verified") is True
        and receipts[0].get("server_keyup_attempts", [{}])[0].get("server_key_down_after") is True
        and receipts[0].get("server_keyup_attempts", [{}, {}])[1].get("server_key_down_after") is False),
    "verified_empty_batch": (len(rows) == 2 and all(
        row.get("release_batch_complete") is True
        and row.get("owner_transition_verified") is True
        and row.get("owner_thread_keyup_verified") is True
        and row.get("owned_keycodes_after_batch") == [] for row in rows)
        and raw.get("final_fake_keys") == []),
    "no_real_io_claim": raw.get("claims") == {
        "real_x11": False, "real_input": False, "application": False},
}
status = ("RAW_BEHAVIOR_CONFIRMED_AUDITOR_SCHEMA_BUG" if all(checks.values())
          and record.get("audit", {}).get("status") == "FAIL"
          else "POSTHOC_CHECK_FAILURE")
result = {
    "schema": "v39-v15-retry-wrapper-a06-posthoc-audit-v1",
    "status": status,
    "source": "Captured RUNNER_OUTPUT.json only; candidate was not rerun.",
    "checks": checks,
    "frozen_auditor_status": record.get("audit", {}).get("status"),
    "frozen_auditor_failed_check": "per_key_receipts_match_rows",
    "failure_explanation": (
        "Frozen auditor compared receipt.keycode with release_row.keycode; release rows "
        "expose key and nest keycode in owner_thread_keyup_receipt."
    ),
    "raw_output_sha256": hashlib.sha256(runner_bytes).hexdigest(),
}
(ROOT / "POSTHOC_AUDIT.json").write_text(
    json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
