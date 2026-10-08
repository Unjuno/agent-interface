"""Independent raw-only reconstruction; imports no candidate or simulator."""
from copy import deepcopy


VALUES = (0x11, 0x23, 0x45, 0x89, 0x5A, 0xC3, 0x6D, 0xF0)
MANDATORY = (0, 2, 5, 7)
OPTIONAL = (1, 3, 4, 6)
CONTRACT = {"status": [0, 2, 5, 7], "detail": list(range(8)),
            "optional_dependent": [0, 2, 5, 6, 7]}
ARMS = ("equal_repair", "unequal_repair", "mandatory_first_retransmit",
        "raw_all_retransmit")
FAULTS = ("wrong_generation", "wrong_window", "incomplete_manifest",
          "stale_manifest", "importance_missing", "critical_mislabeled_optional",
          "corrupt_mandatory_source")
PROFILES = (0, 255, 15, 240)
DEADLINE, CUT = 4, 1
WINDOW, GENERATION = "fec-window-5459-t2-01", 2026100201
MANIFEST_IDS = list(range(8))
MANIFEST_HASH = "sha256:fec-importance-manifest-5459-t2-v1"
IMPORTANCE_HASH = "sha256:fec-importance-labels-5459-t2-v1"
SEED = 54592026100201


def _context(fault):
    generation, window = GENERATION, WINDOW
    ids, digest, rank_digest = list(MANIFEST_IDS), MANIFEST_HASH, IMPORTANCE_HASH
    labels = {i: ("mandatory" if i in MANDATORY else "optional") for i in range(8)}
    valid = True
    if fault == "wrong_generation":
        generation -= 1
    elif fault == "wrong_window":
        window = "stale-window"
    elif fault == "incomplete_manifest":
        ids.remove(6)
    elif fault == "stale_manifest":
        digest = "sha256:stale-manifest"
    elif fault == "importance_missing":
        labels, rank_digest, valid = None, None, False
    elif fault == "critical_mislabeled_optional":
        labels[7] = "optional"
        rank_digest = "sha256:importance-map-with-mislabeled-critical-7"
    return {"generation": generation, "window_id": window,
            "manifest_ids": ids, "manifest_hash": digest,
            "importance_labels": labels, "importance_hash": rank_digest,
            "importance_valid": valid}


def _meta_ok(ctx):
    return (ctx["generation"] == GENERATION and ctx["window_id"] == WINDOW
            and ctx["manifest_ids"] == MANIFEST_IDS
            and ctx["manifest_hash"] == MANIFEST_HASH)


def _priority(labels):
    if labels is None:
        return None
    return [i for tier in ("mandatory", "optional")
            for i in range(8) if labels.get(i) == tier]


def _tail(source_loss, profile_index, fault=None):
    if fault is not None:
        return 0, 0
    return ((source_loss * 7 + profile_index * 3 + SEED) & 0b11,
            (source_loss * 5 + profile_index + (SEED >> 4)) & 0b11)


def _schedule(row, ctx):
    arm, fault = row["arm"], row["fault"]
    labels = ctx["importance_labels"]
    priority = _priority(labels)
    specs = []
    for i, value in enumerate(VALUES):
        actual = value ^ 0xFF if fault == "corrupt_mandatory_source" and i == 0 else value
        specs.append({"kind": "source", "symbol_id": i, "repair_id": None,
                      "mask": 1 << i, "value": actual,
                      "auth_ok": not (fault == "corrupt_mandatory_source" and i == 0),
                      "payload_hash_ok": not (fault == "corrupt_mandatory_source" and i == 0),
                      "send_round": 0})
    source_mask = row["source_loss_mask"]
    source_delay = row["source_delay_mask"]
    valid_ctx = _meta_ok(ctx)
    present = set()
    if valid_ctx:
        for i in range(8):
            lost = bool(source_mask & (1 << i))
            delay = 2 if source_delay & (1 << i) else 0
            bad = fault == "corrupt_mandatory_source" and i == 0
            if not lost and delay <= CUT and not bad:
                present.add(i)

    extras = []
    fallback = labels is None
    if arm in ("equal_repair", "unequal_repair") and not fallback:
        if arm == "equal_repair":
            groups = {tier: [i for i in range(8) if labels.get(i) == tier]
                      for tier in ("mandatory", "optional")}
            masks = [sum(1 << i for i in groups[tier][:2])
                     for tier in ("mandatory", "optional") if groups[tier]]
        else:
            masks = [sum(1 << i for i in priority[start:start + 2])
                     for start in (0, 2) if priority[start:start + 2]]
        for rid, mask in enumerate(masks[:2]):
            value = 0
            for i in range(8):
                if mask & (1 << i):
                    value ^= VALUES[i]
            extras.append({"kind": "repair", "symbol_id": None,
                           "repair_id": rid, "mask": mask, "value": value,
                           "auth_ok": True, "payload_hash_ok": True,
                           "send_round": 0})
    else:
        missing = [i for i in range(8) if i not in present]
        if arm == "mandatory_first_retransmit" and priority is not None:
            positions = {sym: idx for idx, sym in enumerate(priority)}
            missing.sort(key=lambda i: positions.get(i, 99))
        for i in missing[:2]:
            extras.append({"kind": "source", "symbol_id": i, "repair_id": None,
                           "mask": 1 << i, "value": VALUES[i],
                           "auth_ok": True, "payload_hash_ok": True,
                           "send_round": CUT})
    return specs[:8] + extras, fallback


