"""Independent raw-only audit for the #5156 fake-Xlib host construction."""
import json
import sys
from pathlib import Path


def audit(rows):
    errors = []
    fixtures = [r for r in rows if r.get("event") == "fixture"]
    requests = [r for r in rows if r.get("event") == "owner_release_request"]
    syncs = [r for r in rows if r.get("event") == "owner_sync_return"]
    callers = [r for r in rows if r.get("event") == "caller_release_receipt"]
    states = [r for r in rows if r.get("event") == "fake_key_state"]
    terminals = [r for r in rows if r.get("event") == "terminal"]

    if len(fixtures) != 1 or fixtures[0].get("evidence_mode") != "synthetic-host":
        errors.append("expected exactly one explicitly synthetic-host fixture")
    if len(requests) != 1:
        errors.append("expected exactly one owner release request")
    if len(syncs) != 1:
        errors.append("expected exactly one owner sync return")
    if len(callers) != 1:
        errors.append("expected exactly one caller release receipt")
    if len(states) != 1:
        errors.append("expected exactly one fake key-state witness")
    if len(terminals) != 1:
        errors.append("expected exactly one terminal record")
    if errors:
        return {"decision": "FAIL_SYNTHETIC_OWNER_BRACKET_AUDIT", "errors": errors}

    request, sync, caller, state, terminal = requests[0], syncs[0], callers[0], states[0], terminals[0]
    occurrence_ids = {r.get("occurrence_id") for r in (request, sync, caller, state)}
    if len(occurrence_ids) != 1 or None in occurrence_ids:
        errors.append("occurrence identity is missing or inconsistent")
    for field in ("owner_id", "intent_token", "operation", "key", "keycode"):
        values = {r.get(field) for r in (request, sync, caller)}
        if len(values) != 1 or None in values:
            errors.append(f"{field} identity is missing or inconsistent")
    if request.get("event_type") != "KeyRelease" or caller.get("operation") != "up":
        errors.append("release operation/event type mismatch")
    if request.get("thread_name") != "input-owner":
        errors.append("release request was not observed on the owner thread")
    if sync.get("thread_name") != "input-owner":
        errors.append("sync return was not observed on the owner thread")

    times = [caller.get("call_started_ns"), request.get("request_ns"),
             sync.get("sync_return_ns"), caller.get("call_returned_ns")]
    if any(type(t) is not int or t < 0 for t in times):
        errors.append("timestamp missing or not a nonnegative integer")
    elif times != sorted(times):
        errors.append("caller/owner event order is not nested")
    if type(caller.get("interval_width_ns")) is not int or caller.get("interval_width_ns") != (
            caller.get("call_returned_ns", -1) - caller.get("call_started_ns", 0)):
        errors.append("caller interval width does not reconcile")
    if caller.get("x11_release_and_sync_completed_before_return") is not True:
        errors.append("wrapper did not attest return after underlying call")
    if caller.get("continuous_physical_state_sampled") is not False:
        errors.append("scope falsely claims continuous physical-state sampling")
    if caller.get("application_consumption_observed") is not False:
        errors.append("scope falsely claims application consumption")
    for row in (request, sync, caller, state, terminal):
        if row.get("grants_input_authority") is not False:
            errors.append("a row grants input authority")
    if state.get("down_before") is not True or state.get("down_after") is not False:
        errors.append("fake key state did not transition down to up")
    if terminal.get("owner_stopped") is not True or terminal.get("owner_thread_alive") is not False:
        errors.append("owner thread cleanup is not verified")
    if terminal.get("formal_x11") is not False or terminal.get("container") is not False:
        errors.append("synthetic run is mislabeled as formal X11/container evidence")

    return {
        "decision": "PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED" if not errors else "FAIL_SYNTHETIC_OWNER_BRACKET_AUDIT",
        "rows": len(rows),
        "release_occurrences": 1,
        "ordering": "caller_start <= owner_release_request <= owner_sync_return <= caller_return",
        "errors": errors,
        "scope": "fake-Xlib host construction only; no physical X11 or application effect",
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: audit_raw.py RAW.jsonl OUTPUT.json")
    raw_path, out_path = map(Path, argv[1:])
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
    result = audit(rows)
    Path(out_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED" else 1)


if __name__ == "__main__":
    main(sys.argv)
