"""Audit only the immutable A02 candidate output."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "results/formal_02/candidate.json").read_text(encoding="utf-8"))
assert data["schema"] == "map01-v39-expiry-pending-cleanup-a02-candidate-v1"
assert "runner_error" not in data
events = data["events"]
admissions = [e for e in events if e.get("event") == "input_admission"]
terminals = [e for e in events if e.get("event") == "terminal"]
ups = [e for e in events if e.get("event") == "input_release_measurement"]
aggregate = [e for e in events if e.get("event") in ("input_released", "input_release_unverified")]
assert len(admissions) == len(terminals) == len(ups) == 1
admission = admissions[0]
assert admission["id"] == "expiry-pending-a02" and admission["step"] == 0
down = admission["physical_key_measurement"]
assert down["classification"] == "CONFIRMED_PHYSICAL_DOWN"
record = [r for r in data["owner_records_after_unblock"]
          if r.get("event") == "owner_release" and r.get("reason") == "expired"]
assert len(record) == 1
record = record[0]
measurement = record["per_key_release_measurements"]
assert record["verified"] is True and record["keys_down"] == [] and len(measurement) == 1
up = measurement[0]
assert (up["id"], up["step"], up["intent_token"]) == (admission["id"], admission["step"], admission["intent_token"])
assert up["physical_key_measurement"]["classification"] == "CONFIRMED_PHYSICAL_UP"
assert up["physical_key_measurement"]["actuation_id"] == down["actuation_id"]
assert ups[0]["id"] == admission["id"] and ups[0]["physical_key_measurement"]["actuation_id"] == down["actuation_id"]
assert terminals[0]["status"] == "expired"
assert terminals[0]["terminal_ns"] >= record["verified_ns"]
assert data["owner_records_before_unblock"] == [] and data["cursor_after_execute_drain"] == 0
assert data["physical_state_while_sync_blocked"] == [] and aggregate == []
assert data["fake_physical_keys_after_terminal"] == data["bridge_held_after_terminal"] == []
assert data["executor_active_after_terminal"] is False
report = {
    "status": "PASS_RELEASE_ALL_DRAINED_PENDING_EXPIRY_RECEIPT_SCOPED",
    "scope": "synthetic fake-display cleanup-pending race only",
    "admission_event_count": len(admissions),
    "owner_confirmed_per_key_up_count": len(measurement),
    "bridge_emitted_per_key_up_count": len(ups),
    "owner_release_verified_before_terminal": True,
    "terminal_status": terminals[0]["status"],
    "final_fake_physical_keys": data["fake_physical_keys_after_terminal"],
    "final_bridge_held": data["bridge_held_after_terminal"],
    "actuation_id": down["actuation_id"],
}
(HERE / "results/formal_02/audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))

