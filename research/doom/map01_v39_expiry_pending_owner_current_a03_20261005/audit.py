"""Independent audit over the immutable current-owner A03 candidate output."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results/formal_01/candidate.json").read_text(encoding="utf-8"))
assert data["schema"] == "map01-v39-expiry-pending-current-owner-a03-v1"
assert "runner_error" not in data
events = data["events"]
admissions = [e for e in events if e.get("event") == "input_admission"]
terminals = [e for e in events if e.get("event") == "terminal"]
receipt_rows = [e for e in events if e.get("event") == "input_release_measurement"]
expiry_records = [r for r in data["owner_records_after_unblock"]
                  if r.get("event") == "owner_release" and r.get("reason") == "expired"]
assert len(admissions) == len(terminals) == len(receipt_rows) == len(expiry_records) == 1
admission = admissions[0]
assert (admission["id"], admission["step"], admission["intent_token"]) == (
    "expiry-pending-owner-a03", 0, "intent-expiry-pending-a03")
down = admission["physical_key_measurement"]
assert down["classification"] == "CONFIRMED_PHYSICAL_DOWN"
actuation_id = down["actuation_id"]
record = expiry_records[0]
assert record["verified"] is True and record["keys_down"] == [] and record["buttons_down"] == []
assert len(record["per_key_release_measurements"]) == 1
up = record["per_key_release_measurements"][0]
assert (up["id"], up["step"], up["intent_token"]) == (
    admission["id"], admission["step"], admission["intent_token"])
assert up["physical_key_measurement"]["classification"] == "CONFIRMED_PHYSICAL_UP"
assert up["physical_key_measurement"]["actuation_id"] == actuation_id
assert receipt_rows[0]["physical_key_measurement"]["actuation_id"] == actuation_id
assert receipt_rows[0]["id"] == admission["id"] and receipt_rows[0]["step"] == admission["step"]
assert terminals[0]["status"] == "expired"
assert terminals[0]["terminal_ns"] >= record["verified_ns"]
assert events.index(receipt_rows[0]) < events.index(terminals[0])
assert data["cursor_after_execute_drain"] == 0 and data["owner_records_before_unblock"] == []
assert data["physical_state_while_sync_blocked"] == []
assert data["fake_physical_keys_after_terminal"] == data["bridge_held_after_terminal"] == []
assert data["executor_active_after_terminal"] is False
report = {
    "status": "PASS_CURRENT_OWNER_PENDING_EXPIRY_RECEIPT_SCOPED",
    "scope": "one synthetic fake-display cleanup-pending interleaving",
    "candidate_head": "c4e893e8515811c77e21639237f1f2a914d4d88b",
    "admission_count": len(admissions),
    "owner_confirmed_per_key_up_count": len(record["per_key_release_measurements"]),
    "bridge_receipt_count": len(receipt_rows),
    "receipt_before_expired_terminal": True,
    "final_fake_physical_keys": data["fake_physical_keys_after_terminal"],
    "final_bridge_held": data["bridge_held_after_terminal"],
    "actuation_id": actuation_id,
}
(HERE / "results/formal_01/audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
