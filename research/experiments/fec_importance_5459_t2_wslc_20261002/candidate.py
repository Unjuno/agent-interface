"""Deterministic, finite T2 packet-channel candidate; no real transport."""
import hashlib
import json
import sys
from pathlib import Path


ALLOCATION = "FEC-IMPORTANCE-5459-T2-WSLC-20261002-01"
SEED = 54592026100201
SOURCE_VALUES = (0x11, 0x23, 0x45, 0x89, 0x5A, 0xC3, 0x6D, 0xF0)
MANDATORY = (0, 2, 5, 7)
OPTIONAL = (1, 3, 4, 6)
DECISION_CONTRACT = {
    "status": [0, 2, 5, 7],
    "detail": list(range(8)),
    "optional_dependent": [0, 2, 5, 6, 7],
}
ARMS = ("equal_repair", "unequal_repair", "mandatory_first_retransmit",
        "raw_all_retransmit")
FAULTS = ("wrong_generation", "wrong_window", "incomplete_manifest",
          "stale_manifest", "importance_missing", "critical_mislabeled_optional",
          "corrupt_mandatory_source")
DELAY_PROFILES = (0x00, 0xFF, 0x0F, 0xF0)
DEADLINE = 4
FEEDBACK_CUT = 1
WINDOW_ID = "fec-window-5459-t2-01"
GENERATION = 2026100201
MANIFEST_IDS = list(range(8))
MANIFEST_HASH = "sha256:fec-importance-manifest-5459-t2-v1"
IMPORTANCE_HASH = "sha256:fec-importance-labels-5459-t2-v1"


def _context(fault):
    generation, window_id = GENERATION, WINDOW_ID
    manifest_ids = list(MANIFEST_IDS)
    manifest_hash, importance_hash = MANIFEST_HASH, IMPORTANCE_HASH
    labels = {i: ("mandatory" if i in MANDATORY else "optional") for i in range(8)}
    importance_valid = True
    if fault == "wrong_generation":
        generation -= 1
    elif fault == "wrong_window":
        window_id = "stale-window"
    elif fault == "incomplete_manifest":
        manifest_ids.remove(6)
    elif fault == "stale_manifest":
        manifest_hash = "sha256:stale-manifest"
    elif fault == "importance_missing":
        importance_hash = None
        labels = None
        importance_valid = False
    elif fault == "critical_mislabeled_optional":
        labels[7] = "optional"
        importance_hash = "sha256:importance-map-with-mislabeled-critical-7"
    return {
        "generation": generation,
        "window_id": window_id,
        "manifest_ids": manifest_ids,
        "manifest_hash": manifest_hash,
        "importance_labels": labels,
        "importance_hash": importance_hash,
        "importance_valid": importance_valid,
    }


def _valid_context(context):
    return (context["generation"] == GENERATION
            and context["window_id"] == WINDOW_ID
            and context["manifest_ids"] == MANIFEST_IDS
            and context["manifest_hash"] == MANIFEST_HASH)


def _label_order(labels):
    if not labels:
        return None
    return [i for tier in ("mandatory", "optional")
            for i in range(8) if labels.get(i) == tier]


def _repair_spec(mask, repair_id):
    value = 0
    for i in range(8):
        if mask & (1 << i):
            value ^= SOURCE_VALUES[i]
    return {"kind": "repair", "symbol_id": None, "repair_id": repair_id,
            "mask": mask, "value": value}


def _source_spec(index, fault):
    value = SOURCE_VALUES[index]
    auth_ok = payload_hash_ok = True
    if fault == "corrupt_mandatory_source" and index == 0:
        value ^= 0xFF
        auth_ok = payload_hash_ok = False
    return {"kind": "source", "symbol_id": index, "repair_id": None,
            "mask": 1 << index, "value": value,
            "auth_ok": auth_ok, "payload_hash_ok": payload_hash_ok}


def _parity_masks(arm, labels):
    order = _label_order(labels)
    if order is None:
        return None
    if arm == "equal_repair":
        groups = {tier: [i for i in range(8) if labels.get(i) == tier]
                  for tier in ("mandatory", "optional")}
        return [sum(1 << i for i in groups[tier][:2])
                for tier in ("mandatory", "optional") if groups[tier]]
    return [sum(1 << i for i in order[start:start + 2])
            for start in (0, 2) if order[start:start + 2]]


def _decode_known(packets, round_number):
    equations = []
    for packet in packets:
        if (not packet["delivered"] or packet["arrival_round"] > round_number
                or not packet["auth_ok"] or not packet["payload_hash_ok"]
                or packet["generation"] != GENERATION
                or packet["window_id"] != WINDOW_ID
                or packet["manifest_ids"] != MANIFEST_IDS
                or packet["manifest_hash"] != MANIFEST_HASH):
            continue
        equations.append([packet["mask"], packet["value"]])
    pivot = 0
    for col in range(8):
        found = next((r for r in range(pivot, len(equations))
                     if equations[r][0] & (1 << col)), None)
        if found is None:
            continue
        equations[pivot], equations[found] = equations[found], equations[pivot]
        for r in range(len(equations)):
            if r != pivot and equations[r][0] & (1 << col):
                equations[r][0] ^= equations[pivot][0]
                equations[r][1] ^= equations[pivot][1]
        pivot += 1
    if any(mask == 0 and value != 0 for mask, value in equations):
        return None
    known = {}
    for mask, value in equations:
        if mask and (mask & (mask - 1)) == 0:
            known[mask.bit_length() - 1] = value
    return known


