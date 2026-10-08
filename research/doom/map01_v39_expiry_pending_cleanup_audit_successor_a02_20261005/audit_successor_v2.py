"""Strict raw-only successor audit for merged ExecutorV12 A02 evidence."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate(data):
    if not (data.get("schema") == "map01-v39-expiry-pending-cleanup-a02-candidate-v1"):
        raise AssertionError("audit invariant failed")
    if not ("runner_error" not in data):
        raise AssertionError("audit invariant failed")
    events = data["events"]
    admissions = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_admission"]
    receipts = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_release_measurement"]
    terminals = [(i, e) for i, e in enumerate(events) if e.get("event") == "terminal"]
    if not (len(admissions) == len(receipts) == len(terminals) == 1):
        raise AssertionError("audit invariant failed")
    admission_index, admission = admissions[0]
    receipt_index, emitted = receipts[0]
    terminal_index, terminal = terminals[0]
    if not (admission_index < receipt_index < terminal_index):
        raise AssertionError("audit invariant failed")
    if not (admission.get("id") == "expiry-pending-a02"):
        raise AssertionError("audit invariant failed")
    if not (type(admission.get("step")) is int and admission["step"] == 0):
        raise AssertionError("audit invariant failed")
    if not (type(admission.get("intent_token")) is str and admission["intent_token"]):
        raise AssertionError("audit invariant failed")
    down = admission["physical_key_measurement"]
    if not (down.get("classification") == "CONFIRMED_PHYSICAL_DOWN"):
        raise AssertionError("audit invariant failed")
    if not (down.get("actuation_id")):
        raise AssertionError("audit invariant failed")

    expired = [r for r in data["owner_records_after_unblock"]
               if r.get("event") == "owner_release" and r.get("reason") == "expired"]
    if not (len(expired) == 1):
        raise AssertionError("audit invariant failed")
    owner_record = expired[0]
    if not (owner_record.get("verified") is True):
        raise AssertionError("audit invariant failed")
    if not (owner_record.get("keys_down") == []):
        raise AssertionError("audit invariant failed")
    if not (owner_record.get("buttons_down") == []):
        raise AssertionError("audit invariant failed")
    owner_rows = owner_record.get("per_key_release_measurements")
    if not (isinstance(owner_rows, list) and len(owner_rows) == 1):
        raise AssertionError("audit invariant failed")
    owner_up = owner_rows[0]
    identity_fields = ("id", "step", "intent_token", "key", "owner_id")
    identity = tuple(admission.get(k) for k in identity_fields)
    if not (tuple(owner_up.get(k) for k in identity_fields) == identity):
        raise AssertionError("audit invariant failed")
    if not (tuple(emitted.get(k) for k in identity_fields) == identity):
        raise AssertionError("audit invariant failed")
    if emitted.get("grants_input_authority") is not False:
        raise AssertionError("audit invariant failed")
    if "edge" in emitted and emitted.get("edge") != "up":
        raise AssertionError("audit invariant failed")
    if emitted.get("reason") != owner_record.get("reason"):
        raise AssertionError("audit invariant failed")
    up = owner_up.get("physical_key_measurement")
    emitted_up = emitted.get("physical_key_measurement")
    if not (up.get("classification") == "CONFIRMED_PHYSICAL_UP"):
        raise AssertionError("audit invariant failed")
    if not (up.get("actuation_id") == down["actuation_id"]):
        raise AssertionError("audit invariant failed")
    if not (emitted_up == up):
        raise AssertionError("audit invariant failed")

    terminal_record = terminal["interruption"]["record"]
    if not (terminal_record.get("event") == "owner_release"):
        raise AssertionError("audit invariant failed")
    if not (terminal_record.get("reason") == "expired"):
        raise AssertionError("audit invariant failed")
    if not (terminal_record.get("verified") is True):
        raise AssertionError("audit invariant failed")
    if not (terminal_record.get("keys_down") == []):
        raise AssertionError("audit invariant failed")
    if not (terminal_record.get("buttons_down") == []):
        raise AssertionError("audit invariant failed")
    if not (terminal_record.get("per_key_release_measurements") == [owner_up]):
        raise AssertionError("audit invariant failed")
    if not (terminal.get("status") == "expired"):
        raise AssertionError("audit invariant failed")
    if not (terminal.get("terminal_ns", -1) >= owner_record.get("verified_ns", 0)):
        raise AssertionError("audit invariant failed")
    if not (terminal.get("release", {}).get("verified") is True):
        raise AssertionError("audit invariant failed")
    if not (terminal["release"].get("keys_down") == []):
        raise AssertionError("audit invariant failed")
    if not (terminal["release"].get("buttons_down") == []):
        raise AssertionError("audit invariant failed")

    if not (data.get("owner_records_before_unblock") == []):

        raise AssertionError("audit invariant failed")
    if not (data.get("cursor_after_execute_drain") == 0):
        raise AssertionError("audit invariant failed")
    if not (data.get("physical_state_while_sync_blocked") == []):
        raise AssertionError("audit invariant failed")
    if not (data.get("fake_physical_keys_after_terminal") == []):
        raise AssertionError("audit invariant failed")
    if not (data.get("bridge_held_after_terminal") == []):
        raise AssertionError("audit invariant failed")
    if not (data.get("executor_active_after_terminal") is False):
        raise AssertionError("audit invariant failed")
    if not (not [e for e in events if e.get("event") in ("input_released", "input_release_unverified")]):
        raise AssertionError("audit invariant failed")
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
