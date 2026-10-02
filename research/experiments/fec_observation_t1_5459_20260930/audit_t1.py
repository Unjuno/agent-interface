"""Independent Gaussian-elimination audit; imports no simulator code."""
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent
RESULTS = ROOT / "results" / "t1-01"
SOURCE = (0x11, 0x23, 0x45, 0x89)
IDS = [0, 1, 2, 3]
WINDOW = "window-5459-t1-01"
GENERATION = 17
MANIFEST = "sha256:5459-t1-manifest-0-1-2-3"
DEADLINE = 4
PROFILES = (0, 63, 48, 15, 42, 21, 9, 54)
ARMS = ("fixed", "retransmit", "adaptive")
FAULTS = ("wrong_generation", "wrong_window", "incomplete_manifest",
          "stale_manifest", "corrupt_unauthenticated_source")


def _solve_equations(packets):
    """Independent GF(2) RREF decoder; returns four values or None."""
    matrix = [[packet["mask"], packet["value"]] for packet in packets]
    pivot_row = 0
    for column in range(4):
        pivot = next((r for r in range(pivot_row, len(matrix))
                      if matrix[r][0] & (1 << column)), None)
        if pivot is None:
            continue
        matrix[pivot_row], matrix[pivot] = matrix[pivot], matrix[pivot_row]
        for r in range(len(matrix)):
            if r != pivot_row and matrix[r][0] & (1 << column):
                matrix[r][0] ^= matrix[pivot_row][0]
                matrix[r][1] ^= matrix[pivot_row][1]
        pivot_row += 1
        if pivot_row == 4:
            break
    if pivot_row != 4:
        return None
    values = [None] * 4
    for mask, value in matrix[:pivot_row]:
        if mask not in (1, 2, 4, 8):
            return None
        values[mask.bit_length() - 1] = value
    return values if all(value is not None for value in values) else None


def _packet_metadata_valid(packet, manifest_valid):
    return (manifest_valid and packet.get("window_id") == WINDOW
            and packet.get("generation") == GENERATION
            and packet.get("manifest_ids") == IDS
            and packet.get("manifest_hash") == MANIFEST
            and packet.get("auth_ok") is True
            and packet.get("payload_hash_ok") is True)


