"""Finite synthetic candidate for Issue #8665 T0; no GUI or OS input."""
import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "PREREGISTRATION.json"
LOADS = ("MINIMAL", "LOADED")
CONTENTS = ("INFORMATIVE", "SHAM")
RESPONSES = ("FIXED_REPLAY", "OBSERVATION_REACTIVE")
CELLS = tuple(itertools.product(LOADS, CONTENTS, RESPONSES))
NOMINAL = 0.5
EPS = 1e-9


def cell_orders(protocol, regime_index):
    rotations = [list(CELLS[i:] + CELLS[:i]) for i in range(len(CELLS))]
    random.Random(protocol["design"]["base_seed"] + regime_index).shuffle(rotations)
    return rotations


def observation(protocol, load, content, cue_state, number, requested_at):
    spec = protocol["simulator"]
    code = cue_state if content == "INFORMATIVE" else spec["cue_codes"]["SHAM"]
    start = requested_at
    completed = start + spec["queue_delay_s"][load] + spec["observation_cost_s"][load]
    payload = json.dumps({"cue": code}, sort_keys=True, separators=(",", ":"))
    return {
        "id": f"obs-{number}",
        "load": load,
        "content": content,
        "requested_at_s": requested_at,
        "started_at_s": start,
        "completed_at_s": completed,
        "work_units": spec["observer_work_units"][load],
        "queue_delay_s": spec["queue_delay_s"][load],
        "service_cost_s": spec["observation_cost_s"][load],
        "payload": payload,
        "payload_bytes": len(payload.encode("ascii")),
        "delivered_cue": code,
    }


