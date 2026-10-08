"""Deterministic four-symbol XOR transport construction; not a real FEC stack."""
from collections import Counter


SOURCE_VALUES = (0x11, 0x23, 0x45, 0x89)
SOURCE_IDS = (0, 1, 2, 3)
WINDOW_ID = "window-5459-t1-01"
GENERATION = 17
MANIFEST_IDS = [0, 1, 2, 3]
MANIFEST_HASH = "sha256:5459-t1-manifest-0-1-2-3"
DEADLINE = 4
FEEDBACK_CUT = 1
DELAY_PROFILES = (0, 63, 48, 15, 42, 21, 9, 54)
ARMS = ("fixed", "retransmit", "adaptive")
FAULTS = ("wrong_generation", "wrong_window", "incomplete_manifest",
          "stale_manifest", "corrupt_unauthenticated_source")
PAIR_MASKS = (0b0011, 0b1100)


def _source(index):
    return {"kind": "source", "symbol_id": index, "mask": 1 << index,
            "value": SOURCE_VALUES[index], "label": f"s{index}"}


def _parity(pair):
    left = pair * 2
    right = left + 1
    return {"kind": "repair", "symbol_id": None, "mask": PAIR_MASKS[pair],
            "value": SOURCE_VALUES[left] ^ SOURCE_VALUES[right], "label": f"p{pair}"}


def _valid_packet(packet, manifest_valid):
    return (manifest_valid and packet["window_id"] == WINDOW_ID
            and packet["generation"] == GENERATION
            and packet["manifest_hash"] == MANIFEST_HASH
            and packet["manifest_ids"] == MANIFEST_IDS
            and packet["auth_ok"] is True and packet["payload_hash_ok"] is True)


def _decode_pairwise(packets):
    """Decode only the two preregistered XOR pairs; return values or None."""
    known = [None, None, None, None]
    parity = [None, None]
    for packet in packets:
        if packet["kind"] == "source":
            index = packet["symbol_id"]
            if known[index] is not None and known[index] != packet["value"]:
                return None
            known[index] = packet["value"]
        elif packet["mask"] in PAIR_MASKS:
            pair = PAIR_MASKS.index(packet["mask"])
            if parity[pair] is not None and parity[pair] != packet["value"]:
                return None
            parity[pair] = packet["value"]

    for pair, equation in enumerate(parity):
        left, right = pair * 2, pair * 2 + 1
        if equation is not None:
            if known[left] is not None and known[right] is None:
                known[right] = equation ^ known[left]
            elif known[right] is not None and known[left] is None:
                known[left] = equation ^ known[right]
            elif known[left] is not None and known[right] is not None:
                if known[left] ^ known[right] != equation:
                    return None
    return known if all(value is not None for value in known) else None


def _metadata(fault):
    generation = GENERATION
    window_id = WINDOW_ID
    manifest_ids = list(MANIFEST_IDS)
    manifest_hash = MANIFEST_HASH
    if fault == "wrong_generation":
        generation -= 1
    elif fault == "wrong_window":
        window_id = "window-stale"
    elif fault == "incomplete_manifest":
        manifest_ids = [0, 1, 2]
    elif fault == "stale_manifest":
        manifest_hash = "sha256:stale"
    return generation, window_id, manifest_ids, manifest_hash


