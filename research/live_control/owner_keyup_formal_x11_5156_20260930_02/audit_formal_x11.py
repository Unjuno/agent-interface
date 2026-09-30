"""Independent raw-only audit for the one-shot #5156 X11 fixture."""
import hashlib
import json
import sys
from pathlib import Path


def audit(records, expected):
    errors = []
    if any(r.get("event") == "runner_failure" for r in records):
        errors.append("runner reported failure")
    admissions = {(r.get("case"), r.get("key")): r for r in records if r.get("event") == "admission"}
    want_admissions = {(case, key) for case, spec in expected["cases"].items() for key in spec["admit"]}
    if set(admissions) != want_admissions:
        errors.append(f"admission inventory mismatch: got={sorted(admissions)} want={sorted(want_admissions)}")
    for identity in want_admissions & set(admissions):
        row = admissions[identity]
        if row.get("down_verified") is not True or row.get("grants_input_authority") is not False:
            errors.append(f"admission not independently verified/non-authorizing: {identity}")
        if type(row.get("keycode")) is not int or not row.get("owner_id") or not row.get("intent_token"):
            errors.append(f"admission identity malformed: {identity}")

    joined = [r for r in records if r.get("event") == "joined_release"]
    auto_rows = []
    for envelope in records:
        if envelope.get("event") != "owner_record":
            continue
        row = envelope.get("record", {})
        if row.get("event") == "owner_key_release_bracket" and row.get("trigger_class") != "explicit_up":
            candidates = [(case, key, adm) for (case, key), adm in admissions.items()
                          if case == "partial_cancel" and adm.get("keycode") == row.get("keycode")]
            if len(candidates) == 1:
                case, key, _ = candidates[0]
                auto_rows.append(dict(row, case=case, expected_key=key))
            else:
                errors.append("autonomous release could not bind uniquely to admitted key")

    actual = {}
    for row in joined:
        identity = (row.get("case"), row.get("key"), "explicit_up")
        if identity in actual:
            errors.append(f"duplicate explicit release: {identity}")
        actual[identity] = row
    for row in auto_rows:
        identity = (row.get("case"), row.get("expected_key"), row.get("trigger_class"))
        if identity in actual:
            errors.append(f"duplicate autonomous release: {identity}")
        actual[identity] = row

    expected_ids = set()
    for case, spec in expected["cases"].items():
        for release in spec["release"]:
            expected_ids.add((case, release["key"], release["class"]))
    if set(actual) != expected_ids:
        errors.append(f"release inventory mismatch: got={sorted(actual)} want={sorted(expected_ids)}")

    for identity in expected_ids & set(actual):
        case, key, trigger = identity
        row = actual[identity]
        adm = admissions.get((case, key))
        if not adm:
            errors.append(f"release has no matching admission: {identity}")
            continue
        if row.get("owner_id") != adm.get("owner_id") or row.get("intent_token") != adm.get("intent_token"):
            errors.append(f"owner/intent identity mismatch: {identity}")
        if row.get("keycode") != adm.get("keycode"):
            errors.append(f"keycode mismatch: {identity}")
        if row.get("timing_valid") is not True:
            errors.append(f"owner timing invalid: {identity}")
        if row.get("grants_input_authority") is not False or row.get("physical_key_up_claimed") is not False:
            errors.append(f"authority or physical-key claim must remain false: {identity}")
        times = [row.get("request_started_ns"), row.get("request_returned_ns"), row.get("shared_sync_returned_ns")]
        if any(type(x) is not int for x in times) or not times[0] <= times[1] <= times[2]:
            errors.append(f"owner request/sync ordering invalid: {identity}")
        if trigger == "explicit_up":
            caller = [row.get("caller_started_ns"), row.get("caller_returned_ns")]
            if row.get("key") != key or any(type(x) is not int for x in caller):
                errors.append(f"explicit release caller/key receipt malformed: {identity}")
            elif not caller[0] <= times[0] <= times[1] <= times[2] <= caller[1]:
                errors.append(f"caller/owner nesting invalid: {identity}")
            if row.get("caller_owner_id") != row.get("owner_id") or row.get("caller_intent_token") != row.get("intent_token"):
                errors.append(f"caller receipt identity mismatch: {identity}")
        else:
            if row.get("key") is not None or "caller_started_ns" in row or "caller_returned_ns" in row:
                errors.append(f"autonomous cleanup must not fabricate caller timestamps/key: {identity}")
            if row.get("reason") != "cancelled":
                errors.append(f"autonomous cleanup reason mismatch: {identity}")

    terminals = {r.get("case"): r for r in records if r.get("event") == "case_terminal"}
    if set(terminals) != set(expected["cases"]):
        errors.append("case terminal inventory mismatch")
    for case in expected["cases"]:
        if case in terminals and terminals[case].get("all_up_verified") is not True:
            errors.append(f"case terminal state not verified: {case}")
    if terminals.get("partial_cancel", {}).get("second_admission_rejected") is not True:
        errors.append("cancel did not reject second admission")
    if len([r for r in records if r.get("event") == "process_cleanup" and r.get("owner_stopped") is True]) != 1:
        errors.append("owner process cleanup not verified exactly once")
    if len([r for r in records if r.get("event") == "terminal_state" and r.get("neutral") is True
             and r.get("grants_input_authority") is False]) != 1:
        errors.append("neutral terminal input state missing")
    if len([r for r in records if r.get("event") == "fixture"]) != 1:
        errors.append("fixture identity missing/duplicated")
    return errors


def main(raw_path, expected_path, audit_path):
    raw_bytes = Path(raw_path).read_bytes()
    records = [json.loads(line) for line in raw_bytes.splitlines() if line]
    expected_bytes = Path(expected_path).read_bytes()
    expected = json.loads(expected_bytes)
    errors = audit(records, expected)
    result = {"status": "PASS_OWNER_THREAD_KEYUP_BRACKET_SCOPED" if not errors else "FAIL_AUDIT",
              "errors": errors, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "expected_sha256": hashlib.sha256(expected_bytes).hexdigest(),
              "raw_rows": len(records), "allocation": expected["allocation"],
              "scope": "disposable X11 fixture only; XSync server-processing bracket, not application consumption"}
    Path(audit_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit_formal_x11.py RAW.jsonl EXPECTED.json AUDIT.json")
    raise SystemExit(main(*sys.argv[1:]))
