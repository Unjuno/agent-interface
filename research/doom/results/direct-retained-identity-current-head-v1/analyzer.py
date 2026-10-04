"""Gate MAP01 logs on direct, bounded retained-input observability."""
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path


def load_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def analyze(events):
    pending = defaultdict(deque)
    holds = []
    invalid_releases = []
    invalid_admissions = []
    for row in events:
        event = row.get("event")
        if event == "input_admission":
            key = row.get("key")
            token = row.get("intent_token")
            if type(key) is not str or not key or type(token) is not str or not token:
                invalid_admissions.append(row)
                continue
            pending[(token, key)].append(row)
        elif event == "input_release_transition" and row.get("operation") == "up":
            token = row.get("intent_token")
            key = row.get("key")
            if type(key) is not str or not key or type(token) is not str or not token:
                invalid_releases.append(row)
                continue
            queue = pending[(token, key)]
            if not queue or row.get("owner_transition_verified") is not True:
                invalid_releases.append(row)
                continue
            start = queue.popleft()
            required = ("admitted_ns", "input_ack_ns")
            release_required = ("release_call_started_ns", "release_call_returned_ns")
            if any(type(start.get(k)) is not int for k in required) or any(type(row.get(k)) is not int for k in release_required):
                invalid_releases.append(row)
                continue
            admitted_ns, input_ack_ns = start["admitted_ns"], start["input_ack_ns"]
            release_start_ns = row["release_call_started_ns"]
            release_return_ns = row["release_call_returned_ns"]
            if not admitted_ns <= input_ack_ns <= release_start_ns <= release_return_ns:
                invalid_releases.append(row)
                continue
            lower_ns = release_start_ns - input_ack_ns
            upper_ns = release_return_ns - admitted_ns
            holds.append({"intent_token": token, "key": key,
                          "retained_lower_ms": lower_ns / 1e6,
                          "retained_upper_ms": upper_ns / 1e6,
                          "censor_width_ms": (upper_ns - lower_ns) / 1e6,
                          "source_events": ["input_admission", "input_release_transition"]})
    unmatched = [dict(row) for queue in pending.values() for row in queue]
    measurement_ready = bool(holds) and not unmatched and not invalid_releases and not invalid_admissions
    return {"schema": "map01-direct-retained-input-v1",
            "measurement_ready": measurement_ready,
            "hold_count": len(holds), "unmatched_admission_count": len(unmatched),
            "invalid_release_count": len(invalid_releases),
            "invalid_admission_count": len(invalid_admissions), "holds": holds,
            "decision": ("PASS: direct bounded release evidence available" if measurement_ready else
                         "FAIL: retained-input duration is not identifiable from this trace")}


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
