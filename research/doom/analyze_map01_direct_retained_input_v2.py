"""Measure per-input retention from transitions carrying admission receipts."""
import argparse
import json
from collections import Counter
from pathlib import Path


def load_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _identity(event, row):
    if event == "input_admission":
        return "down", "key", row.get("key")
    if event == "pointer_admission" and row.get("operation") == "button_down":
        return "button_down", "payload", row.get("payload")
    return None


def _receipt_identity(receipt):
    event = receipt.get("event")
    identity = _identity(event, receipt)
    if identity is None:
        return None
    operation, field, value = identity
    valid_value = (
        type(value) is str and bool(value) if field == "key"
        else type(value) is int and value > 0
    )
    if receipt.get("operation") != operation or not valid_value:
        return None
    admitted_ns = receipt.get("admitted_ns")
    ack_ns = receipt.get("input_ack_ns")
    if type(admitted_ns) is not int or type(ack_ns) is not int:
        return None
    deadline = receipt.get("valid_until_ns")
    if type(deadline) is not int or not admitted_ns <= ack_ns < deadline:
        return None
    owner = receipt.get("owner_id")
    token = receipt.get("intent_token")
    if not isinstance(owner, str) or not owner or not isinstance(token, str) or not token:
        return None
    return (event, operation, field, value, owner, token, deadline, admitted_ns, ack_ns)


def _release_matches(receipt, release):
    identity = _receipt_identity(receipt)
    if identity is None:
        return None
    event, admission_operation, field, value, owner, token, deadline, admitted_ns, ack_ns = identity
    release_operation = "up" if admission_operation == "down" else "button_up"
    if (release.get("operation") != release_operation
            or release.get("key") != value
            or release.get("owner_id") != owner
            or release.get("intent_token") != token
            or release.get("valid_until_ns") != deadline):
        return None
    started_ns = release.get("release_call_started_ns")
    returned_ns = release.get("release_call_returned_ns")
    if (type(started_ns) is not int or type(returned_ns) is not int
            or not admitted_ns <= ack_ns < started_ns < deadline
            or returned_ns < started_ns):
        return None
    return {
        "input_kind": "key" if event == "input_admission" else "pointer_button",
        "key": value,
        "intent_token": token,
        "owner_id": owner,
        "admitted_ns": admitted_ns,
        "input_ack_ns": ack_ns,
        "release_call_started_ns": started_ns,
        "release_call_returned_ns": returned_ns,
        "retained_lower_ms": (started_ns - ack_ns) / 1e6,
        "retained_upper_ms": (returned_ns - admitted_ns) / 1e6,
        "censor_width_ms": ((returned_ns - admitted_ns) - (started_ns - ack_ns)) / 1e6,
        "source_events": [event, "input_release_transition"],
    }


def analyze(events):
    raw_admissions = Counter()
    malformed_admission_count = 0
    for row in events:
        event = row.get("event")
        if event not in ("input_admission", "pointer_admission"):
            continue
        identity = _identity(event, row)
        if identity is None:
            continue
        operation, field, value = identity
        marker = dict(row)
        marker["operation"] = operation
        key = _receipt_identity(marker)
        if key is not None:
            raw_admissions[key] += 1
        else:
            malformed_admission_count += 1

    ambiguous_admission_count = sum(count - 1 for count in raw_admissions.values() if count > 1)

    holds = []
    invalid_releases = []
    for row in events:
        if row.get("event") != "input_release_transition":
            continue
        receipt = row.get("admission_receipt")
        hold = (_release_matches(receipt, row) if isinstance(receipt, dict) else None)
        if (hold is None or row.get("admission_receipt_valid") is not True
                or row.get("owner_transition_verified") is not True
                or row.get("ordinary_release_candidate") is not True):
            invalid_releases.append(row)
            continue
        key = _receipt_identity(receipt)
        if raw_admissions[key] <= 0:
            invalid_releases.append(row)
            continue
        raw_admissions[key] -= 1
        holds.append(hold)

    unmatched = sum(raw_admissions.values())
    ready = (bool(holds) and unmatched == 0 and not invalid_releases
             and malformed_admission_count == 0 and ambiguous_admission_count == 0)
    return {
        "schema": "map01-direct-retained-input-v2",
        "measurement_ready": ready,
        "hold_count": len(holds),
        "unmatched_admission_count": unmatched,
        "malformed_admission_count": malformed_admission_count,
        "ambiguous_admission_count": ambiguous_admission_count,
        "invalid_release_count": len(invalid_releases),
        "holds": holds,
        "decision": ("PASS: direct receipt-linked release evidence available" if ready else
                     "FAIL: admission receipts do not form a complete verified release trace"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("events", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(load_events(args.events))
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
