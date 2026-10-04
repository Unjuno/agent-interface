"""Strict raw-only successor audit for merged ExecutorV12 A02 evidence."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate(data):
    assert data.get("schema") == "map01-v39-expiry-pending-cleanup-a02-candidate-v1"
    assert "runner_error" not in data
    events = data["events"]
    admissions = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_admission"]
    receipts = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_release_measurement"]
    terminals = [(i, e) for i, e in enumerate(events) if e.get("event") == "terminal"]
    assert len(admissions) == len(receipts) == len(terminals) == 1
    admission_index, admission = admissions[0]
    receipt_index, emitted = receipts[0]
    terminal_index, terminal = terminals[0]
    assert admission_index < receipt_index < terminal_index
    assert admission.get("id") == "expiry-pending-a02"
    assert type(admission.get("step")) is int and admission["step"] == 0
    assert type(admission.get("intent_token")) is str and admission["intent_token"]
    down = admission["physical_key_measurement"]
    assert down.get("classification") == "CONFIRMED_PHYSICAL_DOWN"
    assert down.get("actuation_id")

    expired = [r for r in data["owner_records_after_unblock"]
               if r.get("event") == "owner_release" and r.get("reason") == "expired"]
    assert len(expired) == 1
    owner_record = expired[0]
    assert owner_record.get("verified") is True
    assert owner_record.get("keys_down") == []
    assert owner_record.get("buttons_down") == []
    owner_rows = owner_record.get("per_key_release_measurements")
    assert isinstance(owner_rows, list) and len(owner_rows) == 1
    owner_up = owner_rows[0]
    identity_fields = ("id", "step", "intent_token", "key", "owner_id")
    identity = tuple(admission.get(k) for k in identity_fields)
    assert tuple(owner_up.get(k) for k in identity_fields) == identity
    assert tuple(emitted.get(k) for k in identity_fields) == identity
    up = owner_up.get("physical_key_measurement")
    emitted_up = emitted.get("physical_key_measurement")
    assert up.get("classification") == "CONFIRMED_PHYSICAL_UP"
    assert up.get("actuation_id") == down["actuation_id"]
    assert emitted_up == up

    terminal_record = terminal["interruption"]["record"]
    assert terminal_record.get("event") == "owner_release"
    assert terminal_record.get("reason") == "expired"
    assert terminal_record.get("verified") is True
    assert terminal_record.get("keys_down") == []
    assert terminal_record.get("buttons_down") == []
    assert terminal_record.get("per_key_release_measurements") == [owner_up]
    assert terminal.get("status") == "expired"
    assert terminal.get("terminal_ns", -1) >= owner_record.get("verified_ns", 0)
    assert terminal.get("release", {}).get("verified") is True
    assert terminal["release"].get("keys_down") == []
    assert terminal["release"].get("buttons_down") == []

    assert data.get("owner_records_before_unblock") == []
    assert data.get("cursor_after_execute_drain") == 0
    assert data.get("physical_state_while_sync_blocked") == []
    assert data.get("fake_physical_keys_after_terminal") == []
    assert data.get("bridge_held_after_terminal") == []
    assert data.get("executor_active_after_terminal") is False
    assert not [e for e in events if e.get("event") in ("input_released", "input_release_unverified")]
    return {
        "status": "PASS_RELEASE_ALL_DRAINED_PENDING_EXPIRY_RECEIPT_SCOPED",
        "scope": "frozen synthetic fake-display A02 raw only",
        "admission_count": 1,
        "owner_confirmed_up_count": 1,
        "emitted_confirmed_up_count": 1,
        "receipt_precedes_terminal": True,
        "full_identity_matches": True,
        "owner_keys_and_buttons_empty": True,
        "final_physical_and_bridge_held_empty": True,
    }


def main():
    data = json.loads((HERE / "results/formal_02/candidate.json").read_text(encoding="utf-8"))
    report = validate(data)
    (HERE / "results/formal_02/audit_successor.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
