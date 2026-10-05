"""Additive A18 checks; the historical auditor and raw remain immutable."""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("retained_a18", Path(__file__).parent / "retained" / "audit.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def audit(raw):
    try:
        errors = legacy.audit(raw)
    except (TypeError, ValueError, KeyError, IndexError) as exc:
        return ["legacy_schema_exception:" + type(exc).__name__]
    if errors:
        return errors

    for key in ("external_effects", "model_calls"):
        if type(raw[key]) is not int or raw[key] != 0:
            errors.append("activity_counter_type:" + key)

    measured_fields = {"admitted_ns", "input_ack_ns", "release_call_started_ns",
                       "release_call_returned_ns", "release_request_ns", "sync_return_ns",
                       "verified_ns", "requested_ns", "receipt_wait_started_ns",
                       "receipt_wait_finished_ns"}
    def inspect(value):
        if type(value) is dict:
            for key, item in value.items():
                if key in measured_fields and (type(item) is not int or not
                        raw["candidate_started_ns"] <= item <= raw["candidate_finished_ns"]):
                    errors.append("event_outside_candidate_window:" + key)
                inspect(item)
        elif type(value) is list:
            for item in value:
                inspect(item)
    inspect(raw)

    admissions = {(c["intent_token"], c["key"]): c["receipt"] for c in raw["cases"]
                  if c["event"] == "admission"}
    for call in raw["explicit_calls"]:
        ack = admissions[(call["intent_token"], call["key"])]["input_ack_ns"]
        if ack > call["caller_receipt"]["release_call_started_ns"]:
            errors.append("release_precedes_admission_ack:" + call["case"])
    for left, right in zip(raw["explicit_calls"], raw["explicit_calls"][1:]):
        if left["caller_receipt"]["release_call_returned_ns"] > right["caller_receipt"]["release_call_started_ns"]:
            errors.append("explicit_calls_not_serial")

    for c in raw["cases"]:
        if c["event"] == "teardown":
            if c["receipt"]["owner_id"] != raw["owner_id"]:
                errors.append("teardown_foreign_owner")
            expected_intent = {"single": "intent-1", "two_key": "intent-2", "cancel": None}.get(c["case"], "INVALID")
            if c["receipt"]["intent_token"] != expected_intent:
                errors.append("teardown_foreign_intent")
        elif c["event"] == "cancel_cleanup":
            ack = admissions[("intent-3", "w")]["input_ack_ns"]
            for row in c["owner_rows"]:
                for bracket in row["key_release_brackets"]:
                    if bracket["release_request_ns"] < ack:
                        errors.append("cancel_release_precedes_admission_ack")
    return sorted(set(errors))