def _decode(rows, tick, ctx):
    if not _meta_ok(ctx):
        return None
    matrix = []
    for packet in rows:
        if (packet["lost"] or not packet["delivered"]
                or packet["arrival_round"] is None or packet["arrival_round"] > tick
                or not packet["auth_ok"] or not packet["payload_hash_ok"]
                or packet["generation"] != GENERATION
                or packet["window_id"] != WINDOW
                or packet["manifest_ids"] != MANIFEST_IDS
                or packet["manifest_hash"] != MANIFEST_HASH):
            continue
        matrix.append([packet["mask"], packet["value"]])
    pivot_row = 0
    for column in range(8):
        selected = next((r for r in range(pivot_row, len(matrix))
                         if matrix[r][0] & (1 << column)), None)
        if selected is None:
            continue
        matrix[pivot_row], matrix[selected] = matrix[selected], matrix[pivot_row]
        for row in range(len(matrix)):
            if row != pivot_row and matrix[row][0] & (1 << column):
                matrix[row][0] ^= matrix[pivot_row][0]
                matrix[row][1] ^= matrix[pivot_row][1]
        pivot_row += 1
    if any(mask == 0 and value != 0 for mask, value in matrix):
        return None
    result = {}
    for mask, value in matrix:
        if mask and mask & (mask - 1) == 0:
            result[mask.bit_length() - 1] = value
    return result


def _expected_decisions(row, ctx):
    results = {}
    for name, required in CONTRACT.items():
        declared = row.get("decision_contract", {}).get(name, [])
        receipt = None
        if _meta_ok(ctx):
            for tick in range(DEADLINE + 1):
                known = _decode(row["packets"], tick, ctx)
                if known is not None and all(i in known for i in required):
                    receipt = {"state": "ELIGIBLE", "round": tick,
                               "required_ids": declared, "observed_ids": sorted(known),
                               "packets_sent_by_round": sum(
                                   packet["send_round"] <= tick for packet in row["packets"])}
                    break
        results[name] = receipt or {
            "state": "UNKNOWN" if not _meta_ok(ctx) else "INCOMPLETE",
            "round": None, "required_ids": declared, "observed_ids": [],
            "packets_sent_by_round": None}
        results[name]["name"] = name
        results[name]["receipt_scope"] = ("LIMITED" if name == "status" else
                                           "FULL" if name == "detail" else
                                           "DEPENDENCY_SCOPED")
    known_final = _decode(row["packets"], DEADLINE, ctx)
    complete = bool(_meta_ok(ctx) and known_final is not None and len(known_final) == 8)
    state = "COMPLETE" if complete else "UNKNOWN" if not _meta_ok(ctx) else "INCOMPLETE"
    return results, known_final, complete, state


def _compare(left, right):
    a, b = left["decisions"]["status"], right["decisions"]["status"]
    a = None if a["state"] != "ELIGIBLE" else (a["round"], a["packets_sent_by_round"])
    b = None if b["state"] != "ELIGIBLE" else (b["round"], b["packets_sent_by_round"])
    if a is None and b is None:
        return "tie"
    if a is None:
        return "right"
    if b is None:
        return "left"
    return "left" if a < b else "right" if b < a else "tie"