def _independent_row_result(row):
    errors = []
    if row.get("arm") not in ARMS:
        return ["arm_invalid"], None
    loss_mask, delay_mask = row.get("loss_mask"), row.get("delay_mask")
    if type(loss_mask) is not int or not 0 <= loss_mask < 64:
        return ["loss_mask_invalid"], None
    if type(delay_mask) is not int or not 0 <= delay_mask < 64:
        return ["delay_mask_invalid"], None
    packets = row.get("packets")
    if not isinstance(packets, list):
        return ["packets_not_list"], None

    slots = set()
    for packet in packets:
        if not isinstance(packet, dict):
            errors.append("packet_not_object")
            continue
        slot = packet.get("slot")
        if type(slot) is not int or not 0 <= slot < 6 or slot in slots:
            errors.append("packet_slot_invalid_or_duplicate")
            continue
        slots.add(slot)
        if type(packet.get("sent_round")) is not int:
            errors.append("send_round_invalid")
            continue
        expected_lost = bool(loss_mask & (1 << slot))
        expected_delay = 2 if delay_mask & (1 << slot) else 0
        expected_arrival = None if expected_lost else packet["sent_round"] + expected_delay
        if packet.get("lost") is not expected_lost or packet.get("delay") != expected_delay:
            errors.append("channel_trace_mismatch")
        if packet.get("arrival_round") != expected_arrival:
            errors.append("arrival_round_mismatch")
        if packet.get("delivered") is not (not expected_lost and expected_arrival <= DEADLINE):
            errors.append("delivery_flag_mismatch")
        kind, mask, value = packet.get("kind"), packet.get("mask"), packet.get("value")
        if kind == "source":
            index = packet.get("symbol_id")
            if type(index) is not int or not 0 <= index < 4 or mask != (1 << index):
                errors.append("source_equation_invalid")
            elif packet.get("auth_ok") is True and packet.get("payload_hash_ok") is True:
                if value != SOURCE[index]:
                    errors.append("source_payload_mismatch")
        elif kind == "repair":
            if mask == 3:
                expected_value = SOURCE[0] ^ SOURCE[1]
            elif mask == 12:
                expected_value = SOURCE[2] ^ SOURCE[3]
            else:
                expected_value = None
            if expected_value is None:
                errors.append("repair_equation_invalid")
            elif packet.get("auth_ok") is True and packet.get("payload_hash_ok") is True:
                if value != expected_value:
                    errors.append("repair_payload_mismatch")
        else:
            errors.append("packet_kind_invalid")

    if row.get("packets_sent") != len(packets):
        errors.append("packets_sent_mismatch")
    received_count = sum(packet.get("delivered") is True for packet in packets
                         if isinstance(packet, dict))
    if row.get("packets_received") != received_count:
        errors.append("packets_received_mismatch")

    global_metadata_valid = (
        row.get("window_id") == WINDOW and row.get("generation") == GENERATION
        and row.get("manifest_ids") == IDS and row.get("manifest_hash") == MANIFEST
    )
    manifest_valid = row.get("manifest_ids") == IDS and row.get("manifest_hash") == MANIFEST
    usable = [packet for packet in packets
              if isinstance(packet, dict) and packet.get("delivered") is True
              and _packet_metadata_valid(packet, manifest_valid)]
    decoded = None
    decode_round = None
    for tick in range(DEADLINE + 1):
        subset = [packet for packet in usable if packet["arrival_round"] <= tick]
        values = _solve_equations(subset)
        if values is not None:
            decoded, decode_round = values, tick
            break

    if not manifest_valid or not global_metadata_valid:
        status = "UNKNOWN"
    elif decoded is None:
        status = "INCOMPLETE"
    elif decoded == list(SOURCE):
        status = "SEMANTICALLY_CONFIRMED"
    else:
        status = "UNKNOWN"
    claimed = row.get("decoded_values")
    claimed_round = row.get("decode_round")
    claimed_completion = decode_round if status == "SEMANTICALLY_CONFIRMED" else None
    if claimed != decoded:
        errors.append("decoded_values_mismatch")
    if claimed_round != decode_round:
        errors.append("decode_round_mismatch")
    if row.get("semantic_status") != status:
        errors.append("semantic_status_mismatch")
    if row.get("completion_round") != claimed_completion:
        errors.append("completion_round_mismatch")
    if row.get("expected_values") != list(SOURCE):
        errors.append("expected_state_mismatch")

    fault = row.get("fault")
    if fault not in (None,) + FAULTS:
        errors.append("fault_label_invalid")
    if fault == "wrong_generation" and (row.get("generation") == GENERATION or global_metadata_valid):
        errors.append("wrong_generation_control_missing")
    if fault == "wrong_window" and (row.get("window_id") == WINDOW or global_metadata_valid):
        errors.append("wrong_window_control_missing")
    if fault == "incomplete_manifest" and (row.get("manifest_ids") == IDS or row.get("manifest_complete") is True):
        errors.append("missing_dependency_control_missing")
    if fault == "stale_manifest" and row.get("manifest_hash") == MANIFEST:
        errors.append("stale_manifest_control_missing")
    if fault == "corrupt_unauthenticated_source":
        corrupt = [packet for packet in packets if packet.get("auth_ok") is False]
        if (len(corrupt) != 1 or corrupt[0].get("slot") != 0
                or corrupt[0].get("payload_hash_ok") is not False):
            errors.append("corruption_control_missing")

    recomputed = {
        "semantic_status": status, "decoded_values": decoded,
        "completion_round": claimed_completion,
    }
    return errors, recomputed


