#!/usr/bin/env python3
"""Independent raw-only checker; no import of candidate model.py."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


EFFECT_VALUES = ("NONE", "APPLIED", "UNKNOWN")
DELIVERY_VALUES = ("KNOWN", "UNKNOWN")
INPUT_VALUES = ("RELEASED", "HELD", "UNKNOWN")
TARGET_VALUES = ("CURRENT", "STALE", "UNKNOWN")
FAIR_LOCAL_ORDERS = tuple(itertools.permutations(("sync_planner", "sync_broker", "sync_actuator", "quarantine_claim", "trusted_release")))
MESSAGE_ORDERS = tuple(sorted(set(itertools.permutations(("OLD_CLAIM", "ACK", "RELEASE_ACK", "OLD_CLAIM")))))


def expected_configurations():
    rows = []
    for p, b, a, pending, delivery, effect, input_state, release_ok, effect_readable, target, auth, persisted in itertools.product(
        (0, 1), (0, 1), (0, 1), (False, True), DELIVERY_VALUES, EFFECT_VALUES, INPUT_VALUES,
        (False, True), (False, True), TARGET_VALUES, (False, True), (False, True)
    ):
        rows.append({"epochs": [p, b, a], "pending_claim": pending, "delivery_state": delivery, "effect": effect,
                     "input_state": input_state, "release_oracle": release_ok,
                     "effect_oracle": effect_readable, "target_state": target,
                     "new_authorization": auth, "persisted_authority": persisted})
    return rows


def replay(initial, order):
    epochs = list(initial["epochs"])
    fenced = True  # Restart closes volatile admission before persisted state is loaded.
    fence_generation = max(epochs) + 1
    quarantined = False
    release_proof = False
    input_state = initial["input_state"]
    admission_enabled = False
    admission_count = 0
    for event in order:
        if event == "sync_planner":
            epochs[0] = fence_generation
        elif event == "sync_broker":
            epochs[1] = fence_generation
        elif event == "sync_actuator":
            epochs[2] = fence_generation
        elif event == "quarantine_claim":
            quarantined = initial["pending_claim"] or initial["delivery_state"] == "UNKNOWN"
        elif event == "trusted_release" and initial["release_oracle"]:
            input_state = "RELEASED"
            release_proof = True
        if admission_enabled:
            admission_count += 1
    claim_safe = quarantined or (not initial["pending_claim"] and initial["delivery_state"] == "KNOWN")
    safe = (fenced and not admission_enabled and admission_count == 0 and claim_safe
            and epochs == [fence_generation] * 3 and release_proof and input_state == "RELEASED")
    effect_ok = initial["effect_oracle"] and initial["effect"] != "UNKNOWN"
    target_ok = initial["target_state"] == "CURRENT"
    resume = safe and effect_ok and target_ok and initial["new_authorization"]
    return {"safe": safe, "resume": resume, "admissions": admission_count,
            "destination": "RESUMABLE_CURRENT" if resume else ("SAFE_QUIESCENT_UNKNOWN" if safe else "HOLD_UNKNOWN_INPUT"),
            "bound": 1 + len(order)}


def message_probe(order):
    # Old-generation messages cannot create authority or physical postcondition proofs.
    gate_closed = True
    admissions = 0
    release_proofs = 0
    current_generation = 2
    for message in order:
        delivered_generation = 0
        if not gate_closed and delivered_generation == current_generation and message == "OLD_CLAIM":
            admissions += 1
        # ACK/RELEASE_ACK are not independent physical-state evidence in this frozen model.
        if message == "RELEASE_ACK" and not gate_closed and delivered_generation == current_generation:
            release_proofs += 1
    return admissions, release_proofs


def unsafe_naive(initial):
    if not initial["persisted_authority"] or not initial["pending_claim"]:
        return False
    next_generation = max(initial["epochs"]) + 1
    old_generation = max(initial["epochs"]) < next_generation
    return initial["delivery_state"] == "UNKNOWN" or initial["effect"] in ("APPLIED", "UNKNOWN") or old_generation


def valid_initial_shape(config):
    keys = {"epochs", "pending_claim", "delivery_state", "effect", "input_state", "release_oracle", "effect_oracle", "target_state", "new_authorization", "persisted_authority"}
    if not isinstance(config, dict) or set(config) != keys:
        return False
    if not isinstance(config["epochs"], list) or len(config["epochs"]) != 3 or any(type(x) is not int or x not in (0, 1) for x in config["epochs"]):
        return False
    if any(type(config[k]) is not bool for k in ("pending_claim", "release_oracle", "effect_oracle", "new_authorization", "persisted_authority")):
        return False
    return (config["delivery_state"] in DELIVERY_VALUES and config["effect"] in EFFECT_VALUES
            and config["input_state"] in INPUT_VALUES and config["target_state"] in TARGET_VALUES)


def audit_records(records):
    errors = []
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        return {"status": "FAIL_METHOD", "states": len(records) if isinstance(records, list) else 0,
                "expected_states": 13824, "errors": ["raw_record_shape"]}
    expected = expected_configurations()
    if len(records) != len(expected):
        return {"status": "FAIL_METHOD", "states": len(records), "expected_states": len(expected), "errors": ["state_count"]}
    for index, (record, config) in enumerate(zip(records, expected)):
        record_keys = {"state_id", "initial", "fair_schedules", "all_schedules_safe", "convergence_matches_release_assumption", "safe_state_reached", "destination", "max_steps", "resumable", "message_orders", "message_admissions", "message_forged_release_proofs", "naive_unsafe_dispatch", "permanent_stop_progress"}
        if (not isinstance(record, dict) or set(record) != record_keys
                or type(record.get("state_id")) is not int or record["state_id"] != index
                or not valid_initial_shape(record.get("initial")) or record["initial"] != config):
            errors.append(f"state_inventory:{index}")
            break
        expected_outcomes = [replay(config, order) for order in FAIR_LOCAL_ORDERS]
        expected_msg = [message_probe(order) for order in MESSAGE_ORDERS]
        expected_values = {
            "fair_schedules": len(FAIR_LOCAL_ORDERS),
            "all_schedules_safe": all(out["admissions"] == 0 for out in expected_outcomes),
            "convergence_matches_release_assumption": all(out["safe"] for out in expected_outcomes) == config["release_oracle"],
            "safe_state_reached": all(out["safe"] for out in expected_outcomes),
            "destination": expected_outcomes[0]["destination"],
            "max_steps": max(out["bound"] for out in expected_outcomes),
            "resumable": expected_outcomes[0]["resume"],
            "message_orders": len(MESSAGE_ORDERS),
            "message_admissions": max(out[0] for out in expected_msg),
            "message_forged_release_proofs": max(out[1] for out in expected_msg),
            "naive_unsafe_dispatch": unsafe_naive(config),
            "permanent_stop_progress": False,
        }
        if any(type(record.get(key)) is not type(value) or record.get(key) != value for key, value in expected_values.items()):
            errors.append(f"replay_mismatch:{index}")
            break
        if record["destination"] == "RESUMABLE_CURRENT" and not (
            config["release_oracle"] and config["effect_oracle"] and config["effect"] != "UNKNOWN"
            and config["target_state"] == "CURRENT" and config["new_authorization"]
        ):
            errors.append(f"resume_without_independent_evidence:{index}")
            break
    counts = {}
    for row in records:
        d = row.get("destination")
        counts[d] = counts.get(d, 0) + 1
    unsafe_naive_count = sum(row.get("naive_unsafe_dispatch") is True for row in records)
    if not unsafe_naive_count:
        errors.append("naive_counterexample_missing")
    if any(row.get("all_schedules_safe") is not True for row in records):
        errors.append("unsafe_reconciler_schedule")
    if any(row.get("fair_schedules") != 120 or row.get("max_steps") != 6 for row in records):
        errors.append("fair_schedule_or_bound")
    if any(row.get("message_admissions") or row.get("message_forged_release_proofs") for row in records):
        errors.append("message_gate_violation")
    if any(row.get("permanent_stop_progress") for row in records):
        errors.append("permanent_stop_progress_unexpected")
    return {"status": "METHOD_PASS_SCOPED" if not errors else "FAIL_METHOD",
            "states": len(records), "fair_schedules_per_state": 120,
            "total_fair_traces": len(records) * 120, "naive_unsafe_states": unsafe_naive_count,
            "destinations": counts, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--out")
    args = parser.parse_args()
    with Path(args.raw).open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    result = audit_records(rows)
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if result["status"] == "METHOD_PASS_SCOPED" else 1)


if __name__ == "__main__":
    main()