def _summary(rows, faults):
    by_arm = {}
    for arm in ARMS:
        subset = [r for r in rows if r["arm"] == arm]
        by_arm[arm] = {
            "trace_count": len(subset),
            "eligible_by_decision": {d: sum(r["decisions"][d]["state"] == "ELIGIBLE"
                                               for r in subset) for d in CONTRACT},
            "whole_window_complete": sum(r["whole_window_complete"] for r in subset),
            "packets_sent_total": sum(len(r["packets"]) for r in subset),
        }
    contrasts = (("unequal_repair", "equal_repair", "unequal_vs_equal"),
                 ("mandatory_first_retransmit", "raw_all_retransmit", "priority_vs_raw_all"))
    paired = {}
    for left_arm, right_arm, name in contrasts:
        left = {r["trace_id"]: r for r in rows if r["arm"] == left_arm}
        right = {r["trace_id"]: r for r in rows if r["arm"] == right_arm}
        counts = {"left_wins": 0, "right_wins": 0, "ties": 0}
        for key in set(left) & set(right):
            outcome = _compare(left[key], right[key])
            counts[{"left": "left_wins", "right": "right_wins", "tie": "ties"}[outcome]] += 1
        paired[name] = counts
    return {"by_arm": by_arm, "paired_status_comparisons": paired,
            "fault_rows": len(faults)}


def _check_row(row, fault, errors):
    prefix = f"{row.get('trace_id')}:{row.get('arm')}"
    arm, source_loss, profile = row.get("arm"), row.get("source_loss_mask"), row.get("source_delay_mask")
    if arm not in ARMS or type(source_loss) is not int or not 0 <= source_loss < 256:
        errors.append(prefix + ":row_identity")
        return
    if profile not in PROFILES or row.get("fault") != fault:
        errors.append(prefix + ":profile_or_fault")
        return
    profile_index = PROFILES.index(profile)
    expected_tail_loss, expected_tail_delay = _tail(source_loss, profile_index, fault)
    if (row.get("extra_loss_mask") != expected_tail_loss
            or row.get("extra_delay_mask") != expected_tail_delay):
        errors.append(prefix + ":tail_channel")
    full_loss = source_loss | (row["extra_loss_mask"] << 8)
    full_delay = profile | (row["extra_delay_mask"] << 8)
    if row.get("loss_mask") != full_loss or row.get("delay_mask") != full_delay:
        errors.append(prefix + ":full_channel")
    ctx = _context(fault)
    if row.get("decision_contract") != CONTRACT:
        errors.append(prefix + ":decision_contract")
    for key, value in ctx.items():
        if row.get(key) != value:
            errors.append(prefix + f":context_{key}")
    schedule, fallback = _schedule(row, ctx)
    if row.get("priority_fallback") is not fallback:
        errors.append(prefix + ":fallback_flag")
    expected = []
    for slot, spec in enumerate(schedule):
        expected.append({"slot": slot, **spec})
    packets = row.get("packets")
    if not isinstance(packets, list) or len(packets) != len(expected) or len(packets) > 10:
        errors.append(prefix + ":packet_count_or_budget")
        return
    for packet, spec in zip(packets, expected):
        for key, value in spec.items():
            if packet.get(key) != value:
                errors.append(prefix + f":schedule_{key}")
        slot = spec["slot"]
        lost = bool(full_loss & (1 << slot))
        delay = 2 if full_delay & (1 << slot) else 0
        arrival = None if lost else spec["send_round"] + delay
        if (packet.get("lost") is not lost or packet.get("delay") != delay
                or packet.get("arrival_round") != arrival
                or packet.get("delivered") is not (not lost and arrival <= DEADLINE)):
            errors.append(prefix + ":channel_event")
        for key in ("generation", "window_id", "manifest_ids", "manifest_hash", "importance_hash"):
            if packet.get(key) != ctx[key]:
                errors.append(prefix + f":packet_{key}")
        if packet.get("auth_ok") is not spec["auth_ok"] or packet.get("payload_hash_ok") is not spec["payload_hash_ok"]:
            errors.append(prefix + ":packet_integrity")
    expected_extra = [{"slot": p["slot"], "kind": p["kind"],
                       "symbol_id": p["symbol_id"], "repair_id": p["repair_id"],
                       "mask": p["mask"], "send_round": p["send_round"]}
                      for p in expected[8:]]
    if row.get("extra_schedule") != expected_extra:
        errors.append(prefix + ":extra_schedule")

    expected_decisions, known, complete, whole_state = _expected_decisions(row, ctx)
    if row.get("decisions") != expected_decisions:
        errors.append(prefix + ":decision_dependency_or_timing")
    if _meta_ok(ctx) and row.get("decoded_by_deadline") != known:
        errors.append(prefix + ":decoded_values")
    if row.get("whole_window_complete") is not complete or row.get("whole_window_state") != whole_state:
        errors.append(prefix + ":whole_window_claim")


