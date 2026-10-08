"""Read-only independent checks for the paired wait-order trace."""
import hashlib
import json
from pathlib import Path
from .candidate import FREEZE, verify_freeze

HERE = Path(__file__).resolve().parent


def validate(result, raw):
    verify_freeze()
    if (result.get("schema") != "issue59-v39-ack-observation-order-result-a01" or
            result.get("main_commit") != FREEZE["main_commit"]):
        raise ValueError("result identity mismatch")
    cases = result.get("cases")
    if not isinstance(cases, list) or [case.get("case") for case in cases] != [
            "typed_before_ack", "ack_before_typed"]:
        raise ValueError("case set mismatch")
    if raw != result.get("events") or raw != [event for case in cases for event in case["events"]]:
        raise ValueError("raw event stream mismatch")
    before, after = cases
    if (before.get("monitor_calls") != 0 or before.get("first_ack_event") != "accepted" or
            before.get("following_wait_event") != "terminal"):
        raise ValueError("typed-before-ack case mismatch")
    if (after.get("monitor_calls") != 1 or after.get("first_ack_event") != "accepted" or
            after.get("following_wait_event") != "running_action_invalidation"):
        raise ValueError("ack-before-typed case mismatch")
    dropped = [event for event in before["events"] if event["event"] == "production_wait_dequeued"]
    delivered = [event for event in after["events"] if event["event"] == "monitor_observe"]
    if [event.get("row_event") for event in dropped] != ["typed_observation", "accepted", "terminal"]:
        raise ValueError("typed-before-ack dequeue trace mismatch")
    if len(delivered) != 1 or delivered[0].get("health") != 70:
        raise ValueError("ack-before-typed monitor trace mismatch")
    return True


def main():
    result_path, events_path = HERE / "RESULT.json", HERE / "events.jsonl"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate(result, raw)
    audit = {"schema": "issue59-v39-ack-observation-order-audit-v1",
             "status": "PASS_ACK_ORDER_SENSITIVE",
             "frozen_main": FREEZE["main_commit"], "event_rows": len(raw),
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
             "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
             "checks": {"same_production_wait_helper_both_cases": True,
                        "typed_before_ack_dropped_unmonitored": True,
                        "ack_before_typed_delivered_to_monitor": True,
                        "real_executor_or_input_not_claimed": True}}
    path = HERE / "AUDIT.json"
    if path.exists():
        raise FileExistsError("refusing to overwrite retained audit")
    path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