def run_trace(loss_mask, delay_mask, arm, fault=None):
    if type(loss_mask) is not int or not 0 <= loss_mask < 64:
        raise ValueError("loss_mask must be a six-bit integer")
    if type(delay_mask) is not int or not 0 <= delay_mask < 64:
        raise ValueError("delay_mask must be a six-bit integer")
    if arm not in ARMS or fault not in (None,) + FAULTS:
        raise ValueError("unknown arm or fault")

    generation, window_id, manifest_ids, manifest_hash = _metadata(fault)
    manifest_valid = (manifest_ids == MANIFEST_IDS and manifest_hash == MANIFEST_HASH)
    global_window_valid = generation == GENERATION and window_id == WINDOW_ID
    packets = []

    def send(slot, spec, send_round):
        lost = bool(loss_mask & (1 << slot))
        delay = 2 if delay_mask & (1 << slot) else 0
        value = spec["value"]
        auth_ok = True
        payload_hash_ok = True
        if fault == "corrupt_unauthenticated_source" and slot == 0 and spec["kind"] == "source":
            value ^= 0xFF
            auth_ok = False
            payload_hash_ok = False
        arrival = None if lost else send_round + delay
        packets.append({
            "slot": slot, "kind": spec["kind"], "symbol_id": spec["symbol_id"],
            "label": spec["label"], "mask": spec["mask"], "value": value,
            "sent_round": send_round, "lost": lost, "delay": delay,
            "arrival_round": arrival,
            "delivered": not lost and arrival <= DEADLINE,
            "window_id": window_id, "generation": generation,
            "manifest_ids": list(manifest_ids), "manifest_hash": manifest_hash,
            "auth_ok": auth_ok, "payload_hash_ok": payload_hash_ok,
        })

    for index in SOURCE_IDS:
        send(index, _source(index), 0)

    initial_feedback = [packet for packet in packets
                        if packet["delivered"] and packet["arrival_round"] <= FEEDBACK_CUT
                        and _valid_packet(packet, manifest_valid)
                        and packet["kind"] == "source"]
    present = {packet["symbol_id"] for packet in initial_feedback}

    if arm == "fixed":
        followups = [(_parity(0), 0), (_parity(1), 0)]
    elif arm == "retransmit":
        followups = [(_source(index), FEEDBACK_CUT)
                     for index in SOURCE_IDS if index not in present][:2]
    else:
        actions = []
        for pair in range(2):
            members = (pair * 2, pair * 2 + 1)
            missing = [index for index in members if index not in present]
            if len(missing) == 1:
                actions.append(_parity(pair))
            else:
                actions.extend(_source(index) for index in missing)
        followups = [(spec, FEEDBACK_CUT) for spec in actions[:2]]

    for slot, (spec, send_round) in zip((4, 5), followups):
        send(slot, spec, send_round)

    valid_deliveries = [packet for packet in packets
                        if packet["delivered"] and _valid_packet(packet, manifest_valid)]
    decoded = None
    decode_round = None
    for round_number in range(DEADLINE + 1):
        available = [packet for packet in valid_deliveries
                     if packet["arrival_round"] <= round_number]
        candidate = _decode_pairwise(available)
        if candidate is not None:
            decoded = candidate
            decode_round = round_number
            break

    if not manifest_valid or not global_window_valid:
        semantic_status = "UNKNOWN"
    elif decoded is None:
        semantic_status = "INCOMPLETE"
    elif decoded == list(SOURCE_VALUES):
        semantic_status = "SEMANTICALLY_CONFIRMED"
    else:
        semantic_status = "UNKNOWN"

    expected_values = list(SOURCE_VALUES)
    return {
        "trace_id": f"loss-{loss_mask:02x}-delay-{delay_mask:02x}",
        "loss_mask": loss_mask, "delay_mask": delay_mask, "arm": arm,
        "fault": fault, "deadline": DEADLINE, "feedback_cut": FEEDBACK_CUT,
        "window_id": window_id, "expected_window_id": WINDOW_ID,
        "generation": generation, "expected_generation": GENERATION,
        "manifest_ids": manifest_ids, "expected_manifest_ids": MANIFEST_IDS,
        "manifest_hash": manifest_hash, "expected_manifest_hash": MANIFEST_HASH,
        "manifest_complete": manifest_ids == MANIFEST_IDS,
        "window_metadata_valid": global_window_valid,
        "packets": packets, "packets_sent": len(packets),
        "packets_received": sum(packet["delivered"] for packet in packets),
        "decoded_values": decoded, "decode_round": decode_round,
        "semantic_status": semantic_status,
        "completion_round": decode_round if semantic_status == "SEMANTICALLY_CONFIRMED" else None,
        "expected_values": expected_values,
    }


def _summary(trace_runs, fault_runs):
    result = {}
    for arm in ARMS:
        rows = [row for row in trace_runs if row["arm"] == arm]
        times = sorted(row["completion_round"] for row in rows
                       if row["completion_round"] is not None)
        result[arm] = {
            "trace_count": len(rows),
            "confirmed": sum(row["semantic_status"] == "SEMANTICALLY_CONFIRMED" for row in rows),
            "false_successes": sum(row["semantic_status"] == "SEMANTICALLY_CONFIRMED"
                                   and row["decoded_values"] != row["expected_values"] for row in rows),
            "packets_sent_total": sum(row["packets_sent"] for row in rows),
            "completion_round_counts": {str(t): times.count(t) for t in sorted(set(times))},
        }
    return {
        "trace_count": len(trace_runs),
        "fault_run_count": len(fault_runs),
        "by_arm": result,
        "fault_false_successes": sum(row["semantic_status"] == "SEMANTICALLY_CONFIRMED"
                                     and (row["decoded_values"] != row["expected_values"]
                                          or not row["window_metadata_valid"]
                                          or not row["manifest_complete"])
                                     for row in fault_runs),
    }


def build_raw():
    trace_runs = []
    for loss_mask in range(64):
        for delay_mask in DELAY_PROFILES:
            for arm in ARMS:
                trace_runs.append(run_trace(loss_mask, delay_mask, arm))
    fault_runs = [run_trace(0, 0, arm, fault)
                  for fault in FAULTS for arm in ARMS]
    return {
        "schema": "fec-observation-t1-raw-v1",
        "protocol": {
            "source_values": list(SOURCE_VALUES), "source_ids": MANIFEST_IDS,
            "window_id": WINDOW_ID, "generation": GENERATION,
            "manifest_hash": MANIFEST_HASH, "deadline": DEADLINE,
            "feedback_cut": FEEDBACK_CUT, "delay_profiles": list(DELAY_PROFILES),
            "loss_masks_per_profile": 64, "arms": list(ARMS),
            "repair_pair_masks": list(PAIR_MASKS),
        },
        "trace_runs": trace_runs,
        "fault_runs": fault_runs,
        "summary": _summary(trace_runs, fault_runs),
    }