def audit_result(raw):
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "fec-observation-t1-raw-v1":
        return ["raw_schema_invalid"]
    protocol = raw.get("protocol")
    if not isinstance(protocol, dict):
        return ["protocol_missing"]
    if (protocol.get("source_values") != list(SOURCE) or protocol.get("source_ids") != IDS
            or protocol.get("window_id") != WINDOW or protocol.get("generation") != GENERATION
            or protocol.get("manifest_hash") != MANIFEST or protocol.get("deadline") != DEADLINE
            or protocol.get("feedback_cut") != 1 or protocol.get("delay_profiles") != list(PROFILES)
            or protocol.get("arms") != list(ARMS)):
        errors.append("protocol_mismatch")

    trace_runs, fault_runs = raw.get("trace_runs"), raw.get("fault_runs")
    if not isinstance(trace_runs, list) or len(trace_runs) != 64 * len(PROFILES) * len(ARMS):
        return errors + ["trace_grid_incomplete"]
    if not isinstance(fault_runs, list) or len(fault_runs) != len(FAULTS) * len(ARMS):
        return errors + ["fault_grid_incomplete"]

    expected_trace_keys = {(loss, delay, arm) for loss in range(64)
                           for delay in PROFILES for arm in ARMS}
    observed_trace_keys = set()
    verified_trace = []
    for row in trace_runs:
        if not isinstance(row, dict):
            errors.append("trace_row_not_object")
            continue
        key = (row.get("loss_mask"), row.get("delay_mask"), row.get("arm"))
        if key in observed_trace_keys:
            errors.append("trace_row_duplicate")
        observed_trace_keys.add(key)
        if key not in expected_trace_keys:
            errors.append("trace_row_unexpected")
        row_errors, checked = _independent_row_result(row)
        errors.extend(f"trace:{row.get('trace_id')}:{e}" for e in row_errors)
        if checked is not None:
            verified_trace.append({**row, **checked})
    if observed_trace_keys != expected_trace_keys:
        errors.append("trace_grid_identity_mismatch")

    expected_fault_keys = {(fault, arm) for fault in FAULTS for arm in ARMS}
    observed_fault_keys = set()
    verified_fault = []
    for row in fault_runs:
        if not isinstance(row, dict):
            errors.append("fault_row_not_object")
            continue
        key = (row.get("fault"), row.get("arm"))
        if key in observed_fault_keys:
            errors.append("fault_row_duplicate")
        observed_fault_keys.add(key)
        if key not in expected_fault_keys:
            errors.append("fault_row_unexpected")
        row_errors, checked = _independent_row_result(row)
        errors.extend(f"fault:{row.get('fault')}:{row.get('arm')}:{e}" for e in row_errors)
        if checked is not None:
            verified_fault.append({**row, **checked})
    if observed_fault_keys != expected_fault_keys:
        errors.append("fault_grid_identity_mismatch")

    recomputed = {
        "schema": "fec-observation-t1-summary-v1",
        "trace_count": len(verified_trace),
        "fault_run_count": len(verified_fault),
        "by_arm": {},
        "fault_false_successes": sum(
            row["semantic_status"] == "SEMANTICALLY_CONFIRMED"
            and (row["decoded_values"] != row["expected_values"]
                 or not row["window_metadata_valid"] or not row["manifest_complete"])
            for row in verified_fault),
    }
    for arm in ARMS:
        rows = [row for row in verified_trace if row["arm"] == arm]
        times = [row["completion_round"] for row in rows
                 if row["semantic_status"] == "SEMANTICALLY_CONFIRMED"]
        counts = Counter(times)
        recomputed["by_arm"][arm] = {
            "trace_count": len(rows),
            "confirmed": sum(row["semantic_status"] == "SEMANTICALLY_CONFIRMED" for row in rows),
            "false_successes": sum(row["semantic_status"] == "SEMANTICALLY_CONFIRMED"
                                   and row["decoded_values"] != row["expected_values"] for row in rows),
            "packets_sent_total": sum(row["packets_sent"] for row in rows),
            "completion_round_counts": {str(t): counts[t] for t in sorted(counts)},
        }
    if raw.get("summary") != {key: value for key, value in recomputed.items() if key != "schema"}:
        errors.append("summary_mismatch")
    if recomputed["fault_false_successes"] != 0:
        errors.append("fault_false_success")
    return errors


def main():
    raw_path = RESULTS / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = audit_result(raw)
    result = {
        "auditor": "audit_t1.py independent RREF implementation",
        "candidate_imported": False,
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper(),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "trace_runs": len(raw.get("trace_runs", [])),
        "fault_runs": len(raw.get("fault_runs", [])),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "AUDIT.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
