"""Revision 3: distinguish parsed JSON witness types, retaining v1/v2."""
import json
from repair_v2.teardown_audit import audit as previous_audit


def _signature(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def audit(raw):
    errors = previous_audit(raw)
    if errors:
        return errors
    try:
        for case in raw["cases"]:
            if case["event"] != "teardown":
                continue
            projection = {key: value for key, value in case["receipt"].items()
                          if key not in {"release_call_started_ns", "release_call_returned_ns"}}
            signature = _signature(projection)
            if sum(_signature(row) == signature for row in raw["owner_snapshots_final"]) != 1:
                errors.append("teardown_final_json_mismatch:" + case["case"])
            if case["case"] in ("single", "two_key") and _signature(case.get("owner_rows_appended")) != _signature([projection]):
                errors.append("teardown_appended_json_mismatch:" + case["case"])
    except (TypeError, ValueError):
        errors.append("teardown_witness_not_json")
    return sorted(set(errors))
