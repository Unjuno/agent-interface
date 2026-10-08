"""Independent policy-schedule check for immutable #5459 T1 raw evidence.

This module intentionally does not import the T1 candidate or decoder. It
checks whether each recorded arm emitted the follow-up packets prescribed by
the frozen policy, given the initial feedback available at the cut.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SOURCE = (0x11, 0x23, 0x45, 0x89)
WINDOW = "window-5459-t1-01"
GENERATION = 17
MANIFEST_IDS = [0, 1, 2, 3]
MANIFEST_HASH = "sha256:5459-t1-manifest-0-1-2-3"
FEEDBACK_CUT = 1
DEADLINE = 4
PAIR_MASK = (0b0011, 0b1100)
ARMS = ("fixed", "retransmit", "adaptive")


def _valid_feedback(packet: dict) -> bool:
    return (
        packet.get("delivered") is True
        and type(packet.get("arrival_round")) is int
        and packet["arrival_round"] <= FEEDBACK_CUT
        and packet.get("window_id") == WINDOW
        and packet.get("generation") == GENERATION
        and packet.get("manifest_ids") == MANIFEST_IDS
        and packet.get("manifest_hash") == MANIFEST_HASH
        and packet.get("auth_ok") is True
        and packet.get("payload_hash_ok") is True
    )


def _source(index: int, sent_round: int) -> dict:
    return {
        "kind": "source", "symbol_id": index, "mask": 1 << index,
        "label": f"s{index}", "sent_round": sent_round,
    }


def _repair(pair: int, sent_round: int) -> dict:
    return {
        "kind": "repair", "symbol_id": None, "mask": PAIR_MASK[pair],
        "label": f"p{pair}", "sent_round": sent_round,
    }


def expected_schedule(row: dict) -> list[dict]:
    """Reconstruct source and follow-up assignments from frozen arm policy."""
    arm = row.get("arm")
    if arm not in ARMS:
        raise ValueError("arm_invalid")
    packets = row.get("packets")
    if not isinstance(packets, list):
        raise ValueError("packets_not_list")
    by_slot = {p.get("slot"): p for p in packets if isinstance(p, dict)}
    if (len(by_slot) != len(packets) or len(packets) < 4
            or set(by_slot) != set(range(len(packets)))):
        raise ValueError("packet_slots_not_contiguous_from_zero")

    expected = [_source(i, 0) for i in range(4)]
    for slot, spec in enumerate(expected):
        actual = by_slot[slot]
        if any(actual.get(key) != value for key, value in spec.items()):
            raise ValueError(f"initial_source_schedule_mismatch_slot_{slot}")

    present = {
        by_slot[i].get("symbol_id") for i in range(4)
        if _valid_feedback(by_slot[i])
    }
    if arm == "fixed":
        followups = [_repair(0, 0), _repair(1, 0)]
    elif arm == "retransmit":
        followups = [_source(i, FEEDBACK_CUT)
                     for i in range(4) if i not in present][:2]
    else:
        followups = []
        for pair in range(2):
            members = (pair * 2, pair * 2 + 1)
            missing = [i for i in members if i not in present]
            if len(missing) == 1:
                followups.append(_repair(pair, FEEDBACK_CUT))
            elif len(missing) == 2:
                followups.extend(_source(i, FEEDBACK_CUT) for i in missing)
        followups = followups[:2]
    return expected + followups


def policy_errors(row: dict) -> list[str]:
    try:
        expected = expected_schedule(row)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    packets = row["packets"]
    if len(packets) != len(expected):
        return ["packet_count_policy_mismatch"]
    errors = []
    loss_mask, delay_mask = row.get("loss_mask"), row.get("delay_mask")
    if (type(loss_mask) is not int or not 0 <= loss_mask < 64
            or type(delay_mask) is not int or not 0 <= delay_mask < 64):
        return ["channel_mask_invalid"]
    for packet in packets:
        slot = packet["slot"]
        if type(packet.get("sent_round")) is not int:
            errors.append(f"slot_{slot}_send_round_invalid")
            continue
        lost = bool(loss_mask & (1 << slot))
        delay = 2 if delay_mask & (1 << slot) else 0
        arrival = None if lost else packet["sent_round"] + delay
        if packet.get("lost") is not lost or packet.get("delay") != delay:
            errors.append(f"slot_{slot}_channel_mismatch")
        if packet.get("arrival_round") != arrival:
            errors.append(f"slot_{slot}_arrival_mismatch")
        if packet.get("delivered") is not (not lost and arrival <= DEADLINE):
            errors.append(f"slot_{slot}_delivery_mismatch")
    for slot, spec in enumerate(expected):
        actual = packets[slot]
        if actual.get("slot") != slot or any(actual.get(k) != v for k, v in spec.items()):
            errors.append(f"slot_{slot}_policy_mismatch")
    return errors


def audit(raw: dict) -> dict:
    if raw.get("schema") != "fec-observation-t1-raw-v1":
        raise ValueError("raw_schema_invalid")
    rows, faults = raw.get("trace_runs"), raw.get("fault_runs")
    if not isinstance(rows, list) or len(rows) != 1536:
        raise ValueError("trace_grid_incomplete")
    if not isinstance(faults, list) or len(faults) != 15:
        raise ValueError("fault_grid_incomplete")
    mismatches = []
    for kind, group in (("trace", rows), ("fault", faults)):
        for index, row in enumerate(group):
            mismatches.extend(f"{kind}[{index}]:{e}" for e in policy_errors(row))
    return {
        "schema": "fec-observation-5459-policy-audit-v1",
        "trace_rows": len(rows), "fault_rows": len(faults),
        "rows_checked": len(rows) + len(faults),
        "policy_mismatches": mismatches,
        "status": "PASS_POLICY_SCHEDULE_SCOPED" if not mismatches else "FAIL_POLICY_SCHEDULE",
    }


def audit_file(path: Path) -> dict:
    raw_bytes = path.read_bytes()
    report = audit(json.loads(raw_bytes))
    report["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest().upper()
    report["raw_bytes"] = len(raw_bytes)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_json", type=Path)
    args = parser.parse_args()
    result = audit_file(args.raw_json)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["policy_mismatches"] else 1)

