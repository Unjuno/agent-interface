"""Independent raw-only audit for Issue #8665 T0; imports no candidate code."""
import argparse
import copy
import hashlib
import itertools
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "PREREGISTRATION.json"
EXPECTED_CELLS = set(itertools.product(
    ("MINIMAL", "LOADED"),
    ("INFORMATIVE", "SHAM"),
    ("FIXED_REPLAY", "OBSERVATION_REACTIVE"),
))
EPS = 1e-8


def shuffled_orders(protocol, regime_index):
    cells = list(itertools.product(
        protocol["design"]["factors"]["observation_load"],
        protocol["design"]["factors"]["cue_content"],
        protocol["design"]["factors"]["response_rule"],
    ))
    square = [cells[offset:] + cells[:offset] for offset in range(len(cells))]
    random.Random(protocol["design"]["base_seed"] + regime_index).shuffle(square)
    return square


def close(actual, expected):
    try:
        return abs(float(actual) - float(expected)) <= EPS
    except (TypeError, ValueError):
        return False


def inspect(protocol, rows):
    errors = []

    def fail(code, detail):
        errors.append({"code": code, "detail": str(detail)})

    regimes = protocol["design"]["regimes"]
    expected_rows = sum(len(item["seeds"]) for item in regimes) * len(EXPECTED_CELLS)
    if len(rows) != expected_rows:
        fail("row_count", f"{len(rows)} != {expected_rows}")
    index = {}
    for row in rows:
        aid = row.get("attempt_id")
        if aid in index:
            fail("duplicate_attempt", aid)
        index[aid] = row

    spec = protocol["simulator"]
    work = spec["observer_work_units"]
    queue = spec["queue_delay_s"]
    service = spec["observation_cost_s"]
    release = spec["input_release_delay_s"]
    persist = spec["persisted_effect_delay_after_release_s"]
    nominal = spec["fixed_action_nominal_s"]
    expected_ids = set()
    expected_index = 0

    for ri, regime in enumerate(regimes):
        orders = shuffled_orders(protocol, ri)
        for si, seed in enumerate(regime["seeds"]):
            expected_order = orders[si]
            reset_id = hashlib.sha256(
                (protocol["freeze_id"] + ":" + regime["name"] + ":" + str(seed)).encode()
            ).hexdigest()
            group = [r for r in rows if r.get("regime") == regime["name"] and r.get("seed") == seed]
            if len(group) != len(EXPECTED_CELLS):
                fail("matched_cells", f"{regime['name']}/{seed}: {len(group)}")
            seen_cells = set()
            seen_positions = set()
            payload_sizes_by_load = {load: set() for load in ("MINIMAL", "LOADED")}
            delivery_times_by_load = {load: set() for load in ("MINIMAL", "LOADED")}
            for row in group:
                load = row.get("observation_load")
                content = row.get("cue_content")
                response = row.get("response_rule")
                cell = (load, content, response)
                expected_aid = f'{protocol["freeze_id"]}-{regime["name"]}-{seed:02d}-{load}-{content}-{response}'
                expected_ids.add(expected_aid)
                if row.get("attempt_id") != expected_aid:
                    fail("attempt_identity_or_factor_label", row.get("attempt_id"))
                if cell not in EXPECTED_CELLS:
                    fail("unknown_factor_level", row.get("attempt_id"))
                if cell in seen_cells:
                    fail("duplicate_cell", row.get("attempt_id"))
                seen_cells.add(cell)
                position = row.get("order_position")
                if not isinstance(position, int) or position not in range(len(EXPECTED_CELLS)):
                    fail("order_position", row.get("attempt_id"))
                    continue
                seen_positions.add(position)
                if tuple(expected_order[position]) != cell:
                    fail("randomized_cell_order", row.get("attempt_id"))
                if row.get("order") != [list(item) for item in expected_order]:
                    fail("order_record", row.get("attempt_id"))
                if row.get("regime_index") != ri or row.get("reset_id") != reset_id:
                    fail("reset_or_regime_identity", row.get("attempt_id"))
                if row.get("run_index") != expected_index + position:
                    fail("run_index", row.get("attempt_id"))
                if row.get("task_deadline_s") != regime["deadline_s"] or row.get("cue_valid_until_s") != regime["cue_valid_until_s"]:
                    fail("regime_timing", row.get("attempt_id"))
                if row.get("ground_truth_cue") != regime["cue_state"]:
                    fail("ground_truth_binding", row.get("attempt_id"))

                obs = row.get("observations", [])
                cue = regime["cue_state"] if content == "INFORMATIVE" else spec["cue_codes"]["SHAM"]
                expected_payload = json.dumps({"cue": cue}, sort_keys=True, separators=(",", ":"))
                block = queue[load] + service[load]
                should_confirm = response == "OBSERVATION_REACTIVE" and cue == "URGENT"
                expected_n = 2 if should_confirm and block * 2 + release + persist <= regime["deadline_s"] and (regime["cue_valid_until_s"] is None or block * 2 <= regime["cue_valid_until_s"]) else 1
                if len(obs) != expected_n:
                    fail("observation_count", row.get("attempt_id"))
                for oi, event in enumerate(obs):
                    requested = 0.0 if oi == 0 else block
                    completed = requested + block
                    if event.get("id") != f"obs-{oi+1}" or event.get("load") != load or event.get("content") != content:
                        fail("observation_factor_identity", row.get("attempt_id"))
                    if not close(event.get("requested_at_s"), requested) or not close(event.get("started_at_s"), requested) or not close(event.get("completed_at_s"), completed):
                        fail("observation_timing", row.get("attempt_id"))
                    if event.get("work_units") != work[load] or not close(event.get("queue_delay_s"), queue[load]) or not close(event.get("service_cost_s"), service[load]):
                        fail("load_operation_check", row.get("attempt_id"))
                    if event.get("payload") != expected_payload or event.get("delivered_cue") != cue:
                        fail("cue_content_or_truth", row.get("attempt_id"))
                    if event.get("payload_bytes") != len(expected_payload.encode("ascii")):
                        fail("payload_size", row.get("attempt_id"))
                    if oi == 0:
                        payload_sizes_by_load[load].add(event.get("payload_bytes"))
                        delivery_times_by_load[load].add(event.get("completed_at_s"))
                if len(obs) == 2 and obs[0].get("payload_bytes") != obs[1].get("payload_bytes"):
                    fail("repeat_payload_size", row.get("attempt_id"))

                decisions = row.get("decisions", [])
                if response == "FIXED_REPLAY":
                    if len(decisions) != 1 or decisions[0].get("basis") != "precommitted_schedule" or decisions[0].get("at_s") != 0.0 or decisions[0].get("observation_id") is not None or decisions[0].get("scheduled_at_s") != nominal:
                        fail("fixed_replay_authority", row.get("attempt_id"))
                    desired = "SUBMIT"
                    final_decision_at = 0.0
                    nominal_action_at = nominal
                else:
                    if any(d.get("basis") != "delivered_cue" for d in decisions):
                        fail("reactive_authority", row.get("attempt_id"))
                    if decisions and decisions[0].get("observation_id") != "obs-1":
                        fail("decision_evidence_reference", row.get("attempt_id"))
                    if decisions and not close(decisions[0].get("at_s"), obs[0].get("completed_at_s")):
                        fail("decision_before_receipt", row.get("attempt_id"))
                    if should_confirm:
                        budget_ok = block * 2 + release + persist <= regime["deadline_s"] and (regime["cue_valid_until_s"] is None or block * 2 <= regime["cue_valid_until_s"])
                        desired = "SUBMIT" if budget_ok and len(obs) == 2 else "YIELD"
                        if desired == "SUBMIT":
                            if len(decisions) != 2 or decisions[0].get("choice") != "REOBSERVE" or decisions[1].get("observation_id") != "obs-2" or decisions[1].get("choice") != "SUBMIT" or not close(decisions[1].get("at_s"), obs[1].get("completed_at_s")):
                                fail("confirmation_decision", row.get("attempt_id"))
                            final_decision_at = obs[1]["completed_at_s"]
                        else:
                            if len(decisions) != 1 or decisions[0].get("choice") != "YIELD":
                                fail("bounded_yield", row.get("attempt_id"))
                            final_decision_at = obs[0]["completed_at_s"]
                        nominal_action_at = max(nominal, final_decision_at)
                    else:
                        desired = "SUBMIT"
                        if len(decisions) != 1 or decisions[0].get("choice") != "SUBMIT":
                            fail("nonurgent_response", row.get("attempt_id"))
                        final_decision_at = obs[0]["completed_at_s"]
                        nominal_action_at = nominal

                action_time = max(nominal_action_at, obs[-1]["completed_at_s"]) if desired == "SUBMIT" else None
                action_admissible = action_time is not None and action_time < regime["deadline_s"] - EPS
                effects = row.get("actions", [])
                if action_admissible:
                    expected_effect = action_time + release + persist
                    if len(effects) != 1:
                        fail("missing_or_duplicate_action", row.get("attempt_id"))
                    else:
                        action = effects[0]
                        times_ok = (
                            close(action.get("admitted_at_s"), action_time)
                            and close(action.get("input_down_at_s"), action_time)
                            and close(action.get("input_up_at_s"), action_time + release)
                            and close(action.get("release_verified_at_s"), action_time + release)
                            and close(action.get("persisted_effect_at_s"), expected_effect)
                        )
                        if action.get("name") != "SUBMIT" or not times_ok or action.get("held_after") != []:
                            fail("input_release_or_effect_receipt", row.get("attempt_id"))
                    on_time = expected_effect <= regime["deadline_s"] + EPS
                    expected_status = "PERSISTED_ON_TIME" if on_time else "PERSISTED_LATE"
                    terminal_at = expected_effect
                    terminal_reason = expected_status
                else:
                    expected_effect = None
                    on_time = False
                    expected_status = "NO_EFFECT_YIELDED" if desired == "YIELD" else "NO_EFFECT_DEADLINE_MISS"
                    terminal_at = min(regime["deadline_s"], obs[-1]["completed_at_s"]) if desired == "YIELD" else regime["deadline_s"]
                    terminal_reason = "CONFIRMATION_CANNOT_FINISH_IN_WINDOW" if desired == "YIELD" else "EVENT_LOOP_RESUMED_AFTER_DEADLINE"
                    if effects:
                        fail("action_after_deadline_or_yield", row.get("attempt_id"))
                if row.get("persisted_effect_at_s") != expected_effect or row.get("persisted_effect_status") != expected_status or row.get("task_success") is not on_time or row.get("deadline_miss") is not (not on_time):
                    fail("task_result", row.get("attempt_id"))
                if not close(row.get("terminal_at_s"), terminal_at) or row.get("terminal_reason") != terminal_reason:
                    fail("terminal_result", row.get("attempt_id"))
                if not close(row.get("queue_latency_s"), obs[0]["completed_at_s"]):
                    fail("queue_latency_metric", row.get("attempt_id"))
                expected_action_latency = None if action_time is None or not action_admissible else action_time - final_decision_at
                if row.get("action_latency_s") is None:
                    if expected_action_latency is not None:
                        fail("action_latency_missing", row.get("attempt_id"))
                elif expected_action_latency is None or not close(row.get("action_latency_s"), expected_action_latency):
                    fail("action_latency_metric", row.get("attempt_id"))
                trace = row.get("trace", [])
                if [event.get("seq") for event in trace] != list(range(len(trace))) or [event.get("at_s") for event in trace] != sorted(event.get("at_s") for event in trace):
                    fail("trace_order", row.get("attempt_id"))
                trace_counts = Counter(event.get("kind") for event in trace)
                trace_decisions = [event for event in trace if event.get("kind") == "decision"]
                if len(trace_decisions) != len(decisions) or any(
                    not close(te.get("at_s"), de.get("at_s"))
                    or te.get("choice") != de.get("choice")
                    or te.get("basis") != de.get("basis")
                    or te.get("observation_id") != de.get("observation_id")
                    for te, de in zip(trace_decisions, decisions)
                ):
                    fail("decision_trace_mismatch", row.get("attempt_id"))
                if action_admissible:
                    if any(trace_counts[kind] != 1 for kind in ("input_down", "input_up", "release_verified", "persisted_effect")) or trace_counts["no_action"]:
                        fail("effect_trace_mismatch", row.get("attempt_id"))
                    expected_trace_times = {
                        "input_down": action_time,
                        "input_up": action_time + release,
                        "release_verified": action_time + release,
                        "persisted_effect": expected_effect,
                    }
                    for kind, expected_time in expected_trace_times.items():
                        event = next((item for item in trace if item.get("kind") == kind), {})
                        if not close(event.get("at_s"), expected_time):
                            fail("effect_trace_timing", row.get("attempt_id"))
                elif any(trace_counts[kind] for kind in ("input_down", "input_up", "release_verified", "persisted_effect")) or trace_counts["no_action"] != 1:
                    fail("no_effect_trace_mismatch", row.get("attempt_id"))
                if not any(event.get("kind") == "terminal" and close(event.get("at_s"), terminal_at) for event in trace):
                    fail("terminal_trace_missing", row.get("attempt_id"))
            for load in payload_sizes_by_load:
                if len(payload_sizes_by_load[load]) != 1:
                    fail("payload_size_not_matched", f"{regime['name']}/{seed}/{load}")
                if len(delivery_times_by_load[load]) != 1:
                    fail("delivery_slot_not_matched", f"{regime['name']}/{seed}/{load}")
            if seen_cells != EXPECTED_CELLS:
                fail("cell_coverage", f"{regime['name']}/{seed}")
            if seen_positions != set(range(len(EXPECTED_CELLS))):
                fail("position_coverage", f"{regime['name']}/{seed}")
            expected_index += len(EXPECTED_CELLS)
    if set(index) != expected_ids:
        fail("attempt_set", f"missing={len(expected_ids-set(index))}, unexpected={len(set(index)-expected_ids)}")

    def rate(regime_name, load=None, content=None, response=None):
        selected = [r for r in rows if r.get("regime") == regime_name
                    and (load is None or r.get("observation_load") == load)
                    and (content is None or r.get("cue_content") == content)
                    and (response is None or r.get("response_rule") == response)]
        return sum(bool(r.get("task_success")) for r in selected) / len(selected) if selected else None

    load_only = rate("load_only_tight_deadline", "LOADED") - rate("load_only_tight_deadline", "MINIMAL")

    def content_effect(regime, load, response):
        return rate(regime, load, "INFORMATIVE", response) - rate(regime, load, "SHAM", response)

    content_response = sum(
        content_effect("transient_urgent_cue", load, "OBSERVATION_REACTIVE")
        - content_effect("transient_urgent_cue", load, "FIXED_REPLAY")
        for load in ("MINIMAL", "LOADED")
    ) / 2
    control_stable = sum(
        content_effect("stable_urgent_cue", load, "OBSERVATION_REACTIVE")
        - content_effect("stable_urgent_cue", load, "FIXED_REPLAY")
        for load in ("MINIMAL", "LOADED")
    ) / 2
    control_no_info = sum(
        content_effect("no_decision_information", load, "OBSERVATION_REACTIVE")
        - content_effect("no_decision_information", load, "FIXED_REPLAY")
        for load in ("MINIMAL", "LOADED")
    ) / 2
    if abs(load_only) >= 0.50 and abs(content_response) >= 0.25:
        classification = "MIXED_SCOPED_FIXTURE"
    elif abs(load_only) >= 0.50:
        classification = "LOAD_DOMINANT_SCOPED_FIXTURE"
    elif abs(content_response) >= 0.25:
        classification = "CONTENT_RESPONSE_DOMINANT_SCOPED_FIXTURE"
    else:
        classification = "NO_REPLICATION_SCOPED_FIXTURE"
    contrasts = {
        "load_only_tight_deadline_loaded_minus_minimal": load_only,
        "transient_urgent_content_response": content_response,
        "stable_control_content_response": control_stable,
        "no_information_control_content_response": control_no_info,
        "classification": classification,
    }
    return errors, contrasts


