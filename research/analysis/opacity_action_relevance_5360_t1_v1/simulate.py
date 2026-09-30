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
    """Build an explicit event trace and the read's consume-time validity."""
    generation = 2 if pattern == "mixed_generation" else 1
    status = "tentative"
    events = [{"seq": 1, "type": "begin", "tx": "read-tx", "generation": generation}]
    events.append({"seq": 2, "type": "read", "id": "r1", "generation": generation,
                   "producer_status": status})
    if pattern == "clean_commit":
        status = "committed"
        events.append({"seq": 3, "type": "commit", "tx": "read-tx"})
    elif pattern == "read_then_abort":
        status = "aborted"
        events.append({"seq": 3, "type": "abort", "tx": "read-tx"})
    elif pattern == "delayed_completion":
        status = "committed"
        events.append({"seq": 3, "type": "commit", "tx": "read-tx", "after_consume": True})
    elif pattern == "mixed_generation":
        status = "committed"
        events.append({"seq": 3, "type": "commit", "tx": "read-tx"})
    elif pattern == "supersession":
        status = "committed"
        events.extend(({"seq": 3, "type": "commit", "tx": "read-tx"},
                       {"seq": 4, "type": "supersede", "old_generation": 1,
                        "new_generation": 2}))
    elif pattern == "rollback_after_read":
        status = "rolled_back"
        events.append({"seq": 3, "type": "rollback", "tx": "read-tx"})
    elif pattern == "duplicate_completion":
        status = "committed"
        events.extend(({"seq": 3, "type": "commit", "tx": "read-tx"},
                       {"seq": 4, "type": "commit", "tx": "read-tx", "duplicate": True}))
    elif pattern == "tentative_presentation":
        events.append({"seq": 3, "type": "present", "read_id": "r1"})

    action_epoch = 1
    consume_seq = 4
    consumes = role == "action_consumed"
    events.append({"seq": consume_seq, "type": "consume" if consumes else "present_only",
                   "read_id": "r1", "action_id": "a1" if consumes else None,
                   "action_epoch": action_epoch if consumes else None})

    invalid_reason = None
    if consumes:
        if pattern in ("read_then_abort", "rollback_after_read"):
            invalid_reason = status
        elif pattern == "delayed_completion":
            invalid_reason = "not_committed_at_consume"
        elif generation != action_epoch:
            invalid_reason = "generation_mismatch"
        elif pattern == "tentative_presentation":
            invalid_reason = "not_committed_at_consume"

    return {
        "pattern": pattern,
        "role": role,
        "events": events,
        "read_provenance": {"read_id": "r1", "source_generation": generation,
                            "producer_final_status": status, "consume_seq": consume_seq,
                            "action_relevant": consumes, "consumer_action": "a1" if consumes else None},
        "final_generation": 2 if pattern in ("mixed_generation", "supersession") else 1,
        "action_epoch": action_epoch if consumes else None,
        "action_attempted": consumes,
        "oracle_invalid_reason": invalid_reason,
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
