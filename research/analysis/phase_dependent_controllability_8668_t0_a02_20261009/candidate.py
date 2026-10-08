#!/usr/bin/env python3
"""One-shot candidate for the Issue #8668 T0 A02 finite plant."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_ID = "PHASE-CONTROL-DELAYS-8668-T0-A02-20261009"
BASE = "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385"
EMIT = 3
RETRY_TIME = 4.75
PHASES = ("PROPOSED", "ADMITTED", "QUEUED", "EMITTED", "CONSUMED")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze["allocation"] != RUN_ID or freeze["base_commit"] != BASE:
        raise SystemExit("STOP_FREEZE_ID_OR_BASE_MISMATCH")
    for name, expected in freeze["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise SystemExit(f"STOP_FREEZE_SOURCE_MISMATCH:{name}")
    return json.loads((ROOT / "design.json").read_text())


def removal_is_confirmed(phase: str, control_delay: int, receipt_delay: int,
                         same_frontier_order: str) -> bool:
    phase_index = PHASES.index(phase)
    if phase_index >= EMIT:
        return False
    removal_receipt_time = phase_index + control_delay + receipt_delay
    return removal_receipt_time < EMIT or (
        removal_receipt_time == EMIT and same_frontier_order == "CONTROL_FIRST"
    )


def trace_for(schedule: dict, outcome: dict) -> list[str]:
    phase = schedule["request_phase"]
    if phase == "NONE":
        return ["NO_INPUT", "NO_EFFECT"]
    phase_index = PHASES.index(phase)
    requested_at = float(phase_index) + (0.01 if phase_index >= EMIT else 0.0)
    events: list[tuple[float, int, str]] = [(requested_at, 0, f"AT_PHASE({phase})")]
    action = outcome["actual"]["cancel_requested"]
    if action:
        command_at = requested_at + schedule["control_delay_transitions"]
        removal_at = command_at + schedule["removal_receipt_delay_transitions"]
        same_time_priority = (0 if schedule["same_frontier_order"] == "CONTROL_FIRST" else 4)
        events.extend(((requested_at, 1, "CANCEL_REQUEST(op1)"),
                       (command_at, same_time_priority if command_at == EMIT else 0,
                        "CANCEL_COMMAND_DELIVERED(op1)"),
                       (removal_at, same_time_priority if removal_at == EMIT else 0,
                        "OPERATION_REMOVAL_CONFIRMED(op1)"
                        if outcome["actual"]["removal_confirmed_before_emit"]
                        else "REMOVAL_NOT_CONFIRMED(op1)")))
    stale = schedule["stale_receipt_position"]
    if stale == "BEFORE_RETRY":
        events.append((4.60, 0, "STALE_EFFECT_ACK(op0)"))
    if outcome["actual"]["effect_committed"]:
        events.extend(((float(EMIT), 1, "EMIT(op1)"), (float(EMIT), 2, "CONSUME(op1)"),
                       (float(EMIT), 3, "EFFECT_COMMIT(op1)"), (4.0, 0, "INPUT_RELEASE(op1)")))
        if schedule["effect_receipt_order"] == "EFFECT_FIRST":
            events.extend(((4.1, 0, "EFFECT_ACK(op1)"), (4.5, 0, "INPUT_RELEASE_ACK(op1)")))
        else:
            events.append((4.5, 0, "INPUT_RELEASE_ACK(op1)"))
    decision = outcome["controller"]["reported_state_at_retry"]
    events.append((RETRY_TIME, 0, f"RETRY_DECISION({decision})"))
    if schedule["retry_requested"]:
        events.append((RETRY_TIME + 0.01, 0,
                       "RETRY_ADMITTED(op2)" if outcome["controller"]["retry_admitted"]
                       else "RETRY_HELD(op2)"))
    if stale == "AFTER_RETRY":
        events.append((4.90, 0, "STALE_EFFECT_ACK(op0)"))
    if outcome["actual"]["effect_committed"] and schedule["effect_receipt_order"] == "RELEASE_FIRST":
        events.append((5.0, 0, "EFFECT_ACK(op1)"))
    return [event for _, _, event in sorted(events)]


def simulate(schedule: dict, policy: str) -> dict:
    if schedule["request_phase"] == "NONE":
        result = {
            "actual": {"cancel_requested": False, "removal_confirmed_before_emit": False,
                       "cancel_command_delivered_by_retry_decision": False,
                       "effect_committed": False, "input_release_required": False,
                       "effect_receipt_before_retry": False},
            "controller": {"reported_state_at_retry": "IDLE", "retry_admitted": False,
                           "false_cancel_claim": False, "unsafe_duplicate": False,
                           "safe_cancel_missed": False, "stale_receipt_accepted": False},
        }
        result["trace"] = trace_for(schedule, result)
        return result

    phase_index = PHASES.index(schedule["request_phase"])
    cancel_requested = {
        "STATIC_CANCELABLE": True,
        "STATIC_UNCONTROLLABLE": False,
        "PHASE_REFINED": phase_index < EMIT,
        "FAIL_CLOSED": False,
    }[policy]
    removable = removal_is_confirmed(
        schedule["request_phase"], schedule["control_delay_transitions"],
        schedule["removal_receipt_delay_transitions"], schedule["same_frontier_order"]
    )
    removed = cancel_requested and removable
    committed = not removed
    effect_seen = committed and schedule["effect_receipt_order"] == "EFFECT_FIRST"
    request_time = float(phase_index) + (0.01 if phase_index >= EMIT else 0.0)
    command_delivered = cancel_requested and (
        request_time + schedule["control_delay_transitions"] <= RETRY_TIME)
    safe_opportunity = removable
    retry_requested = schedule["retry_requested"]

    if policy == "STATIC_CANCELABLE":
        # The frozen static comparator equates command delivery with removal
        # whenever no effect receipt has yet arrived.
        reported = ("COMMITTED" if effect_seen else
                    "CANCELED" if command_delivered else "UNKNOWN")
        retry_admitted = retry_requested and reported == "CANCELED"
    elif policy == "STATIC_UNCONTROLLABLE":
        reported = "COMMITTED" if effect_seen else "PENDING"
        retry_admitted = False
    elif policy == "PHASE_REFINED":
        if removed:
            reported = "CANCELED"
        else:
            reported = "COMMITTED" if effect_seen else "UNKNOWN"
        retry_admitted = retry_requested and reported == "CANCELED"
    elif policy == "FAIL_CLOSED":
        reported = "COMMITTED" if effect_seen else "UNKNOWN"
        retry_admitted = False
    else:
        raise ValueError(policy)

    result = {
        "actual": {
            "cancel_requested": cancel_requested,
            "removal_confirmed_before_emit": removed,
            "cancel_command_delivered_by_retry_decision": command_delivered,
            "effect_committed": committed,
            "input_release_required": committed,
            "effect_receipt_before_retry": effect_seen,
        },
        "controller": {
            "reported_state_at_retry": reported,
            "retry_admitted": retry_admitted,
            "false_cancel_claim": reported == "CANCELED" and not removed,
            "unsafe_duplicate": committed and retry_admitted,
            "safe_cancel_missed": bool(retry_requested and safe_opportunity and not removed),
            "stale_receipt_accepted": False,
        },
    }
    result["trace"] = trace_for(schedule, result)
    return result


def schedules(design: dict) -> list[dict]:
    axes = design["axes"]
    rows = [{"schedule_id": "no-input-control", "request_phase": "NONE",
             "control_delay_transitions": 0, "removal_receipt_delay_transitions": 0,
             "same_frontier_order": "CONTROL_FIRST", "effect_receipt_order": "EFFECT_FIRST",
             "stale_receipt_position": "NONE", "retry_requested": False}]
    products = itertools.product(
        axes["request_phase"], axes["control_delay_transitions"],
        axes["removal_receipt_delay_transitions"], axes["same_frontier_order"],
        axes["effect_receipt_order"], axes["stale_receipt_position"],
        axes["retry_requested"],
    )
    for values in products:
        phase, cdelay, rdelay, order, receipt, stale, retry = values
        label = "-".join((phase.lower(), str(cdelay), str(rdelay), order.lower(),
                          receipt.lower(), stale.lower(), "retry" if retry else "no-retry"))
        rows.append({"schedule_id": label, "request_phase": phase,
                     "control_delay_transitions": cdelay,
                     "removal_receipt_delay_transitions": rdelay,
                     "same_frontier_order": order, "effect_receipt_order": receipt,
                     "stale_receipt_position": stale, "retry_requested": retry})
    return rows


def main() -> None:
    design = verify_freeze()
    policies = tuple(design["policies"])
    rows = []
    for schedule in schedules(design):
        rows.append({"exogenous_schedule": schedule,
                     "policy_outcomes": {name: simulate(schedule, name) for name in policies}})
    document = {"schema": "phase-control-delay-8668-t0-a02-v1",
                "run_id": RUN_ID, "base_commit": BASE,
                "design_sha256": digest(ROOT / "design.json"),
                "candidate_sha256": digest(Path(__file__)),
                "schedule_count": len(rows), "rows": rows}
    print(json.dumps(document, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
