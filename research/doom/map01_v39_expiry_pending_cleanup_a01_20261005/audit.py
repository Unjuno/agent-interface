"""Independent adjudication of the retained raw event and owner-record output."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results/formal_01/candidate.json").read_text(encoding="utf-8"))
assert data["schema"] == "map01-v39-expiry-pending-cleanup-candidate-v1"
assert "runner_error" not in data
events = data["events"]
admissions = [e for e in events if e.get("event") == "input_admission"]
terminals = [e for e in events if e.get("event") == "terminal"]
emitted_ups = [e for e in events if e.get("event") == "input_release_measurement"]
aggregate = [e for e in events if e.get("event") in ("input_released", "input_release_unverified")]
assert len(admissions) == 1 and len(terminals) == 1
assert admissions[0]["id"] == "expiry-pending-a01" and admissions[0]["step"] == 0
admission_measurement = admissions[0]["physical_key_measurement"]
actuation_id = admission_measurement["actuation_id"]
assert actuation_id and admission_measurement["classification"] == "CONFIRMED_PHYSICAL_DOWN"
expiry_records = [r for r in data["owner_records_after_unblock"]
                  if r.get("event") == "owner_release" and r.get("reason") == "expired"]
assert len(expiry_records) == 1
record = expiry_records[0]
assert record["verified"] is True and record["keys_down"] == [] and record["buttons_down"] == []
measurements = record["per_key_release_measurements"]
assert len(measurements) == 1
up = measurements[0]
assert (up["id"], up["step"], up["intent_token"]) == (
    admissions[0]["id"], admissions[0]["step"], admissions[0]["intent_token"])
up_measurement = up["physical_key_measurement"]
assert up_measurement["classification"] == "CONFIRMED_PHYSICAL_UP"
assert up_measurement["actuation_id"] == actuation_id
assert data["cursor_after_execute_drain"] == 0
assert data["owner_records_before_unblock"] == []
assert data["physical_state_while_sync_blocked"] == []
assert emitted_ups == []
terminal = terminals[0]
assert terminal["status"] == "expired"
assert terminal["release"]["verified"] is True
assert terminal["terminal_ns"] >= record["verified_ns"]
assert aggregate == []
assert data["fake_physical_keys_after_terminal"] == []
assert data["bridge_held_after_terminal"] == []
assert data["executor_active_after_terminal"] is False
report = {
    "status": "FAIL_RECEIPT_NOT_EMITTED_BEFORE_EXPIRY_TERMINAL",
    "scope": "synthetic fake-display cleanup-pending race only",
    "admission_event_count": len(admissions),
    "owner_confirmed_per_key_up_count": len(measurements),
    "bridge_emitted_per_key_up_count": len(emitted_ups),
    "owner_release_verified_before_terminal": True,
    "terminal_status": terminal["status"],
    "final_fake_physical_keys": data["fake_physical_keys_after_terminal"],
    "final_bridge_held": data["bridge_held_after_terminal"],
    "actuation_id": actuation_id,
}
(HERE / "results/formal_01/audit.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
