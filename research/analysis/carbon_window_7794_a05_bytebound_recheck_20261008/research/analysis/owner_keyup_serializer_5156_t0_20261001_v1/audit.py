import json
import sys
from pathlib import Path


def audit_rows(inputs, rows):
    errors = []
    if not isinstance(inputs, list) or not isinstance(rows, list) or len(inputs) != 3 or len(rows) != 3:
        return ["expected exactly three input/output rows"]
    wanted_cases = ["single_explicit", "two_key_explicit", "two_key_explicit"]
    wanted_keys = ["a", "a", "b"]
    for index, (item, row) in enumerate(zip(inputs, rows)):
        source = item.get("owner_row", {})
        caller = item.get("caller_context", {})
        if row.get("event") != "joined_release":
            errors.append(f"row {index}: joined event missing")
        if row.get("owner_event") != "owner_key_release_bracket":
            errors.append(f"row {index}: source event provenance missing")
        for key, value in source.items():
            if key != "event" and row.get(key) != value:
                errors.append(f"row {index}: owner field changed: {key}")
        for key, value in caller.items():
            if row.get(key) != value:
                errors.append(f"row {index}: caller field changed: {key}")
        if row.get("case") != wanted_cases[index] or row.get("key") != wanted_keys[index]:
            errors.append(f"row {index}: release order/identity changed")
        if row.get("owner_id") != row.get("caller_owner_id"):
            errors.append(f"row {index}: owner identity mismatch")
        if row.get("intent_token") != row.get("caller_intent_token"):
            errors.append(f"row {index}: intent identity mismatch")
        times = [row.get(name) for name in (
            "caller_started_ns", "request_started_ns", "request_returned_ns",
            "shared_sync_returned_ns", "caller_returned_ns",
        )]
        if any(type(value) is not int for value in times) or times != sorted(times):
            errors.append(f"row {index}: bracket ordering invalid")
        if row.get("timing_valid") is not True:
            errors.append(f"row {index}: timing validity lost")
        if row.get("grants_input_authority") is not False or row.get("physical_key_up_claimed") is not False:
            errors.append(f"row {index}: authority/physical claim changed")
    return errors


def audit_files(input_path, raw_path):
    inputs = json.loads(Path(input_path).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(raw_path).read_text(encoding="utf-8").splitlines() if line]
    errors = audit_rows(inputs, rows)
    return {"decision": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT", "rows": len(rows), "errors": errors}


if __name__ == "__main__":
    report = audit_files(sys.argv[1], sys.argv[2])
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if not report["errors"] else 1)