def _decision_states(packets, context, sent):
    meta_ok = _valid_context(context)
    result = {}
    for name, required in DECISION_CONTRACT.items():
        first = None
        if meta_ok:
            for tick in range(DEADLINE + 1):
                known = _decode_known(packets, tick)
                if known is not None and all(i in known for i in required):
                    first = {"state": "ELIGIBLE", "round": tick,
                             "required_ids": required,
                             "observed_ids": sorted(known),
                             "packets_sent_by_round": sum(1 for p in sent
                                                          if p["send_round"] <= tick)}
                    break
        result[name] = first or {"state": "UNKNOWN" if not meta_ok else "INCOMPLETE",
                                 "round": None, "required_ids": required,
                                 "observed_ids": [], "packets_sent_by_round": None}
        result[name]["name"] = name
        result[name]["receipt_scope"] = ("LIMITED" if name == "status" else
                                         "FULL" if name == "detail" else
                                         "DEPENDENCY_SCOPED")
    return result


def simulate_trace(source_loss_mask, source_delay_mask, extra_loss_mask,
                   extra_delay_mask, arm, fault=None, trace_id="manual"):
    if arm not in ARMS or fault not in (None,) + FAULTS:
        raise ValueError("unknown arm or fault")
    if type(source_loss_mask) is not int or not 0 <= source_loss_mask < 256:
        raise ValueError("source_loss_mask must be an 8-bit integer")
    if source_delay_mask not in DELAY_PROFILES:
        raise ValueError("unknown source delay profile")
    if type(extra_loss_mask) is not int or not 0 <= extra_loss_mask < 4:
        raise ValueError("extra_loss_mask must be a 2-bit integer")
    if type(extra_delay_mask) is not int or not 0 <= extra_delay_mask < 4:
        raise ValueError("extra_delay_mask must be a 2-bit integer")

    context = _context(fault)
    packets, schedule = [], []
    full_loss = source_loss_mask | (extra_loss_mask << 8)
    full_delay = source_delay_mask | (extra_delay_mask << 8)

    def send(slot, spec, send_round):
        lost = bool(full_loss & (1 << slot))
        delay = 2 if full_delay & (1 << slot) else 0
        arrival = None if lost else send_round + delay
        packet = {
            "slot": slot, **spec, "send_round": send_round,
            "lost": lost, "delay": delay, "arrival_round": arrival,
            "delivered": not lost and arrival <= DEADLINE,
            "generation": context["generation"], "window_id": context["window_id"],
            "manifest_ids": context["manifest_ids"],
            "manifest_hash": context["manifest_hash"],
            "importance_hash": context["importance_hash"],
            "auth_ok": spec.get("auth_ok", True),
            "payload_hash_ok": spec.get("payload_hash_ok", True),
        }
        packets.append(packet)
        schedule.append({"slot": slot, "kind": spec["kind"],
                         "symbol_id": spec["symbol_id"],
                         "repair_id": spec["repair_id"], "mask": spec["mask"],
                         "send_round": send_round})

    for i in range(8):
        send(i, _source_spec(i, fault), 0)

    labels = context["importance_labels"]
    fallback = labels is None
    if arm in ("equal_repair", "unequal_repair") and not fallback:
        extra_specs = [(_repair_spec(mask, ix), 0)
                       for ix, mask in enumerate(_parity_masks(arm, labels))][:2]
    else:
        cutoff_present = set()
        if _valid_context(context):
            cutoff_present = {p["symbol_id"] for p in packets
                              if p["kind"] == "source" and p["delivered"]
                              and p["arrival_round"] <= FEEDBACK_CUT
                              and p["auth_ok"] and p["payload_hash_ok"]}
        missing = [i for i in range(8) if i not in cutoff_present]
        if arm == "mandatory_first_retransmit" and labels is not None:
            order = _label_order(labels)
            missing.sort(key=lambda i: order.index(i) if i in order else 99)
        # Invalid importance metadata uses the explicit raw-all fallback.
        extra_specs = [(_source_spec(i, None), FEEDBACK_CUT) for i in missing[:2]]

    for slot, (spec, send_round) in zip((8, 9), extra_specs):
        send(slot, spec, send_round)

    decisions = _decision_states(packets, context, packets)
    final_known = _decode_known(packets, DEADLINE)
    metadata_ok = _valid_context(context)
    whole = bool(metadata_ok and final_known is not None and len(final_known) == 8)
    return {
        "trace_id": trace_id, "source_loss_mask": source_loss_mask,
        "source_delay_mask": source_delay_mask,
        "extra_loss_mask": extra_loss_mask, "extra_delay_mask": extra_delay_mask,
        "loss_mask": full_loss, "delay_mask": full_delay,
        "arm": arm, "fault": fault, "priority_fallback": fallback,
        "generation": context["generation"], "window_id": context["window_id"],
        "manifest_ids": context["manifest_ids"], "manifest_hash": context["manifest_hash"],
        "importance_labels": context["importance_labels"],
        "importance_hash": context["importance_hash"],
        "importance_valid": context["importance_valid"],
        "decision_contract": DECISION_CONTRACT,
        "extra_schedule": schedule[8:], "packets": packets,
        "decisions": decisions,
        "decoded_by_deadline": final_known,
        "whole_window_state": "COMPLETE" if whole else
                              "UNKNOWN" if not metadata_ok else "INCOMPLETE",
        "whole_window_complete": whole,
    }


