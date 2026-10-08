"""Direct raw witnesses; imports neither validators, candidate nor mutation code."""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ["retained_control", "candidate_window_excludes_events", "admission_after_explicit_release",
         "two_key_temporal_order_reversed", "teardown_foreign_owner", "teardown_foreign_intent",
         "cancel_release_before_admission_ack", "external_counter_boolean", "model_counter_float",
         "existing_keymap_negative", "existing_bracket_negative"]


def violated(name, r):
    calls, events = r["explicit_calls"], r["cases"]
    if name == "candidate_window_excludes_events":
        return r["candidate_started_ns"] > events[0]["receipt"]["admitted_ns"]
    if name == "admission_after_explicit_release":
        return events[0]["receipt"]["input_ack_ns"] > calls[0]["caller_receipt"]["release_call_started_ns"]
    if name == "two_key_temporal_order_reversed":
        return calls[1]["caller_receipt"]["release_call_returned_ns"] > calls[2]["caller_receipt"]["release_call_started_ns"]
    if name == "teardown_foreign_owner":
        return events[1]["receipt"]["owner_id"] != r["owner_id"]
    if name == "teardown_foreign_intent":
        return events[1]["receipt"]["intent_token"] != events[0]["intent_token"]
    if name == "cancel_release_before_admission_ack":
        return events[7]["owner_rows"][0]["key_release_brackets"][0]["release_request_ns"] < events[6]["receipt"]["input_ack_ns"]
    if name == "external_counter_boolean":
        return type(r["external_effects"]) is bool
    if name == "model_counter_float":
        return type(r["model_calls"]) is float
    if name == "existing_keymap_negative":
        return calls[0]["key_down_before"] is False
    if name == "existing_bracket_negative":
        return calls[0]["caller_receipt"]["release_call_returned_ns"] < calls[0]["owner_rows_appended"][0]["sync_return_ns"]
    if name == "retained_control":
        return False
    raise ValueError(name)


def main():
    out = Path(sys.argv[1])
    report = json.loads((out / "candidate.json").read_text())
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    errors = []
    if report["run_id"] != freeze["run_id"] or report["pid"] == os.getpid():
        errors.append("identity/process boundary")
    if [r["case"] for r in report["rows"]] != NAMES:
        errors.append("case census")
    original = json.loads((HERE / "retained/raw.json").read_text())
    for row in report["rows"]:
        data = (out / row["raw_file"]).read_bytes()
        raw = json.loads(data)
        invalid = violated(row["case"], raw)
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            errors.append("hash:" + row["case"])
        if invalid != row["invalid"] or bool(row["supplemental_errors"]) != invalid:
            errors.append("oracle:" + row["case"])
        if row["case"] == "retained_control" and (raw != original or row["legacy_errors"]):
            errors.append("retained control changed/rejected")
    result = {"status": "PASS_RAW_WITNESS_AUDIT_SCOPED" if not errors else "FAIL",
              "run_id": freeze["run_id"], "pid": os.getpid(), "errors": errors,
              "rows": len(report["rows"]), "legacy_false_accepts": sum(r["invalid"] and not r["legacy_errors"] for r in report["rows"]),
              "scope": "independent mutation witnesses/hash checks; no backend authenticity or efficacy claim"}
    with (out / "independent-audit.json").open("x") as f:
        f.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
