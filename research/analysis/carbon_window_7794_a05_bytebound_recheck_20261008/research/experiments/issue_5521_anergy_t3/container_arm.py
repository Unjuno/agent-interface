#!/usr/bin/env python3
"""Run exactly one preregistered expiry policy arm for container isolation."""
import argparse
import hashlib
import json

import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("policy", choices=("clear", "tombstone"))
    args = parser.parse_args()
    schedule = json.dumps(run.EVENTS, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps({
        "type": "freeze",
        "policy": args.policy,
        "schedule_sha256": hashlib.sha256(schedule).hexdigest(),
        "events": run.EVENTS,
    }, sort_keys=True))
    state, segment, segment_id = {}, [], 0
    rows = []
    for event in run.EVENTS:
        if event["op"] == "restart":
            result = run.invoke_worker(args.policy, state, segment, segment_id)
            rows.extend(result["rows"])
            state = json.loads(json.dumps(result["state"], sort_keys=True))
            rows.append({"type": "process_exit", "policy": args.policy, "segment": segment_id,
                         "pid": result["pid"], "exit_code": 0, "state_sha256": result["state_sha256"]})
            rows.append({"type": "state_snapshot", "policy": args.policy, "segment": segment_id,
                         "state": state, "state_sha256": run.state_digest(state)})
            rows.append({"type": "restart", "policy": args.policy, "tick": event["tick"],
                         "restored_state_sha256": run.state_digest(state), "restored_entries": len(state)})
            segment_id += 1
            segment = []
        else:
            segment.append(event)
    result = run.invoke_worker(args.policy, state, segment, segment_id)
    rows.extend(result["rows"])
    state = json.loads(json.dumps(result["state"], sort_keys=True))
    rows.append({"type": "process_exit", "policy": args.policy, "segment": segment_id,
                 "pid": result["pid"], "exit_code": 0, "state_sha256": result["state_sha256"]})
    rows.append({"type": "state_snapshot", "policy": args.policy, "segment": segment_id,
                 "state": state, "state_sha256": run.state_digest(state)})
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    print(json.dumps({
        "type": "summary",
        "policy": args.policy,
        "verifier_checks": sum(r.get("verifier_check") is True for r in rows),
        "admitted_effects": sum(r.get("effect") is True for r in rows),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