def audit_raw(raw):
    errors = []
    if not isinstance(raw, dict) or raw.get("schema") != "fec-importance-5459-t2-raw-v1":
        return ["raw_schema"]
    protocol = raw.get("protocol")
    expected_protocol = {
        "allocation": "FEC-IMPORTANCE-5459-T2-WSLC-20261002-01",
        "seed": SEED, "source_values": list(VALUES), "mandatory_ids": list(MANDATORY),
        "optional_ids": list(OPTIONAL), "decision_contract": CONTRACT,
        "arms": list(ARMS), "faults": list(FAULTS), "delay_profiles": list(PROFILES),
        "deadline": DEADLINE, "feedback_cut": CUT, "extra_packet_budget": 2,
        "max_packets_per_window": 10, "source_masks": 256,
    }
    if protocol != expected_protocol:
        errors.append("protocol_mismatch")
    traces, faults = raw.get("trace_runs"), raw.get("fault_runs")
    expected_trace_keys = {(mask, profile, arm) for mask in range(256)
                           for profile in PROFILES for arm in ARMS}
    seen = set()
    if not isinstance(traces, list) or len(traces) != len(expected_trace_keys):
        return errors + ["trace_grid_incomplete"]
    for row in traces:
        if not isinstance(row, dict):
            errors.append("trace_row_type")
            continue
        key = (row.get("source_loss_mask"), row.get("source_delay_mask"), row.get("arm"))
        if key in seen:
            errors.append("trace_duplicate")
        seen.add(key)
        if key not in expected_trace_keys:
            errors.append("trace_unexpected")
        ix = (key[0] * 4 + PROFILES.index(key[1])) if type(key[0]) is int and key[1] in PROFILES else -1
        expected_id = f"loss-{key[0]:02x}-delay-{key[1]:02x}" if ix >= 0 else None
        if row.get("trace_id") != expected_id:
            errors.append("trace_id")
        _check_row(row, None, errors)
    if seen != expected_trace_keys:
        errors.append("trace_grid_identity")
    expected_fault_keys = {(fault, arm) for fault in FAULTS for arm in ARMS}
    seen_faults = set()
    if not isinstance(faults, list) or len(faults) != len(expected_fault_keys):
        return errors + ["fault_grid_incomplete"]
    for row in faults:
        if not isinstance(row, dict):
            errors.append("fault_row_type")
            continue
        key = (row.get("fault"), row.get("arm"))
        if key in seen_faults:
            errors.append("fault_duplicate")
        seen_faults.add(key)
        if key not in expected_fault_keys:
            errors.append("fault_unexpected")
        if row.get("trace_id") != f"fault-{key[0]}":
            errors.append("fault_trace_id")
        _check_row(row, key[0], errors)
    if seen_faults != expected_fault_keys:
        errors.append("fault_grid_identity")
    expected_summary = _summary(traces, faults)
    if raw.get("summary") != expected_summary:
        errors.append("summary_mismatch")
    return errors


def main(input_path, output_path):
    import hashlib
    import json
    from pathlib import Path
    source = Path(input_path).read_bytes()
    raw = json.loads(source)
    errors = audit_raw(raw)
    report = {"audit": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "errors": errors, "raw_sha256": hashlib.sha256(source).hexdigest(),
              "trace_rows": len(raw.get("trace_runs", [])),
              "fault_rows": len(raw.get("fault_runs", [])),
              "paired_status_comparisons": raw.get("summary", {}).get("paired_status_comparisons")}
    Path(output_path).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditor.py RAW_JSON OUTPUT_REPORT")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
