"""Paired queue-order test using the exact frozen V39 wait helper."""
import json
from pathlib import Path

from ..v39_ready_to_submit_queue_race_a03_20261008.candidate import (
    FREEZE as SOURCE_FREEZE, source_anchors, pinned_source,
    build_exact_wait, RecordingQueue, FakeProcess)

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def verify_freeze():
    if FREEZE["main_commit"] != SOURCE_FREEZE["main_commit"]:
        raise ValueError("paired study and source-slice freeze differ")
    spec = FREEZE["source"]
    if spec != SOURCE_FREEZE["source"]:
        raise ValueError("paired study source identity differs")
    return source_anchors(pinned_source())


class Monitor:
    event_types = {"typed_observation"}

    def __init__(self, events):
        self.events = events
        self.calls = 0

    def observe(self, row):
        self.calls += 1
        self.events.append({"event": "monitor_observe", "sequence": row["sequence"],
                            "health": row["signals"]["health"]["value"]})
        return {"event": "running_action_invalidation", "reason": "health:below_hard_minimum",
                "grants_input_authority": False}


def run_case(name, typed_first):
    events = [{"event": "case_start", "case": name,
               "order": "typed_before_ack" if typed_first else "ack_before_typed"}]
    incoming = RecordingQueue(events)
    observation = {"event": "typed_observation", "sequence": 2,
                   "signals": {"health": {"value": 70}}}
    accepted = {"event": "accepted", "id": "action-0", "accepted_ns": 1}
    terminal = {"event": "terminal", "id": "action-0", "status": "completed"}
    for row in ((observation, accepted, terminal) if typed_first else (accepted,)):
        incoming.put(row)
    anchors = source_anchors(pinned_source())
    wait, _latest = build_exact_wait(anchors["production_wait"], incoming, FakeProcess())
    monitor = Monitor(events)
    ack = wait(lambda row: row["event"] in ("accepted", "rejected"), timeout=1)
    events.append({"event": "ack_returned", "event_type": ack["event"],
                   "monitor_calls": monitor.calls, "queue_depth": incoming.qsize()})
    if not typed_first:
        incoming.put(observation)
        incoming.put(terminal)
    outcome = wait(lambda row: row["event"] == "terminal", timeout=1,
                   observation_monitor=monitor)
    events.append({"event": "monitored_wait_returned", "event_type": outcome["event"],
                   "monitor_calls": monitor.calls, "queue_depth": incoming.qsize()})
    return {"case": name, "monitor_calls": monitor.calls,
            "first_ack_event": ack["event"], "following_wait_event": outcome["event"],
            "events": events}


def run_once():
    verify_freeze()
    cases = [run_case("typed_before_ack", True), run_case("ack_before_typed", False)]
    flattened = [event for case in cases for event in case["events"]]
    return {"schema": "issue59-v39-ack-observation-order-result-a01",
            "status": "CONSTRUCTION_OBSERVATION",
            "main_commit": FREEZE["main_commit"], "cases": cases,
            "events": flattened,
            "scope": "Two deterministic queue orderings through the exact frozen production wait helper; fake acceptance only, no executor binary or input."}


def main():
    result_path = HERE / "RESULT.json"
    events_path = HERE / "events.jsonl"
    if result_path.exists() or events_path.exists():
        raise FileExistsError("refusing to overwrite retained candidate output")
    result = run_once()
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                           newline="\n")
    events_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n"
                                   for row in result["events"]),
                           encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "case_count": len(result["cases"]),
                      "event_count": len(result["events"])}, separators=(",", ":")))


if __name__ == "__main__":
    main()
