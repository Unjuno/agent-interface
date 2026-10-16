#!/usr/bin/env python3
"""Emit the frozen Issue #8668 finite schedule model and policy decisions."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

RUN_ID = "PHASE-CONTROL-DELAY-8668-T0-A01-20261009"
BASE = "23d1807ffad8359e0f89421ee2b9bf5783c9d5f4"
FRONTIERS = ("PROPOSED", "ADMITTED", "QUEUED", "EMITTED", "CONSUMED")
PHASE_INDEX = {name: index for index, name in enumerate(FRONTIERS)}
EMIT_INDEX = PHASE_INDEX["EMITTED"]


def source_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def verify_frozen_source() -> None:
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text())
    expected = freeze["source_sha256"]["candidate.py"]
    if freeze["allocation"] != RUN_ID or freeze["base_commit"] != BASE or source_hash() != expected:
        raise SystemExit("STOP_FREEZE_SOURCE_MISMATCH")


def safe_removal(phase: str, control_delay: int, reply_delay: int, tie: str) -> bool:
    """Whether operation-bound removal is confirmed before emission."""
    start = PHASE_INDEX[phase]
    if start >= EMIT_INDEX:
        return False
    arrival = start + control_delay + reply_delay
    if arrival < EMIT_INDEX:
        return True
    return arrival == EMIT_INDEX and tie == "CONTROL_FIRST"


def event_trace(case: dict, canceled: bool, effect_seen: bool) -> list[str]:
    if case["request_phase"] == "NONE":
        return ["NO_INPUT", "NO_EFFECT"]
    trace = [f"CANCEL_REQUEST(op1,{case['request_phase']})"]
    trace.append(f"CONTROL_DELAY({case['control_delay']})")
    trace.append("CANCEL_COMMAND_DELIVERED(op1)")
    trace.append(f"CANCEL_REPLY_DELAY({case['reply_delay']})")
    trace.append("CANCEL_REMOVAL_CONFIRMED(op1)" if canceled else "CANCEL_DELIVERY_ONLY(op1)")
    if canceled:
        if case["stale_position"] == "BEFORE_RETRY":
            trace.append("STALE_EFFECT_ACK(op0)")
        if case["retry_requested"]:
            trace.append("RETRY_AFTER_CANCEL_PROOF(op2)")
        if case["stale_position"] == "AFTER_RETRY":
            trace.append("STALE_EFFECT_ACK(op0)")
        return trace
    if not canceled:
        trace.extend(("EMIT(op1)", "CONSUME(op1)", "EFFECT_COMMIT(op1)", "INPUT_RELEASE(op1)"))
        receipts = (["EFFECT_ACK(op1)", "INPUT_RELEASE_ACK(op1)"]
                    if case["receipt_order"] == "EFFECT_FIRST"
                    else ["INPUT_RELEASE_ACK(op1)", "EFFECT_ACK(op1)"])
        if effect_seen:
            trace.extend(receipts)
        else:
            trace.extend(item for item in receipts if not item.startswith("EFFECT_ACK"))
    stale = case["stale_position"]
    if stale == "BEFORE_RETRY":
        trace.append("STALE_EFFECT_ACK(op0)")
    if effect_seen:
        if case["retry_requested"]:
            trace.append("RETRY_AFTER_EFFECT_ACK(op2)")
    else:
        trace.append("OBSERVATION_TIMEOUT(op1)")
        if case["retry_requested"]:
            trace.append("RETRY_REQUEST(op2)")
    if stale == "AFTER_RETRY":
        trace.append("STALE_EFFECT_ACK(op0)")
    if not canceled and not effect_seen:
        trace.append("EFFECT_ACK(op1)")
    return trace


def make_case(phase: str, control_delay: int, reply_delay: int, tie: str,
              receipt_order: str, stale_position: str, retry: bool) -> dict:
    case_id = "-".join((phase.lower(), str(control_delay), str(reply_delay),
                        tie.lower(), receipt_order.lower(), stale_position.lower(),
                        "retry" if retry else "no-retry"))
    case = {
        "case_id": case_id,
        "request_phase": phase,
        "control_delay": control_delay,
        "reply_delay": reply_delay,
        "boundary_order": tie,
        "receipt_order": receipt_order,
        "stale_position": stale_position,
        "retry_requested": retry,
    }
    if phase == "NONE":
        case["actual"] = {
            "removal_confirmed_before_emit": False,
            "effect_committed": False,
            "input_release_required": False,
            "effect_receipt_before_retry": False,
            "stale_receipt_accepted_by_phase_policy": False,
            "release_implies_abort": False,
        }
        idle = {
            "STATIC_CANCELABLE": {"status_at_retry": "IDLE", "false_cancel_claim": False,
                                  "retry_admitted": False, "unsafe_duplicate": False},
            "STATIC_UNCONTROLLABLE": {"status_at_retry": "IDLE", "safe_cancel_missed": False,
                                      "retry_admitted": False, "unsafe_duplicate": False},
            "FAIL_CLOSED": {"status_at_retry": "IDLE", "safe_cancel_missed": False,
                            "retry_admitted": False, "unsafe_duplicate": False},
            "PHASE_REFINED": {"status_at_retry": "IDLE", "false_cancel_claim": False,
                              "retry_admitted": False, "unsafe_duplicate": False,
                              "safe_cancel_preserved": False},
        }
        case["policies"] = idle
        case["trace"] = ["NO_INPUT", "NO_EFFECT"]
        return case
    canceled = safe_removal(phase, control_delay, reply_delay, tie)
    effect_committed = not canceled
    effect_seen_before_retry = effect_committed and receipt_order == "EFFECT_FIRST"
    static_cancelable_reported = not effect_seen_before_retry
    static_retry = retry and static_cancelable_reported
    phase_status = "CANCELED" if canceled else (
        "COMMITTED" if effect_seen_before_retry else "UNKNOWN")
    phase_retry = retry and phase_status == "CANCELED"
    case["actual"] = {
        "removal_confirmed_before_emit": canceled,
        "effect_committed": effect_committed,
        "input_release_required": effect_committed,
        "effect_receipt_before_retry": effect_seen_before_retry,
        "stale_receipt_accepted_by_phase_policy": False,
        "release_implies_abort": False,
    }
    case["policies"] = {
        "STATIC_CANCELABLE": {
            "status_at_retry": "CANCELED" if static_cancelable_reported else "COMMITTED",
            "false_cancel_claim": bool(effect_committed and static_cancelable_reported),
            "retry_admitted": static_retry,
            "unsafe_duplicate": bool(effect_committed and static_retry),
        },
        "STATIC_UNCONTROLLABLE": {
            "status_at_retry": "UNKNOWN" if not effect_seen_before_retry else "COMMITTED",
            "safe_cancel_missed": canceled,
            "retry_admitted": False,
            "unsafe_duplicate": False,
        },
        "FAIL_CLOSED": {
            "status_at_retry": "UNKNOWN" if not effect_seen_before_retry else "COMMITTED",
            "safe_cancel_missed": canceled,
            "retry_admitted": False,
            "unsafe_duplicate": False,
        },
        "PHASE_REFINED": {
            "status_at_retry": phase_status,
            "false_cancel_claim": False,
            "retry_admitted": phase_retry,
            "unsafe_duplicate": False,
            "safe_cancel_preserved": canceled,
        },
    }
    case["trace"] = event_trace(case, canceled, effect_seen_before_retry)
    return case


def schedule_rows() -> list[dict]:
    rows = [make_case("NONE", 0, 0, "CONTROL_FIRST", "EFFECT_FIRST", "NONE", False)]
    axes = itertools.product(
        FRONTIERS, (0, 1), (0, 1), ("CONTROL_FIRST", "PLANT_FIRST"),
        ("EFFECT_FIRST", "RELEASE_FIRST"), ("NONE", "BEFORE_RETRY", "AFTER_RETRY"),
        (False, True),
    )
    rows.extend(make_case(*values) for values in axes)
    return rows


def main() -> None:
    verify_frozen_source()
    rows = schedule_rows()
    result = {
        "schema": "phase-controllability-8668-t0-a01-v1",
        "run_id": RUN_ID,
        "base_commit": BASE,
        "candidate_sha256": source_hash(),
        "declared_bounds": {"control_delivery_transitions": 1, "cancel_reply_transitions": 1,
                            "phase_count": len(FRONTIERS)},
        "schedule_count": len(rows),
        "cases": rows,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
