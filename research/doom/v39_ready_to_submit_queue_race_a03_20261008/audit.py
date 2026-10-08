"""Independent read-only validation of the exact production wait trace."""
import hashlib
import json
from pathlib import Path
from .candidate import FREEZE, source_anchors, pinned_source

HERE = Path(__file__).resolve().parent


def validate(result, raw):
    anchors = source_anchors(pinned_source())
    expected = {key: value for key, value in anchors.items() if key != "production_wait"}
    if (result.get("schema") != "issue59-v39-ready-submit-result-a03" or
            result.get("frozen_main") != FREEZE["main_commit"] or
            result.get("anchors") != expected):
        raise ValueError("source identity or caller anchors mismatch")
    if raw != result.get("events"):
        raise ValueError("raw event stream mismatch")
    names = [row.get("event") for row in raw]
    required = ["action_readiness", "typed_observation_queued", "submit_written",
                "production_wait_dequeued", "production_wait_dequeued",
                "acceptance_returned", "monitor_call_count_after_ack", "queued_rows_after_ack",
                "legacy_latest_after_ack"]
    if names != required:
        raise ValueError("event ordering mismatch")
    if ([raw[3].get("row_event"), raw[4].get("row_event")] !=
            ["typed_observation", "accepted"] or raw[5].get("id") != "action-0"):
        raise ValueError("acknowledgement wait did not consume expected rows")
    if raw[6].get("count") != 0 or raw[7].get("count") != 0 or raw[8].get("value") is not None:
        raise ValueError("typed observation was retained, monitored, or became latest")
    if raw[2].get("input_emission") != "NOT_MODELED":
        raise ValueError("result overclaims executor input")
    return True


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    validate(result, raw)
    audit = {"schema": "issue59-v39-ready-submit-audit-v1",
             "status": "PASS_TYPED_OBSERVATION_DROPPED_AT_ACK",
             "frozen_main": FREEZE["main_commit"], "event_rows": len(raw),
             "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
             "events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
             "checks": {"frozen_source_identity": True,
                        "acceptance_wait_unmonitored": True,
                        "exact_wait_consumed_typed_row": True,
                        "typed_row_not_retained_for_later_monitor": True,
                        "executor_acceptance_and_input_not_claimed": True}}
    path = HERE / "AUDIT.json"
    if path.exists():
        raise FileExistsError("refusing to overwrite retained audit")
    path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
