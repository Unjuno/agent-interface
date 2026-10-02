from __future__ import annotations
import copy
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALLOC = "MAP01-OWNER-KEYUP-BRACKET-5156-WSLC-20261002-18"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8")) if (HERE / "FREEZE.json").exists() else {}
EXPECTED = {"explicit_order": [("intent-1", "w", "single"),
                              ("intent-2", "w", "two_key_order_1"),
                              ("intent-2", "a", "two_key_order_2")],
            "admissions": [("intent-1", "w"), ("intent-2", "w"), ("intent-2", "a"), ("intent-3", "w")],
            "keycodes": {"w": 25, "a": 38}}


def is_int(v):
    return type(v) is int and v > 0


def audit(raw):
    errors = []
    def require(condition, code):
        if not condition:
            errors.append(code)

    require(type(raw) is dict, "raw_not_object")
    if type(raw) is not dict:
        return ["raw_not_object"]
    require(raw.get("schema") == "owner-keyup-wslc-candidate-v1", "schema")
    require(raw.get("allocation_id") == ALLOC, "allocation")
    require(raw.get("image_id") == FREEZE.get("image_id"), "image_id")
    require(raw.get("source_sha256") == FREEZE.get("source_sha256"), "source_hashes")
    require(raw.get("candidate_status") == "PASS_CANDIDATE_SHAPE", "candidate_status")
    require(raw.get("candidate_completed") is True, "candidate_incomplete")
    require(raw.get("errors") == [], "candidate_errors")
    require(raw.get("authority_granted") is False, "authority_granted")
    require(raw.get("external_effects") == 0 and raw.get("model_calls") == 0, "external_activity")
    require(raw.get("processes_clean") is True and raw.get("owner_thread_stopped") is True, "cleanup")
    require(type(raw.get("xvfb_exit_code")) is int, "xvfb_exit_missing")
    require(is_int(raw.get("candidate_started_ns")) and is_int(raw.get("candidate_finished_ns")) and
            raw.get("candidate_finished_ns", 0) >= raw.get("candidate_started_ns", 0), "candidate_clock")
    owner_id = raw.get("owner_id")
    require(type(owner_id) is str and len(owner_id) == 32, "owner_id")
    require(raw.get("keycodes") == EXPECTED["keycodes"], "keycode_map")

    cases = raw.get("cases")
    calls = raw.get("explicit_calls")
    records = raw.get("owner_snapshots_final")
    require(type(cases) is list, "cases_type")
    require(type(calls) is list and len(calls) == 3, "explicit_call_count")
    require(type(records) is list, "owner_snapshot_type")
    if type(cases) is not list or type(calls) is not list or type(records) is not list:
        return errors

    explicit_records = [r for r in records if type(r) is dict and r.get("event") == "owner_explicit_key_up"]
    require(len(explicit_records) == 3, "explicit_owner_row_count")
    observed_call_keys = [(c.get("intent_token"), c.get("key"), c.get("case")) for c in calls if type(c) is dict]
    require(observed_call_keys == EXPECTED["explicit_order"], "explicit_order")
    for index, (call, expected_tuple) in enumerate(zip(calls, EXPECTED["explicit_order"])):
        if type(call) is not dict:
            require(False, f"call_{index}_type")
            continue
        token, key, case_name = expected_tuple
        require(call.get("intent_token") == token and call.get("key") == key and call.get("case") == case_name,
                f"call_{index}_identity")
        keycode = EXPECTED["keycodes"].get(key)
        require(call.get("keycode") == keycode, f"call_{index}_keycode")
        require(call.get("key_down_before") is True and call.get("key_down_after") is False,
                f"call_{index}_keymap")
        receipt = call.get("caller_receipt")
        require(type(receipt) is dict, f"call_{index}_receipt")
        if type(receipt) is dict:
            require(receipt.get("event") == "input_release_transition" and
                    receipt.get("transition_schema") == "input-release-transition-v3" and
                    receipt.get("operation") == "up" and receipt.get("key") == key and
                    receipt.get("owner_id") == owner_id and receipt.get("intent_token") == token and
                    receipt.get("grants_input_authority") is False, f"call_{index}_caller_contract")
            caller_start = receipt.get("release_call_started_ns")
            caller_return = receipt.get("release_call_returned_ns")
        else:
            caller_start = caller_return = None
        appended = call.get("owner_rows_appended")
        require(type(appended) is list and len(appended) == 1, f"call_{index}_owner_append_count")
        row = appended[0] if type(appended) is list and len(appended) == 1 else None
        if type(row) is dict:
            require(row.get("event") == "owner_explicit_key_up" and row.get("owner_id") == owner_id and
                    row.get("intent_token") == token and row.get("keycode") == keycode and
                    row.get("grants_input_authority") is False, f"call_{index}_owner_identity")
            start = row.get("release_request_ns")
            sync_return = row.get("sync_return_ns")
            require(is_int(start) and is_int(sync_return) and sync_return >= start, f"call_{index}_owner_times")
            require(is_int(caller_start) and is_int(caller_return) and caller_start <= start <= sync_return <= caller_return,
                    f"call_{index}_nested_bracket")
            require(row in explicit_records, f"call_{index}_snapshot_join")
        else:
            require(False, f"call_{index}_owner_row")

    admission_cases = [c for c in cases if type(c) is dict and c.get("event") == "admission"]
    admission_keys = [(c.get("intent_token"), c.get("key")) for c in admission_cases]
    require(admission_keys == EXPECTED["admissions"], "admission_order")
    require(len(admission_cases) == 4, "admission_count")
    for index, case in enumerate(admission_cases):
        key = case.get("key")
        receipt = case.get("receipt")
        require(case.get("key_down_after") is True and case.get("keycode") == EXPECTED["keycodes"].get(key),
                f"admission_{index}_keymap")
        require(type(receipt) is dict and receipt.get("event") == "input_admission" and
                receipt.get("key") == key and receipt.get("intent_token") == case.get("intent_token") and
                is_int(receipt.get("admitted_ns")) and is_int(receipt.get("input_ack_ns")) and
                receipt.get("input_ack_ns", 0) >= receipt.get("admitted_ns", 0), f"admission_{index}_receipt")

    stale = [c for c in cases if type(c) is dict and c.get("event") == "stale_release"]
    require(len(stale) == 1, "stale_count")
    if len(stale) == 1:
        s = stale[0]
        require(s.get("rejected") is True and type(s.get("error")) is dict and
                s["error"].get("type") == "ValueError" and s.get("receipt") is None and
                s.get("owner_rows_appended") == [] and s.get("w_down_after") is True and
                s.get("a_down_after") is True and s.get("intent_token") == "intent-stale" and
                s.get("foreign_to") == "intent-2", "stale_release_contract")

    cancelled = [c for c in cases if type(c) is dict and c.get("event") == "cancel_cleanup"]
    require(len(cancelled) == 1, "cancel_count")
    cancel_row = None
    if len(cancelled) == 1:
        c = cancelled[0]
        require(type(c.get("cancelled_down_error")) is dict and
                c["cancelled_down_error"].get("type") == "Cancelled" and
                c.get("intent_token") == "intent-3" and c.get("a_down_after") is False and
                c.get("w_down_after") is False, "cancel_admission_contract")
        require(is_int(c.get("requested_ns")) and is_int(c.get("receipt_wait_started_ns")) and
                is_int(c.get("receipt_wait_finished_ns")) and
                c.get("receipt_wait_finished_ns", 0) >= c.get("receipt_wait_started_ns", 0) and
                c.get("receipt_wait_cap_ms") == 500, "cancel_wait_contract")
        snapshots = c.get("owner_snapshot")
        require(type(snapshots) is list, "cancel_snapshot_type")
        if type(snapshots) is list:
            matches = [r for r in snapshots if type(r) is dict and r.get("event") == "owner_release" and
                       r.get("reason") == "cancelled" and r.get("intent_token") == "intent-3"]
            require(len(matches) == 1, "cancel_owner_row_count")
            cancel_row = matches[0] if len(matches) == 1 else None
            require(matches == c.get("owner_rows"), "cancel_snapshot_join")
        else:
            require(False, "cancel_owner_row_missing")
        if type(cancel_row) is dict:
            require(cancel_row.get("owner_id") == owner_id and cancel_row.get("verified") is True and
                    cancel_row.get("keys_down") == [] and cancel_row.get("buttons_down") == [],
                    "cancel_owner_release_verified")
            key_rows = cancel_row.get("key_release_brackets")
            require(type(key_rows) is list and len(key_rows) == 1, "cancel_key_row_count")
            if type(key_rows) is list and len(key_rows) == 1 and type(key_rows[0]) is dict:
                kr = key_rows[0]
                require(kr.get("intent_token") == "intent-3" and kr.get("keycode") == EXPECTED["keycodes"]["w"] and
                        is_int(kr.get("release_request_ns")) and is_int(kr.get("sync_return_ns")) and
                        kr.get("release_request_ns", 0) <= kr.get("sync_return_ns", 0) <= cancel_row.get("verified_ns", 0),
                        "cancel_key_row_contract")

    teardowns = [c for c in cases if type(c) is dict and c.get("event") == "teardown"]
    require(len(teardowns) == 3, "teardown_count")
    for index, case in enumerate(teardowns):
        receipt = case.get("receipt")
        require(type(receipt) is dict and receipt.get("event") == "owner_release" and
                receipt.get("verified") is True and receipt.get("keys_down") == [] and
                receipt.get("buttons_down") == [] and case.get("w_down_after") is False and
                case.get("a_down_after") is False, f"teardown_{index}_neutral")

    return errors


