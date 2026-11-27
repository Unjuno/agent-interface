"""Frozen deterministic candidate for Issue #8651 A01."""
import argparse
import hashlib
import json
import random
from pathlib import Path

def _cells(protocol):
    return [(c["observation"], c["response"]) for c in protocol["design"]["cells"]]

def balanced_orders(protocol, regime_index):
    cells = _cells(protocol)
    rotations = [cells[i:] + cells[:i] for i in range(len(cells))]
    orders = rotations * 2
    seed = protocol["design"]["randomized_order"]["base_seed"] + regime_index
    random.Random(seed).shuffle(orders)
    return orders

def _cue_valid(evidence, at, cue_valid_until):
    return evidence != "urgent" or cue_valid_until is None or at < cue_valid_until

def simulate_cell(protocol, regime, seed, observation, response, order, run_index):
    costs = protocol["simulator"]["observation_costs"]
    cost = float(costs[observation])
    deadline = float(regime["task_deadline"])
    cue_until = regime["cue_valid_until"]
    evidence = regime["evidence"]
    release_delay = float(protocol["simulator"]["input_release_delay"])
    effect_delay = release_delay + float(protocol["simulator"]["persisted_effect_delay_after_release"])
    nominal = float(protocol["simulator"]["fixed_action_nominal_time"])
    reset_id = hashlib.sha256(
        (protocol["freeze_id"] + ":" + regime["regime"] + ":" + str(seed)).encode()
    ).hexdigest()
    row = {
        "attempt_id": "%s-%s-%02d-%s-%s" % (
            protocol["freeze_id"], regime["regime"], seed, observation, response),
        "freeze_id": protocol["freeze_id"], "regime": regime["regime"], "seed": seed,
        "reset_id": reset_id, "observation_level": observation, "response_rule": response,
        "order": list(order), "order_position": order.index((observation, response)),
        "run_index": run_index, "deadline": deadline, "cue_evidence": evidence,
        "cue_valid_until": cue_until, "observation_cost": cost,
        "observations": [], "decisions": [], "actions": [], "trace": [],
        "action_at": None, "input_release_at": None, "persisted_effect_at": None,
        "persisted_effect": False, "terminal_at": None
    }
    seq = 0
    def event(at, kind, **fields):
        nonlocal seq
        row["trace"].append({"at": round(float(at), 6), "seq": seq, "kind": kind, **fields})
        seq += 1

    event(0.0, "reset", reset_id=reset_id)
    if evidence == "urgent":
        event(0.0, "cue_onset", cue="urgent")
    event(0.0, "observation_request", observation_id="obs-1")
    event(0.0, "observation_start", observation_id="obs-1", level=observation)
    event(0.0, "event_loop_block_begin", observation_id="obs-1")
    if response == "FIXED_REPLAY":
        event(0.0, "fixed_decision", basis="precommitted_schedule", observation_id=None)
        event(nominal, "action_scheduled", action="SUBMIT", nominal_at=nominal)
    first_end = cost
    row["observations"].append({
        "id": "obs-1", "requested_at": 0.0, "started_at": 0.0,
        "completed_at": first_end, "evidence": evidence, "level": observation
    })
    event(first_end, "observation_complete", observation_id="obs-1", evidence=evidence)
    event(first_end, "event_loop_block_end", observation_id="obs-1")

    action_at = None
    if response == "FIXED_REPLAY":
        action_at = max(nominal, first_end)
        row["decisions"].append({
            "at": 0.0, "choice": "SUBMIT", "basis": "precommitted_schedule",
            "observation_id": None, "evidence": None
        })
    else:
        first_choice = None
        first_reason = None
        if evidence == "urgent":
            second_end = first_end + cost
            can_confirm = (
                second_end + effect_delay <= deadline
                and _cue_valid(evidence, second_end, cue_until)
            )
            if can_confirm:
                first_choice = "REOBSERVE"
                event(first_end, "reactive_decision", choice=first_choice,
                      basis="obs-1", evidence=evidence)
                row["decisions"].append({
                    "at": first_end, "choice": first_choice, "basis": "observation",
                    "observation_id": "obs-1", "evidence": evidence
                })
                event(first_end, "observation_request", observation_id="obs-2")
                event(first_end, "observation_start", observation_id="obs-2", level=observation)
                event(first_end, "event_loop_block_begin", observation_id="obs-2")
                row["observations"].append({
                    "id": "obs-2", "requested_at": first_end, "started_at": first_end,
                    "completed_at": second_end, "evidence": evidence, "level": observation
                })
                event(second_end, "observation_complete", observation_id="obs-2", evidence=evidence)
                event(second_end, "event_loop_block_end", observation_id="obs-2")
                first_choice = "SUBMIT" if _cue_valid(evidence, second_end, cue_until) else "YIELD"
                first_reason = "fresh_confirmation" if first_choice == "SUBMIT" else "cue_expired"
                event(second_end, "reactive_decision", choice=first_choice,
                      basis="obs-2", evidence=evidence, reason=first_reason)
                row["decisions"].append({
                    "at": second_end, "choice": first_choice, "basis": "fresh_confirmation",
                    "observation_id": "obs-2", "evidence": evidence
                })
                if first_choice == "SUBMIT":
                    action_at = second_end
            else:
                first_choice = "YIELD"
                first_reason = "confirmation_cannot_finish_within_deadline_or_cue_validity"
                event(first_end, "reactive_decision", choice=first_choice,
                      basis="obs-1", evidence=evidence, reason=first_reason)
                row["decisions"].append({
                    "at": first_end, "choice": first_choice, "basis": "observation",
                    "observation_id": "obs-1", "evidence": evidence
                })
        else:
            first_choice = "SUBMIT"
            first_reason = "no_decision_information_use_fixed_schedule"
            event(first_end, "reactive_decision", choice=first_choice,
                  basis="obs-1", evidence=evidence, reason=first_reason)
            row["decisions"].append({
                "at": first_end, "choice": first_choice, "basis": "observation",
                "observation_id": "obs-1", "evidence": evidence
            })
            action_at = max(nominal, first_end)

    if action_at is not None and action_at + effect_delay <= deadline:
        row["action_at"] = round(action_at, 6)
        row["input_release_at"] = round(action_at + release_delay, 6)
        row["persisted_effect_at"] = round(action_at + effect_delay, 6)
        row["persisted_effect"] = True
        row["actions"].append({
            "action": "SUBMIT", "admitted_at": round(action_at, 6),
            "input_down_at": round(action_at, 6),
            "input_up_at": round(action_at + release_delay, 6),
            "release_receipt_at": round(action_at + release_delay, 6),
            "key": "ENTER", "held_after": []
        })
        event(action_at, "action_admission", action="SUBMIT", key="ENTER")
        event(action_at, "input_down", key="ENTER")
        event(action_at + release_delay, "input_up", key="ENTER")
        event(action_at + release_delay, "input_release_measurement",
              key="ENTER", held_after=[])
        event(action_at + effect_delay, "persisted_effect", effect="task_saved")
        row["terminal_at"] = round(action_at + effect_delay, 6)
    else:
        row["persisted_effect"] = False
        row["terminal_at"] = deadline
        event(deadline, "task_deadline", deadline=deadline)
    event(row["terminal_at"], "terminal", persisted_effect=row["persisted_effect"])
    row["trace"].sort(key=lambda item: (item["at"], item["seq"]))
    return row

def run_matrix(protocol):
    rows = []
    run_index = 0
    for regime_index, regime in enumerate(protocol["design"]["seed_blocks"]):
        orders = balanced_orders(protocol, regime_index)
        for seed, order in zip(regime["seeds"], orders):
            for position, (observation, response) in enumerate(order):
                rows.append(simulate_cell(
                    protocol, regime, seed, observation, response,
                    order, run_index))
                rows[-1]["order_position"] = position
                run_index += 1
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default="protocol.json")
    parser.add_argument("--out", default="RAW.jsonl")
    args = parser.parse_args()
    protocol = json.loads(Path(args.protocol).read_text(encoding="utf-8"))
    rows = run_matrix(protocol)
    rendered = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    if args.out == "-":
        print(rendered, end="")
    else:
        Path(args.out).write_text(rendered, encoding="utf-8")

if __name__ == "__main__":
    main()
