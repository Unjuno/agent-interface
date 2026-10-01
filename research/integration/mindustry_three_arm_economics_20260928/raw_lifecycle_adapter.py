"""Join private game-channel lifecycle evidence to raw task event records."""

from __future__ import annotations

import copy

from raw_allocation_audit_v2 import ARMS, TASKS, RawAuditError


def attach_private_lifecycle(raw: object, arm: str, evidence: object) -> dict:
    """Return a copy of v2 raw events with one arm's private receipts attached.

    Task start and score timestamps in ``raw`` must already use the same host
    monotonic clock as ``PrivateBenchmarkChannel``. No timestamps are repaired
    or synthesized here; mismatched/incomplete inputs fail closed.
    """
    if type(raw) is not dict or raw.get("schema") != "mindustry_three_arm_raw_events_v2":
        raise RawAuditError("v2 raw event object required")
    if (arm not in ARMS or type(raw.get("arms")) is not dict
            or type(raw.get("transition_events")) is not list):
        raise RawAuditError("frozen raw arm required")
    if type(evidence) is not dict or set(evidence) != {
            "task_started_ns", "score_checked_ns", "reset_events",
            "transition_events"}:
        raise RawAuditError("exact private lifecycle evidence required")

    starts = evidence["task_started_ns"]
    scores = evidence["score_checked_ns"]
    resets = evidence["reset_events"]
    transitions = evidence["transition_events"]
    if (type(starts) is not dict or set(starts) != set(range(1, 7))
            or type(scores) is not dict or set(scores) != set(TASKS)
            or type(resets) is not dict or set(resets) != set(TASKS)
            or type(transitions) is not list or len(transitions) != 1):
        raise RawAuditError("all six task starts/scores/resets and one transition required")
    rows = raw["arms"].get(arm)
    if type(rows) is not list or len(rows) != len(TASKS):
        raise RawAuditError("six raw task rows required for target arm")

    result = copy.deepcopy(raw)
    for index, task_id in enumerate(TASKS):
        row = result["arms"][arm][index]
        start, score = starts[index + 1], scores[task_id]
        if (type(start) is not int or type(score) is not int
                or type(row) is not dict or type(row.get("score_event")) is not dict
                or type(row.get("ended_ns")) is not int or row["ended_ns"] <= start):
            raise RawAuditError("private start/score timestamps must bind raw task interval")
        reset = resets[task_id]
        if type(reset) is not dict or set(reset) != {
                "request_ns", "witness_ns", "receipt_id", "before", "after"}:
            raise RawAuditError("exact private reset event required for each task")
        row["started_ns"] = start
        row["score_event"]["checked_ns"] = score
        row["reset_event"] = copy.deepcopy(reset)

    event = transitions[0]
    if type(event) is not dict or event.get("arm") != arm:
        raise RawAuditError("geometry receipt arm differs from attachment target")
    result["transition_events"] = [
        row for row in result.get("transition_events", []) if row.get("arm") != arm]
    result["transition_events"].append(copy.deepcopy(event))
    return result
