"""Raw JSONL-only auditor for owner key-release request brackets."""
import json
import sys


def audit(records):
    failures = []
    for index, record in enumerate(records):
        if record.get("event") != "owner_key_release_bracket":
            continue
        prefix = f"record[{index}]"
        required = ("owner_id", "intent_token", "keycode", "request_started_ns",
                    "request_returned_ns", "shared_sync_returned_ns", "caller_started_ns",
                    "caller_returned_ns", "timing_valid", "grants_input_authority",
                    "physical_key_up_claimed")
        missing = [key for key in required if key not in record]
        if missing:
            failures.append(f"{prefix}: missing {','.join(missing)}")
            continue
        if not isinstance(record["owner_id"], str) or not record["owner_id"]:
            failures.append(f"{prefix}: invalid owner_id")
        if not isinstance(record["intent_token"], str) or not record["intent_token"]:
            failures.append(f"{prefix}: invalid intent_token")
        times = [record[name] for name in ("caller_started_ns", "request_started_ns",
                                            "request_returned_ns", "shared_sync_returned_ns",
                                            "caller_returned_ns")]
        if any(type(value) is not int for value in times):
            failures.append(f"{prefix}: timestamps must be integers")
        elif not all(left <= right for left, right in zip(times, times[1:])):
            failures.append(f"{prefix}: bracket ordering invalid")
        if record["timing_valid"] is not True:
            failures.append(f"{prefix}: timing_valid must be true")
        if record["grants_input_authority"] is not False:
            failures.append(f"{prefix}: authority claim must be false")
        if record["physical_key_up_claimed"] is not False:
            failures.append(f"{prefix}: physical key-up claim must be false")
    return failures


def main(path):
    with open(path, encoding="utf-8") as source:
        records = [json.loads(line) for line in source if line.strip()]
    failures = audit(records)
    if failures:
        print("FAIL")
        print("\n".join(failures))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_owner_release_brackets.py RAW.jsonl")
    raise SystemExit(main(sys.argv[1]))
