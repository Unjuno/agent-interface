"""Independent raw-only audit for the one-shot #5156 X11 fixture."""
import hashlib
import json
import re
import sys
from pathlib import Path


def audit(records, expected):
    errors = []
    if any(r.get("event") == "runner_failure" for r in records):
        errors.append("runner reported failure")
    admissions = {}
    for row in records:
        if row.get("event") != "admission":
            continue
        identity = (row.get("case"), row.get("key"))
        if identity in admissions:
            errors.append(f"admission identity duplicated: {identity}")
        else:
            admissions[identity] = row
    want_admissions = {(case, key) for case, spec in expected["cases"].items() for key in spec["admit"]}
    if set(admissions) != want_admissions:
        errors.append(f"admission inventory mismatch: got={sorted(admissions)} want={sorted(want_admissions)}")
    for identity in want_admissions & set(admissions):
        row = admissions[identity]
        if row.get("down_verified") is not True or row.get("grants_input_authority") is not False:
            errors.append(f"admission not independently verified/non-authorizing: {identity}")
        if type(row.get("keycode")) is not int or not row.get("owner_id") or not row.get("intent_token"):
            errors.append(f"admission identity malformed: {identity}")
    for case in expected["cases"]:
        codes = [row.get("keycode") for (c, _), row in admissions.items() if c == case]
        if len(codes) != len(set(codes)):
            errors.append(f"duplicate admitted keycode in case {case}")

    # XQueryKeymap witnesses are persisted as raw 256-bit snapshots. Summary
    # booleans are deliberately not accepted as a substitute for these bytes.
    witness_errors = []
    snapshots = {}
    expected_stages = {
        "single_explicit": {"pre_down": set(), "post_down": {"a"}, "post_release": set()},
        "two_key_explicit": {"pre_down": set(), "post_down": {"a", "b"}, "post_release": set()},
        "partial_cancel": {"pre_down": set(), "post_down": {"a"}, "post_cleanup": set()},
    }
    for row in records:
        if row.get("event") != "keymap_snapshot":
            continue
        case, stage = row.get("case"), row.get("stage")
        ident = (case, stage)
        if ident in snapshots:
            witness_errors.append(f"duplicate snapshot {ident}")
            continue
        snapshots[ident] = row
        keys = expected_stages.get(case, {}).get(stage)
        case_admissions = {key: adm.get("keycode") for (c, key), adm in admissions.items() if c == case}
        if keys is None:
            witness_errors.append(f"unexpected snapshot stage {ident}")
            continue
        if row.get("keycodes") != {key: case_admissions.get(key) for key in sorted(case_admissions)}:
            witness_errors.append(f"keycode identity mismatch {ident}")
        stamp = row.get("observed_ns")
        if type(stamp) is not int or stamp < 0:
            witness_errors.append(f"invalid observation timestamp {ident}")
        bitmap = row.get("bitmap_hex")
        try:
            raw = bytes.fromhex(bitmap) if isinstance(bitmap, str) else b""
        except ValueError:
            raw = b""
        if len(raw) != 32 or not isinstance(bitmap, str) or len(bitmap) != 64:
            witness_errors.append(f"bitmap must encode exactly 32 bytes {ident}")
            continue
        observed_down = set()
        expected_bitmap = bytearray(32)
        for key, code in case_admissions.items():
            if type(code) is not int or not 0 <= code < 256:
                witness_errors.append(f"invalid admitted keycode {ident}/{key}")
            else:
                if key in keys:
                    expected_bitmap[code // 8] |= 1 << (code % 8)
                if raw[code // 8] & (1 << (code % 8)):
                    observed_down.add(key)
        if observed_down != keys:
            witness_errors.append(f"bitmap state mismatch {ident}: got={sorted(observed_down)} want={sorted(keys)}")
        if raw != bytes(expected_bitmap):
            witness_errors.append(f"bitmap contains unaccounted key state {ident}")

    expected_snapshot_ids = {(case, stage) for case, stages in expected_stages.items() for stage in stages}
    if set(snapshots) != expected_snapshot_ids:
        witness_errors.append(f"snapshot inventory mismatch: got={sorted(snapshots)} want={sorted(expected_snapshot_ids)}")
    for case, stages in expected_stages.items():
        times = [snapshots.get((case, stage), {}).get("observed_ns") for stage in stages]
        if any(type(t) is not int for t in times) or times != sorted(times) or len(set(times)) != len(times):
            witness_errors.append(f"snapshot timestamps not strictly ordered for {case}")
        pre = snapshots.get((case, "pre_down"), {}).get("observed_ns")
        held = snapshots.get((case, "post_down"), {}).get("observed_ns")
        terminal_stage = "post_cleanup" if case == "partial_cancel" else "post_release"
        terminal = snapshots.get((case, terminal_stage), {}).get("observed_ns")
        if type(pre) is int and type(held) is int and pre >= held:
            witness_errors.append(f"pre-down snapshot must precede held snapshot for {case}")
    if witness_errors:
        errors.append("keymap witness: " + "; ".join(witness_errors))

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

    cancelled_owner_receipts = [envelope.get("record", {}) for envelope in records
                                if envelope.get("event") == "owner_record"
                                and envelope.get("record", {}).get("event") == "owner_release"
                                and envelope.get("record", {}).get("reason") == "cancelled"]
    if len(cancelled_owner_receipts) != 1:
        errors.append("cancelled owner-release receipt missing/duplicated")
    elif (cancelled_owner_receipts[0].get("verified") is not True
          or cancelled_owner_receipts[0].get("keys_down") != []
          or cancelled_owner_receipts[0].get("buttons_down") != []):
        errors.append("cancelled owner-release did not verify neutral state")

    actual = {}
    actual_sequence = []
    for row in joined:
        identity = (row.get("case"), row.get("key"), "explicit_up")
        if identity in actual:
            errors.append(f"duplicate explicit release: {identity}")
        actual[identity] = row
        actual_sequence.append(identity)
    for row in auto_rows:
        identity = (row.get("case"), row.get("expected_key"), row.get("trigger_class"))
        if identity in actual:
            errors.append(f"duplicate autonomous release: {identity}")
        actual[identity] = row
        actual_sequence.append(identity)

    expected_ids = set()
    expected_sequence = []
    for case, spec in expected["cases"].items():
        for release in spec["release"]:
            identity = (case, release["key"], release["class"])
            expected_ids.add(identity)
            expected_sequence.append(identity)
    if set(actual) != expected_ids:
        errors.append(f"release inventory mismatch: got={sorted(actual)} want={sorted(expected_ids)}")
    if actual_sequence != expected_sequence:
        errors.append(f"release order mismatch: got={actual_sequence} want={expected_sequence}")

    for case in expected_stages:
        held = snapshots.get((case, "post_down"), {}).get("observed_ns")
        terminal_stage = "post_cleanup" if case == "partial_cancel" else "post_release"
        terminal = snapshots.get((case, terminal_stage), {}).get("observed_ns")
        release_rows = [row for identity, row in actual.items() if identity[0] == case]
        starts = [r.get("request_started_ns") for r in release_rows]
        finishes = [r.get("shared_sync_returned_ns") for r in release_rows]
        if release_rows:
            if type(held) is not int or any(type(t) is not int or held >= t for t in starts):
                errors.append(f"keymap witness: held snapshot must precede release request for {case}")
            if type(terminal) is not int or any(type(t) is not int or terminal <= t for t in finishes):
                errors.append(f"keymap witness: terminal snapshot must follow release sync for {case}")

    for identity in expected_ids & set(actual):
        case, key, trigger = identity
        row = actual[identity]
        if trigger == "explicit_up" and row.get("owner_event") != "owner_key_release_bracket":
            errors.append(f"source owner event provenance invalid: {identity}")
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
            if row.get("trigger_class") != "explicit_up":
                errors.append(f"explicit release class mismatch: {identity}")
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

    terminals = {}
    for row in records:
        if row.get("event") != "case_terminal":
            continue
        case = row.get("case")
        if case in terminals:
            errors.append(f"case terminal duplicated: {case}")
        else:
            terminals[case] = row
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
    else:
        fixture = next(r for r in records if r.get("event") == "fixture")
        if (fixture.get("allocation") != expected.get("allocation")
                or fixture.get("frozen_main") != expected.get("frozen_main")):
            errors.append("fixture identity does not match expected allocation/frozen main")
    complete = [r for r in records if r.get("event") == "runner_complete" and r.get("exit_code") == 0]
    if len(complete) != 1:
        errors.append("runner completion sentinel missing/duplicated")
    return errors


def validate_host_launch_receipt(receipt, raw_bytes, expected_bytes, expected, fixture):
    errors = []
    if not isinstance(receipt, dict) or receipt.get("schema") != "formal-x11-host-launch-v1":
        return ["invalid formal X11 host launch receipt schema"]
    expected_fields = {
        "allocation": expected.get("allocation"),
        "frozen_main": expected.get("frozen_main"),
        "runner_sha256": hashlib.sha256((Path(__file__).parent / "run_formal_x11.py").read_bytes()).hexdigest(),
        "expected_sha256": hashlib.sha256(expected_bytes).hexdigest(),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_exit_code": 0,
        "container_exit_code": 0,
    }
    for field, value in expected_fields.items():
        if receipt.get(field) != value or (field.endswith("exit_code") and type(receipt.get(field)) is not int):
            errors.append(f"host launch receipt {field} mismatch")
    if not isinstance(receipt.get("container_id"), str) or not re.fullmatch(r"[0-9a-f]{64}", receipt["container_id"]):
        errors.append("host launch receipt container_id is not a full Docker container ID")
    digest = receipt.get("image_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        errors.append("host launch receipt image_digest is invalid")
    if not isinstance(receipt.get("platform"), str) or not re.fullmatch(r"linux/[a-z0-9_]+", receipt["platform"]):
        errors.append("host launch receipt platform is invalid")
    if not isinstance(receipt.get("engine_context"), str) or not receipt["engine_context"]:
        errors.append("host launch receipt engine_context is missing")
    if not isinstance(receipt.get("argv"), list) or receipt["argv"] != ["python3", "-B", "run_formal_x11.py", "raw.jsonl"]:
        errors.append("host launch receipt argv mismatch")
    if (fixture.get("image_digest") != digest or fixture.get("platform") != receipt.get("platform")
            or not isinstance(fixture.get("display"), str) or not fixture["display"].startswith(":")
            or fixture.get("evidence_mode") != "formal-x11"):
        errors.append("raw formal fixture identity does not match host launch receipt")
    return errors


def main(raw_path, expected_path, audit_path, mode, receipt_path=None):
    raw_bytes = Path(raw_path).read_bytes()
    records = [json.loads(line) for line in raw_bytes.splitlines() if line]
    expected_bytes = Path(expected_path).read_bytes()
    expected = json.loads(expected_bytes)
    errors = audit(records, expected)
    fixtures = [r for r in records if r.get("event") == "fixture"]
    marker_values = [r.get("synthetic_only") for r in fixtures]
    if mode == "synthetic-cli":
        synthetic_only = True
        if receipt_path is not None:
            errors.append("synthetic-cli mode must not accept a formal host launch receipt")
        if (len(fixtures) != 1 or marker_values != [True]
                or fixtures[0].get("evidence_mode") != "synthetic-cli"):
            errors.append("synthetic-cli mode requires exactly one fixture marked synthetic_only=true")
    else:
        synthetic_only = False
        if (len(fixtures) != 1 or fixtures[0].get("evidence_mode") != "formal-x11"
                or any("synthetic_only" in fixture for fixture in fixtures)):
            errors.append("formal-x11 mode requires exactly one explicit formal-x11 fixture without synthetic markers")
        if receipt_path is None:
            errors.append("formal-x11 mode requires an out-of-band host launch receipt")
        elif len(fixtures) == 1:
            try:
                receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
                errors.extend(validate_host_launch_receipt(receipt, raw_bytes, expected_bytes, expected, fixtures[0]))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"formal X11 host launch receipt unreadable: {type(exc).__name__}")
    pass_status = ("PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY" if synthetic_only
                   else "PASS_OWNER_THREAD_KEYUP_BRACKET_SCOPED")
    result = {"status": pass_status if not errors else "FAIL_AUDIT",
              "errors": errors, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "expected_sha256": hashlib.sha256(expected_bytes).hexdigest(),
              "raw_rows": len(records), "allocation": expected["allocation"],
              "scope": ("synthetic JSONL serialization/process boundary only; no X server or physical input evidence"
                        if synthetic_only else
                        ("disposable X11 fixture only; host launch receipt matched to raw/source/image; XSync server-processing bracket, not application consumption"
                         if not any("host launch receipt" in error or "receipt" in error for error in errors)
                         else "formal X11 provenance unverified; raw bytes alone do not establish server origin"))}
    Path(audit_path).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    if (len(sys.argv) not in (5, 6) or sys.argv[4] not in ("formal-x11", "synthetic-cli")
            or (sys.argv[4] == "synthetic-cli" and len(sys.argv) != 5)):
        raise SystemExit("usage: audit_formal_x11.py RAW.jsonl EXPECTED.json AUDIT.json synthetic-cli | formal-x11 HOST_LAUNCH_RECEIPT.json")
    raise SystemExit(main(*sys.argv[1:]))
