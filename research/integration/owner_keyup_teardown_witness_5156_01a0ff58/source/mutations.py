"""One-factor corruptions of immutable A18 raw; no X11 or input operations."""
import copy


def cases(raw):
    yield "retained_control", copy.deepcopy(raw), False
    item = copy.deepcopy(raw)
    item["candidate_started_ns"] = raw["candidate_finished_ns"] + 1
    item["candidate_finished_ns"] = raw["candidate_finished_ns"] + 2
    yield "candidate_window_excludes_events", item, True

    item = copy.deepcopy(raw)
    receipt = item["cases"][0]["receipt"]
    stamp = item["explicit_calls"][0]["caller_receipt"]["release_call_returned_ns"] + 1
    receipt.update(admitted_ns=stamp, input_ack_ns=stamp + 1)
    yield "admission_after_explicit_release", item, True

    item = copy.deepcopy(raw)
    call = item["explicit_calls"][1]
    old_row = copy.deepcopy(call["owner_rows_appended"][0])
    delta = item["explicit_calls"][2]["caller_receipt"]["release_call_returned_ns"] - call["caller_receipt"]["release_call_started_ns"] + 1
    for k in ("release_call_started_ns", "release_call_returned_ns"):
        call["caller_receipt"][k] += delta
    for row in [call["owner_rows_appended"][0]] + [r for r in item["owner_snapshots_final"] if r == old_row]:
        for k in ("release_request_ns", "sync_return_ns"):
            row[k] += delta
    yield "two_key_temporal_order_reversed", item, True

    item = copy.deepcopy(raw)
    item["cases"][1]["receipt"]["owner_id"] = "f" * 32
    yield "teardown_foreign_owner", item, True

    item = copy.deepcopy(raw)
    item["cases"][1]["receipt"]["intent_token"] = "intent-foreign"
    yield "teardown_foreign_intent", item, True

    item = copy.deepcopy(raw)
    ack = item["cases"][6]["receipt"]["input_ack_ns"]
    for row in item["cases"][7]["owner_rows"] + item["cases"][7]["owner_snapshot"]:
        if row.get("event") == "owner_release" and row.get("reason") == "cancelled" and row.get("intent_token") == "intent-3":
            row["key_release_brackets"][0].update(release_request_ns=ack - 2, sync_return_ns=ack - 1)
    yield "cancel_release_before_admission_ack", item, True

    item = copy.deepcopy(raw)
    item["external_effects"] = False
    yield "external_counter_boolean", item, True

    item = copy.deepcopy(raw)
    item["model_calls"] = 0.0
    yield "model_counter_float", item, True

    item = copy.deepcopy(raw)
    item["explicit_calls"][0]["key_down_before"] = False
    yield "existing_keymap_negative", item, True

    item = copy.deepcopy(raw)
    item["explicit_calls"][0]["caller_receipt"]["release_call_returned_ns"] = item["explicit_calls"][0]["owner_rows_appended"][0]["sync_return_ns"] - 1
    yield "existing_bracket_negative", item, True
