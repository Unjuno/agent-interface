#!/usr/bin/env python3
"""Deterministic finite-history construction for issue #5360 T1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PATTERNS = (
    "clean_commit",
    "read_then_abort",
    "delayed_completion",
    "mixed_generation",
    "supersession",
    "rollback_after_read",
    "duplicate_completion",
    "tentative_presentation",
)
ROLES = ("action_consumed", "presentation_only")
POLICIES = ("FINAL_STATE_ONLY", "ACTION_RELEVANT_OPACITY")


def make_history(pattern: str, role: str) -> dict:
    """Build ordered events; validity metadata is derived from those events."""
    events = []

    def emit(event_type: str, **fields) -> None:
        events.append({"seq": len(events) + 1, "type": event_type, **fields})

    read_generation = 1
    action_epoch = 2 if pattern in {"mixed_generation", "supersession"} else 1
    emit("begin", tx="read-tx", generation=read_generation)
    emit("read", id="r1", generation=read_generation, producer_status="tentative")

    def use_read() -> None:
        consumes = role == "action_consumed"
        emit("consume" if consumes else "present_only", read_id="r1",
             action_id="a1" if consumes else None,
             action_epoch=action_epoch if consumes else None)

    if pattern == "clean_commit":
        emit("commit", tx="read-tx")
        use_read()
    elif pattern == "read_then_abort":
        emit("abort", tx="read-tx")
        use_read()
    elif pattern == "delayed_completion":
        use_read()
        emit("commit", tx="read-tx", completion="delayed")
    elif pattern == "mixed_generation":
        emit("commit", tx="read-tx")
        use_read()
    elif pattern == "supersession":
        emit("commit", tx="read-tx")
        emit("supersede", old_generation=1, new_generation=2)
        use_read()
    elif pattern == "rollback_after_read":
        emit("commit", tx="read-tx")
        use_read()
        emit("rollback", tx="read-tx", rollback_scope="read-owner")
    elif pattern == "duplicate_completion":
        emit("commit", tx="read-tx")
        emit("completion_duplicate", tx="read-tx")
        use_read()
    elif pattern == "tentative_presentation":
        emit("present", read_id="r1")
        use_read()

    return {"pattern": pattern, "role": role, "events": events}


def derive(events: list[dict]) -> dict:
    """Producer-side projection from chronology; independent audit re-derives it."""
    read = next(e for e in events if e["type"] == "read")
    consumers = [e for e in events if e["type"] in {"consume", "present_only"}]
    consumer = consumers[0]
    state = "tentative"
    current_generation = read["generation"]
    status_at_consume = None
    invalidating_event = None
    for event in events:
        if event["type"] in {"commit", "abort", "rollback"}:
            state = {"commit": "committed", "abort": "aborted",
                     "rollback": "rolled_back"}[event["type"]]
        elif event["type"] == "supersede":
            current_generation = event["new_generation"]
        if event is consumer:
            status_at_consume = state
    action = consumer["type"] == "consume"
    reason = None
    if action:
        earlier = [e for e in events if e["seq"] < consumer["seq"]]
        later = [e for e in events if e["seq"] > consumer["seq"]]
        before_abort = next((e for e in earlier if e["type"] == "abort"), None)
        before_rollback = next((e for e in earlier if e["type"] == "rollback"), None)
        after_abort = next((e for e in later if e["type"] == "abort"), None)
        after_rollback = next((e for e in later if e["type"] == "rollback"), None)
        if before_abort:
            reason = "aborted_before_consume"
        elif before_rollback:
            reason = "rolled_back_before_consume"
        elif status_at_consume != "committed":
            reason = "not_committed_at_consume"
        elif after_abort:
            reason = "aborted_after_consume"
        elif after_rollback:
            reason = "rolled_back_after_consume"
        elif read["generation"] != consumer["action_epoch"] or any(
                e["type"] == "supersede" and e["old_generation"] == read["generation"]
                and e["seq"] < consumer["seq"] for e in earlier):
            reason = "generation_mismatch"
    return {
        "action_attempted": action,
        "action_epoch": consumer.get("action_epoch"),
        "final_generation": current_generation,
        "oracle_invalid_reason": reason,
        "read_provenance": {
            "read_id": read["id"],
            "source_generation": read["generation"],
            "producer_final_status": state,
            "consume_seq": consumer["seq"],
            "action_relevant": action,
            "consumer_action": consumer.get("action_id"),
        },
    }


def decide(row: dict, policy: str) -> dict:
    if not row["action_attempted"]:
        return {"accepted": False, "reason": "no_action_attempt", "first_invalid_read": None}
    reason = row["oracle_invalid_reason"]
    if policy == "FINAL_STATE_ONLY":
        # Deliberately weak comparator: only the final generation is checked.
        accepted = row["action_epoch"] == row["final_generation"]
        return {"accepted": accepted, "reason": "final_generation_match" if accepted else "final_generation_mismatch",
                "first_invalid_read": None}
    return {"accepted": reason is None, "reason": "valid" if reason is None else reason,
            "first_invalid_read": None if reason is None else "r1"}


def run() -> dict:
    rows = []
    for pattern in PATTERNS:
        for role in ROLES:
            history = make_history(pattern, role)
            history.update(derive(history["events"]))
            for policy in POLICIES:
                decision = decide(history, policy)
                rows.append({**history, "policy": policy, "decision": decision})
    return {"schema": "opacity-action-relevance-5360-t1/v1", "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite raw output: {args.output}")
    args.output.write_text(json.dumps(run(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