def mutation_tests(protocol, rows):
    tests = {}
    cases = {}
    cases["dropped_attempt"] = rows[:-1]
    changed = copy.deepcopy(rows)
    changed[0]["cue_content"] = "SHAM" if changed[0]["cue_content"] == "INFORMATIVE" else "INFORMATIVE"
    cases["factor_label_swap"] = changed
    changed = copy.deepcopy(rows)
    changed[0]["observations"][0]["completed_at_s"] += 0.01
    cases["altered_queue_timing"] = changed
    changed = copy.deepcopy(rows)
    target = next(r for r in changed if not r["task_success"])
    target["task_success"] = True
    target["deadline_miss"] = False
    cases["forged_effect"] = changed
    changed = copy.deepcopy(rows)
    target = next(r for r in changed if r["response_rule"] == "OBSERVATION_REACTIVE" and r["observations"])
    target["decisions"][0]["at_s"] = target["observations"][0]["completed_at_s"] - 0.01
    cases["decision_before_receipt"] = changed
    expected = {
        "dropped_attempt": "row_count",
        "factor_label_swap": "attempt_identity_or_factor_label",
        "altered_queue_timing": "observation_timing",
        "forged_effect": "task_result",
        "decision_before_receipt": "decision_before_receipt",
    }
    for name, mutated in cases.items():
        codes = {item["code"] for item in inspect(protocol, mutated)[0]}
        tests[name] = expected[name] in codes
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=ROOT / "results/first-outcome/RAW.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "results/first-outcome/AUDIT.json")
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text())
    rows = [json.loads(line) for line in args.raw.read_text().splitlines() if line.strip()]
    errors, contrasts = inspect(protocol, rows)
    mutations = mutation_tests(protocol, rows)
    payload = {
        "schema": "issue8665-t0-independent-audit-v1",
        "input_rows": len(rows),
        "errors": errors,
        "mutation_rejections": mutations,
        "contrasts": contrasts,
        "status": "PASS_METHOD_SCOPED" if not errors and all(mutations.values()) else "FAIL_AUDIT",
        "claim_limit": "Finite deterministic synthetic fixture only; no live GUI, operating system, model, safety, user tempo, or product inference.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: payload[key] for key in ("input_rows", "status", "mutation_rejections", "contrasts", "errors")}, sort_keys=True))
    if payload["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