def make_attempt(protocol, regime, regime_index, seed, order, position, run_index):
    load, content, response = order[position]
    reset_id = hashlib.sha256(
        f'{protocol["freeze_id"]}:{regime["name"]}:{seed}'.encode("utf-8")
    ).hexdigest()
    observations = [observation(protocol, load, content, regime["cue_state"], 1, 0.0)]
    first_end = observations[0]["completed_at_s"]
    decisions = []
    actions = []
    cue_valid = regime["cue_valid_until_s"]
    deadline = regime["deadline_s"]
    release_delay = protocol["simulator"]["input_release_delay_s"]
    persist_delay = protocol["simulator"]["persisted_effect_delay_after_release_s"]
    choice = "SUBMIT"
    basis = "precommitted_schedule" if response == "FIXED_REPLAY" else "delivered_cue"
    decision_at = 0.0 if response == "FIXED_REPLAY" else first_end
    scheduled_at = NOMINAL
    terminal_reason = "TASK_EFFECT_PERSISTED"

    if response == "OBSERVATION_REACTIVE" and observations[0]["delivered_cue"] == "URGENT":
        can_confirm = first_end + observations[0]["queue_delay_s"] + observations[0]["service_cost_s"] + release_delay + persist_delay <= deadline + EPS
        can_preserve = cue_valid is None or first_end + observations[0]["queue_delay_s"] + observations[0]["service_cost_s"] <= cue_valid + EPS
        if can_confirm and can_preserve:
            decisions.append({"at_s": decision_at, "basis": basis, "observation_id": "obs-1", "choice": "REOBSERVE"})
            observations.append(observation(protocol, load, content, regime["cue_state"], 2, first_end))
            decision_at = observations[-1]["completed_at_s"]
            scheduled_at = max(NOMINAL, decision_at)
            if observations[-1]["delivered_cue"] != "URGENT":
                choice = "YIELD"
                terminal_reason = "CUE_CHANGED_TO_NONURGENT"
        else:
            choice = "YIELD"
            terminal_reason = "CONFIRMATION_CANNOT_FINISH_IN_WINDOW"
            decisions.append({"at_s": decision_at, "basis": basis, "observation_id": "obs-1", "choice": "YIELD"})
        if choice == "SUBMIT":
            decisions.append({"at_s": decision_at, "basis": basis, "observation_id": "obs-2", "choice": "SUBMIT"})
    elif response == "OBSERVATION_REACTIVE":
        decisions.append({"at_s": decision_at, "basis": basis, "observation_id": "obs-1", "choice": "SUBMIT"})
    else:
        decisions.append({"at_s": decision_at, "basis": basis, "observation_id": None, "choice": "SUBMIT", "scheduled_at_s": scheduled_at})

    if choice == "SUBMIT":
        admission = max(scheduled_at, observations[-1]["completed_at_s"])
        effect_at = admission + release_delay + persist_delay
        if admission < deadline - EPS:
            actions.append({
                "name": "SUBMIT",
                "admitted_at_s": admission,
                "input_down_at_s": admission,
                "input_up_at_s": admission + release_delay,
                "release_verified_at_s": admission + release_delay,
                "held_after": [],
                "persisted_effect_at_s": effect_at,
            })
            task_success = effect_at <= deadline + EPS
            effect_status = "PERSISTED_ON_TIME" if task_success else "PERSISTED_LATE"
            terminal_at = effect_at
            terminal_reason = effect_status
        else:
            task_success = False
            effect_status = "NO_EFFECT_DEADLINE_MISS"
            terminal_at = deadline
            terminal_reason = "EVENT_LOOP_RESUMED_AFTER_DEADLINE"
            admission = None
            effect_at = None
    else:
        task_success = False
        effect_status = "NO_EFFECT_YIELDED"
        terminal_at = min(deadline, observations[-1]["completed_at_s"])
        admission = None
        effect_at = None

    trace = [{"at_s": 0.0, "kind": "attempt_start"}]
    for obs in observations:
        trace.extend([
            {"at_s": obs["requested_at_s"], "kind": "observation_request", "observation_id": obs["id"]},
            {"at_s": obs["started_at_s"], "kind": "observation_start", "observation_id": obs["id"]},
            {"at_s": obs["completed_at_s"], "kind": "observation_complete", "observation_id": obs["id"], "cue": obs["delivered_cue"]},
        ])
    for decision in decisions:
        trace.append({"at_s": decision["at_s"], "kind": "decision", "choice": decision["choice"], "basis": decision["basis"], "observation_id": decision["observation_id"]})
    if actions:
        action = actions[0]
        trace.extend([
            {"at_s": action["input_down_at_s"], "kind": "input_down", "action": "SUBMIT"},
            {"at_s": action["input_up_at_s"], "kind": "input_up", "action": "SUBMIT"},
            {"at_s": action["release_verified_at_s"], "kind": "release_verified", "held_after": []},
            {"at_s": action["persisted_effect_at_s"], "kind": "persisted_effect", "on_time": task_success},
        ])
    else:
        trace.append({"at_s": terminal_at, "kind": "no_action", "reason": terminal_reason})
    trace.append({"at_s": terminal_at, "kind": "terminal", "reason": terminal_reason})
    trace.sort(key=lambda event: (event["at_s"], event["kind"]))
    for seq, event in enumerate(trace):
        event["seq"] = seq

    payload_sizes = {obs["payload_bytes"] for obs in observations}
    return {
        "attempt_id": f'{protocol["freeze_id"]}-{regime["name"]}-{seed:02d}-{load}-{content}-{response}',
        "run_index": run_index,
        "regime": regime["name"],
        "regime_index": regime_index,
        "seed": seed,
        "reset_id": reset_id,
        "order_position": position,
        "order": [list(cell) for cell in order],
        "observation_load": load,
        "cue_content": content,
        "response_rule": response,
        "task_deadline_s": deadline,
        "cue_valid_until_s": cue_valid,
        "ground_truth_cue": regime["cue_state"],
        "observations": observations,
        "observation_payload_bytes": sorted(payload_sizes),
        "decisions": decisions,
        "actions": actions,
        "persisted_effect_status": effect_status,
        "persisted_effect_at_s": effect_at,
        "task_success": task_success,
        "deadline_miss": not task_success,
        "queue_latency_s": observations[0]["completed_at_s"],
        "action_latency_s": None if admission is None else admission - decision_at,
        "terminal_at_s": terminal_at,
        "terminal_reason": terminal_reason,
        "trace": trace,
    }


def build(protocol):
    attempts = []
    run_index = 0
    for regime_index, regime in enumerate(protocol["design"]["regimes"]):
        orders = cell_orders(protocol, regime_index)
        for seed_index, seed in enumerate(regime["seeds"]):
            order = orders[seed_index]
            for position in range(len(order)):
                attempts.append(make_attempt(protocol, regime, regime_index, seed, order, position, run_index))
                run_index += 1
    return attempts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results/first-outcome/RAW.jsonl")
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text())
    if protocol["source_main_sha"] != "23d1807ffad8359e0f89421ee2b9bf5783c9d5f4":
        raise SystemExit("HOLD: frozen main SHA mismatch")
    codes = [protocol["simulator"]["cue_codes"][key] for key in ("URGENT", "NEUTRL", "SHAM")]
    sizes = {len(json.dumps({"cue": code}, sort_keys=True, separators=(",", ":")).encode("ascii")) for code in codes}
    if len(sizes) != 1:
        raise SystemExit("HOLD: payload byte sizes are not matched")
    if args.output.exists():
        raise SystemExit("STOP: first-outcome path already exists")
    attempts = build(protocol)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        for attempt in attempts:
            stream.write(json.dumps(attempt, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"attempts={len(attempts)} output={args.output}")


if __name__ == "__main__":
    main()