def _tail_masks(source_loss, profile_index):
    # Deterministic common-random-number outcomes for the two potential tail slots.
    return ((source_loss * 7 + profile_index * 3 + SEED) & 0b11,
            (source_loss * 5 + profile_index + (SEED >> 4)) & 0b11)


def _compare(left, right):
    def value(row):
        d = row["decisions"]["status"]
        return None if d["state"] != "ELIGIBLE" else (
            d["round"], d["packets_sent_by_round"])
    a, b = value(left), value(right)
    if a is None and b is None:
        return "tie"
    if a is None:
        return "right"
    if b is None:
        return "left"
    return "left" if a < b else "right" if b < a else "tie"


def _summary(trace_runs, fault_runs):
    by_arm = {}
    for arm in ARMS:
        rows = [r for r in trace_runs if r["arm"] == arm]
        by_arm[arm] = {
            "trace_count": len(rows),
            "eligible_by_decision": {
                name: sum(r["decisions"][name]["state"] == "ELIGIBLE" for r in rows)
                for name in DECISION_CONTRACT
            },
            "whole_window_complete": sum(r["whole_window_complete"] for r in rows),
            "packets_sent_total": sum(len(r["packets"]) for r in rows),
        }
    comparisons = {}
    pairs = (("unequal_repair", "equal_repair", "unequal_vs_equal"),
             ("mandatory_first_retransmit", "raw_all_retransmit", "priority_vs_raw_all"))
    for left_arm, right_arm, name in pairs:
        left = {r["trace_id"]: r for r in trace_runs if r["arm"] == left_arm}
        right = {r["trace_id"]: r for r in trace_runs if r["arm"] == right_arm}
        counts = {"left_wins": 0, "right_wins": 0, "ties": 0}
        for key in sorted(set(left) & set(right)):
            outcome = _compare(left[key], right[key])
            counts[{"left": "left_wins", "right": "right_wins", "tie": "ties"}[outcome]] += 1
        comparisons[name] = counts
    return {"by_arm": by_arm, "paired_status_comparisons": comparisons,
            "fault_rows": len(fault_runs)}


def build_raw():
    trace_runs, fault_runs = [], []
    for source_loss in range(256):
        for profile_index, profile in enumerate(DELAY_PROFILES):
            extra_loss, extra_delay = _tail_masks(source_loss, profile_index)
            trace_id = f"loss-{source_loss:02x}-delay-{profile:02x}"
            for arm in ARMS:
                trace_runs.append(simulate_trace(source_loss, profile, extra_loss,
                                                 extra_delay, arm, trace_id=trace_id))
    for fault in FAULTS:
        for arm in ARMS:
            fault_runs.append(simulate_trace(0, 0, 0, 0, arm, fault=fault,
                                             trace_id=f"fault-{fault}"))
    protocol = {
        "allocation": ALLOCATION, "seed": SEED,
        "source_values": list(SOURCE_VALUES), "mandatory_ids": list(MANDATORY),
        "optional_ids": list(OPTIONAL), "decision_contract": DECISION_CONTRACT,
        "arms": list(ARMS), "faults": list(FAULTS),
        "delay_profiles": list(DELAY_PROFILES), "deadline": DEADLINE,
        "feedback_cut": FEEDBACK_CUT, "extra_packet_budget": 2,
        "max_packets_per_window": 10, "source_masks": 256,
    }
    raw = {"schema": "fec-importance-5459-t2-raw-v1", "protocol": protocol,
           "trace_runs": trace_runs, "fault_runs": fault_runs}
    raw["summary"] = _summary(trace_runs, fault_runs)
    return raw


def main(output_path):
    raw = build_raw()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(payload)
    print(json.dumps({"allocation": ALLOCATION, "trace_runs": len(raw["trace_runs"]),
                      "fault_runs": len(raw["fault_runs"]),
                      "raw_sha256": hashlib.sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT_JSON")
    main(sys.argv[1])