def run_self_test(raw_path):
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    base_errors = audit(raw)
    if base_errors:
        return {"status": "FAIL", "control_errors": base_errors, "mutations_rejected": 0, "mutations_total": 6}
    mutations = []
    def mutate(fn):
        item = copy.deepcopy(raw)
        fn(item)
        mutations.append(item)
    mutate(lambda x: x["explicit_calls"][0]["caller_receipt"].update(
        release_call_returned_ns=x["explicit_calls"][0]["owner_rows_appended"][0]["sync_return_ns"] - 1))
    mutate(lambda x: x["explicit_calls"][0].update(key_down_before=False))
    mutate(lambda x: x["cases"][4].update(rejected=False, receipt={"event": "input_release_transition"}))
    mutate(lambda x: x["cases"][7]["owner_rows"][0].update(intent_token="wrong-intent"))
    mutate(lambda x: x["cases"][7].update(owner_rows=[]))
    mutate(lambda x: x["explicit_calls"][1]["caller_receipt"].update(grants_input_authority=True))
    rejected = sum(bool(audit(item)) for item in mutations)
    return {"status": "PASS" if rejected == len(mutations) else "FAIL",
            "control_errors": [], "mutations_rejected": rejected, "mutations_total": len(mutations)}


def main(argv):
    if len(argv) >= 2 and argv[1] == "--self-test":
        raw_path = Path(argv[2]) if len(argv) > 2 else HERE / "construction" / "raw.json"
        report = run_self_test(raw_path)
        print(json.dumps(report, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    raw_path = Path(os.environ.get("RAW_PATH", "/audit-input/raw.json"))
    out = Path(os.environ.get("AUDIT_OUT", "/audit-output/audit.json"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = audit(raw)
    report = {"schema": "owner-keyup-wslc-audit-v1", "allocation_id": ALLOC,
              "status": "PASS_OWNER_THREAD_KEYUP_BRACKET_WSLc_SCOPED" if not errors else "STOP_AUDIT_MISMATCH",
              "errors": errors, "explicit_keyup_rows": 3,
              "verified_teardowns": 3, "authority_granted": False,
              "scope": "private Xvfb / WSLc only; XSync server bracket, not physical or application effect"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
