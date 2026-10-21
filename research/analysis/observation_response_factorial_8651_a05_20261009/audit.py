"""Independent raw-only audit for Issue #8651 A01."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

CELLS = [
    ("SHAM_MINIMAL", "FIXED_REPLAY"),
    ("ACTIVE_LOADED", "FIXED_REPLAY"),
    ("SHAM_MINIMAL", "OBSERVATION_REACTIVE"),
    ("ACTIVE_LOADED", "OBSERVATION_REACTIVE"),
]

def orders(protocol, regime_index):
    import random
    cells = [(c["observation"], c["response"]) for c in protocol["design"]["cells"]]
    rotations = [cells[i:] + cells[:i] for i in range(len(cells))]
    result = rotations * 2
    random.Random(protocol["design"]["randomized_order"]["base_seed"] + regime_index).shuffle(result)
    return result

def inspect(protocol, rows):
    errors = []
    def err(code, detail):
        errors.append({"code": code, "detail": detail})
    blocks = protocol["design"]["seed_blocks"]
    expected_n = sum(len(b["seeds"]) for b in blocks) * 4
    if len(rows) != expected_n:
        err("row_count", "%s != %s" % (len(rows), expected_n))
    by_id = {}
    for r in rows:
        aid = r.get("attempt_id")
        if aid in by_id:
            err("duplicate_attempt", str(aid))
        by_id[aid] = r
    obs_cost = protocol["simulator"]["observation_costs"]
    rel = float(protocol["simulator"]["input_release_delay"])
    persist = float(protocol["simulator"]["persisted_effect_delay_after_release"])
    for bi, block in enumerate(blocks):
        expected_orders = orders(protocol, bi)
        for si, seed in enumerate(block["seeds"]):
            order = expected_orders[si]
            expected_reset = hashlib.sha256(
                (protocol["freeze_id"] + ":" + block["regime"] + ":" + str(seed)).encode()
            ).hexdigest()
            group = [r for r in rows if r.get("regime") == block["regime"] and r.get("seed") == seed]
            if len(group) != 4:
                err("matched_cells", "%s/%s has %d" % (block["regime"], seed, len(group)))
            positions = set()
            observed_cells = set()
            for r in group:
                pos = r.get("order_position")
                if not isinstance(pos, int) or pos not in range(4):
                    err("order_position", str(r.get("attempt_id")))
                    continue
                positions.add(pos)
                pair = (r.get("observation_level"), r.get("response_rule"))
                observed_cells.add(pair)
                if pair != tuple(order[pos]):
                    err("swapped_cell_label", "%s position %s" % (r.get("attempt_id"), pos))
                if r.get("order") != [list(c) for c in order]:
                    err("order_mismatch", str(r.get("attempt_id")))
                if r.get("reset_id") != expected_reset:
                    err("reset_mismatch", str(r.get("attempt_id")))
                if r.get("run_index") != (sum(len(x["seeds"]) for x in blocks[:bi]) * 4 + si * 4 + pos):
                    err("run_index", str(r.get("attempt_id")))
                obs = r.get("observations", [])
                expected_obs_n = 2 if (r.get("response_rule") == "OBSERVATION_REACTIVE" and block["evidence"] == "urgent" and float(r.get("observation_cost", -1)) * 2 + rel + persist <= float(block["task_deadline"]) and (block.get("cue_valid_until") is None or float(r.get("observation_cost", 0)) * 2 < float(block["cue_valid_until"]))) else 1
                if len(obs) != expected_obs_n:
                    err("observation_count", str(r.get("attempt_id")))
                for oi, o in enumerate(obs):
                    expected_start = oi * float(r.get("observation_cost", 0))
                    if o.get("id") != "obs-%d" % (oi + 1) or abs(float(o.get("requested_at", -99)) - expected_start) > 1e-8 or abs(float(o.get("started_at", -99)) - expected_start) > 1e-8 or abs(float(o.get("completed_at", -99)) - (expected_start + float(r.get("observation_cost", 0)))) > 1e-8:
                        err("observation_timing", str(r.get("attempt_id")))
                    if o.get("level") != pair[0] or o.get("evidence") != block["evidence"]:
                        err("observation_source", str(r.get("attempt_id")))
                decisions = r.get("decisions", [])
                for d in decisions:
                    if d.get("basis") == "precommitted_schedule":
                        if pair[1] != "FIXED_REPLAY" or d.get("at") != 0 or d.get("observation_id") is not None:
                            err("fixed_decision_authority", str(r.get("attempt_id")))
                    else:
                        ref = next((o for o in obs if o.get("id") == d.get("observation_id")), None)
                        if ref is None:
                            err("decision_evidence_missing", str(r.get("attempt_id")))
                        elif float(d.get("at", -1)) + 1e-8 < float(ref.get("completed_at", 1e9)):
                            err("decision_precedes_observation_completion", str(r.get("attempt_id")))
                trace = r.get("trace", [])
                times = [float(e.get("at", -1)) for e in trace]
                if times != sorted(times) or sorted(e.get("seq") for e in trace) != list(range(len(trace))):
                    err("trace_order", str(r.get("attempt_id")))
                if len(r.get("actions", [])) > 1:
                    err("action_count", str(r.get("attempt_id")))
                action = r.get("actions", [])
                effect = r.get("persisted_effect")
                if effect:
                    if len(action) != 1 or r.get("persisted_effect_at") is None:
                        err("forged_effect_receipt", str(r.get("attempt_id")))
                    else:
                        a = action[0]
                        at = float(a.get("admitted_at", -99))
                        release_at = at + rel
                        effect_at = release_at + persist
                        if abs(float(a.get("input_down_at", -99)) - at) > 1e-8 or abs(float(a.get("input_up_at", -99)) - release_at) > 1e-8 or abs(float(a.get("release_receipt_at", -99)) - release_at) > 1e-8 or a.get("held_after") != [] or abs(float(r.get("persisted_effect_at", -99)) - effect_at) > 1e-8 or effect_at > float(block["task_deadline"]) + 1e-8:
                            err("forged_effect_receipt", str(r.get("attempt_id")))
                elif action or r.get("persisted_effect_at") is not None:
                    err("effect_action_mismatch", str(r.get("attempt_id")))
                if bool(effect) != any(e.get("kind") == "persisted_effect" for e in trace):
                    err("effect_trace_mismatch", str(r.get("attempt_id")))
                if r.get("terminal_at") is None or not any(e.get("kind") == "terminal" for e in trace):
                    err("terminal_missing", str(r.get("attempt_id")))
            if positions != {0, 1, 2, 3}:
                err("order_balance", "%s/%s" % (block["regime"], seed))
            if observed_cells != set(CELLS):
                err("cell_coverage", "%s/%s" % (block["regime"], seed))
    expected_ids = set()
    for block in blocks:
        for seed in block["seeds"]:
            for a, b in CELLS:
                expected_ids.add("%s-%s-%02d-%s-%s" % (protocol["freeze_id"], block["regime"], seed, a, b))
    if set(by_id) != expected_ids:
        err("attempt_ledger_mismatch", "missing=%d unexpected=%d" % (len(expected_ids-set(by_id)), len(set(by_id)-expected_ids)))
    if len(rows) == expected_n:
        for block in blocks:
            def rate(obs, response):
                selected = [r for r in rows if r.get("regime") == block["regime"] and r.get("observation_level") == obs and r.get("response_rule") == response]
                return sum(bool(r.get("persisted_effect")) for r in selected) / len(selected) if selected else None
            fixed = rate("ACTIVE_LOADED", "FIXED_REPLAY") - rate("SHAM_MINIMAL", "FIXED_REPLAY")
            reactive = rate("ACTIVE_LOADED", "OBSERVATION_REACTIVE") - rate("SHAM_MINIMAL", "OBSERVATION_REACTIVE")
            block["_contrasts"] = {"fixed_active_minus_sham": fixed, "reactive_active_minus_sham": reactive, "difference_in_differences": reactive-fixed}
    return errors

def run_self_tests(protocol, rows):
    outcomes = {}
    mutations = {}
    mutations["dropped_attempt"] = rows[:-1]
    swapped = copy.deepcopy(rows)
    swapped[0]["observation_level"] = "ACTIVE_LOADED" if swapped[0]["observation_level"] == "SHAM_MINIMAL" else "SHAM_MINIMAL"
    mutations["swapped_cell_label"] = swapped
    forged = copy.deepcopy(rows)
    target = next(r for r in forged if not r["persisted_effect"])
    target["persisted_effect"] = True
    mutations["forged_effect"] = forged
    late = copy.deepcopy(rows)
    target = next(r for r in late if r["regime"] == "deadline_transient_cue" and r["response_rule"] == "OBSERVATION_REACTIVE" and r["observation_level"] == "SHAM_MINIMAL")
    target["observations"][0]["completed_at"] += 0.01
    for event in target["trace"]:
        if event["kind"] == "observation_complete" and event.get("observation_id") == "obs-1":
            event["at"] += 0.01
    late_test = inspect(copy.deepcopy(protocol), late)
    outcomes["observation_after_decision"] = "decision_precedes_observation_completion" in {e["code"] for e in late_test}
    outcomes["dropped_attempt"] = "row_count" in {e["code"] for e in inspect(copy.deepcopy(protocol), mutations["dropped_attempt"])}
    outcomes["swapped_cell_label"] = "swapped_cell_label" in {e["code"] for e in inspect(copy.deepcopy(protocol), mutations["swapped_cell_label"])}
    outcomes["forged_effect"] = "forged_effect_receipt" in {e["code"] for e in inspect(copy.deepcopy(protocol), mutations["forged_effect"])}
    return outcomes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    protocol = json.loads(Path(a.protocol).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(a.raw).read_text(encoding="utf-8").splitlines() if line]
    errors = inspect(protocol, rows)
    primary_contrasts = copy.deepcopy({b["regime"]: b.get("_contrasts") for b in protocol["design"]["seed_blocks"]})
    controls = run_self_tests(protocol, rows) if a.self_test and not errors else {}
    controls_pass = len(controls) == 4 and all(controls.values())
    status = "PASS_METHOD_SCOPED" if not errors and controls_pass else "STOP_AUDIT_OR_CORRUPTION_CONTROL"
    contrasts = primary_contrasts
    positive = contrasts.get("deadline_transient_cue", {}).get("difference_in_differences")
    controls_ok = all(abs(contrasts.get(name, {}).get("difference_in_differences", 999)) <= protocol["gates"]["control_interaction_max_abs"] for name in ("stable_no_transient_deadline", "no_decision_information"))
    interaction_ok = positive is not None and abs(positive) >= protocol["gates"]["positive_interaction_min_abs"] and controls_ok
    result = {"schema":"issue8651-independent-audit-v1","status":status,"interaction_status":"INTERACTION_SUPPORTED_SCOPED" if status=="PASS_METHOD_SCOPED" and interaction_ok else ("NO_INTERACTION_SCOPED" if status=="PASS_METHOD_SCOPED" else "UNCERTAIN"),"row_count":len(rows),"errors":errors,"mutation_controls":controls,"contrasts":contrasts,"claim_boundary":"Synthetic deterministic mechanism only; not GUI, model, safety, causal mediation, or user-tempo evidence."}
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if a.out == "-":
        print(rendered, end="")
    else:
        Path(a.out).write_text(rendered, encoding="utf-8")
    if status != "PASS_METHOD_SCOPED":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
