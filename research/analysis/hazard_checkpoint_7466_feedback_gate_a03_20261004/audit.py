#!/usr/bin/env python3
"""Independent replay of A02 candidate decisions, event traces and mutations."""
import copy
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "formal_01"


def readj(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_fit(training):
    fit = training["fit"]
    counts = Counter(r["symbol"] for r in fit)
    hits = Counter(r["symbol"] for r in fit if r["interrupted"])
    probs = {s: hits[s] / counts[s] for s in sorted(counts)}
    base = sum(r["interrupted"] for r in fit) / len(fit)
    val = training["validation"]
    bm = sum((probs[r["symbol"]] - r["interrupted"]) ** 2 for r in val) / len(val)
    bb = sum((base - r["interrupted"]) ** 2 for r in val) / len(val)
    vc = Counter(r["symbol"] for r in val)
    return probs, base, {"p_by_signal": probs, "base_rate": base, "brier_model_validation": bm,
                         "brier_base_validation": bb, "calibration_pass": all(vc[s] >= 100 for s in ("HIGH", "LOW")) and bm < bb,
                         "validation_counts": dict(vc)}


def simulate_baseline(case, labels, cp_cost, replay_cost, fixed_interval, event_interval, kind):
    progress = durable = checkpoints = lost = wall = 0
    next_event = event_interval
    for t, y in enumerate(labels):
        if progress >= case["task_units"]:
            break
        legal = bool(case["legal"][t])
        if kind == "fixed":
            take = legal and progress - durable >= fixed_interval
        else:
            take = legal and progress >= next_event
        if take:
            durable = progress
            checkpoints += 1
            if kind == "event":
                next_event = ((progress // event_interval) + 1) * event_interval
        progress += 1
        wall = t + 1
        if y and progress < case["task_units"]:
            lost += (progress - durable) * replay_cost
            progress = durable
    completed = progress >= case["task_units"]
    if completed:
        durable = progress
    return {"completed": completed, "final_effects": progress if completed else durable,
            "expected_effects": case["task_units"], "checkpoint_count": checkpoints,
            "checkpoint_cost": checkpoints * cp_cost, "lost_work_cost": lost,
            "total_cost": checkpoints * cp_cost + lost, "wall_ticks": wall}


def clairvoyant_lower_bound(case, labels, cp_cost, replay_cost):
    """Exact finite-horizon DP with future labels; audit-only unattainable bound."""
    states = {(0, 0): 0}
    for t, y in enumerate(labels):
        nxt = dict(states)
        for (progress, durable), cost in states.items():
            if progress >= case["task_units"]:
                continue
            choices = (False, True) if case["legal"][t] and progress > durable else (False,)
            for checkpoint in choices:
                d = progress if checkpoint else durable
                c = cost + (cp_cost if checkpoint else 0)
                p = progress + 1
                if y and p < case["task_units"]:
                    c += (p - d) * replay_cost
                    p = d
                key = (p, d)
                if c < nxt.get(key, math.inf):
                    nxt[key] = c
        states = nxt
    done = [cost for (progress, _durable), cost in states.items() if progress >= case["task_units"]]
    return min(done) if done else None


def policy_decisions(case, labels, probs, base, calibration, cp_cost, replay_cost, event_interval):
    active = False
    llr, seen = 0.0, 0
    progress = durable = next_event = 0
    next_event = event_interval
    decisions, transcript = [], []
    for t, y in enumerate(labels):
        if progress >= case["task_units"]:
            break
        symbol, legal = case["signals"][t], bool(case["legal"][t])
        age = progress - durable
        p = probs.get(symbol)
        take = (p * age * replay_cost > cp_cost) if (active and p is not None and legal and age > 0) else (legal and progress >= next_event)
        inp = {"type": "TICK", "signal": symbol, "legal": legal, "progress": progress, "age": age,
               "next_event": next_event, "checkpoint_cost": cp_cost, "replay_cost": replay_cost}
        before = active
        if take:
            if not legal:
                raise AssertionError("illegal checkpoint")
            durable = progress
            if progress >= next_event:
                next_event = ((progress // event_interval) + 1) * event_interval
        progress += 1
        if y and progress < case["task_units"]:
            lost_work = (progress - durable) * replay_cost
            progress = durable
        else:
            lost_work = 0
        seen += 1
        if p is not None and 0 < p < 1 and 0 < base < 1:
            llr += y * math.log(p / base) + (1 - y) * math.log((1 - p) / (1 - base))
        if not active and calibration and seen >= 128 and llr >= math.log(1000):
            active = True
        elif active and llr < math.log(100):
            active = False
        decisions.append({"type": "DECISION", "checkpoint": bool(take), "adaptive_active": bool(before), "p": p})
        transcript.append({"episode_id": case["episode_id"], "checkpoint_cost": cp_cost, "replay_cost": replay_cost,
                           "tick": t, "input": inp, "decision": decisions[-1], "observed_interruption": int(y),
                           "progress_after": progress, "durable_after": durable, "lost_work_cost_tick": lost_work,
                           "adaptive_active_after_feedback": bool(active), "llr_after_feedback": round(llr, 9)})
    completed = progress >= case["task_units"]
    return decisions, transcript, {"completed": completed, "final_effects": progress if completed else durable,
            "expected_effects": case["task_units"], "checkpoint_count": sum(d["checkpoint"] for d in decisions),
            "checkpoint_cost_total": sum(d["checkpoint"] for d in decisions) * cp_cost,
            "lost_work_cost": sum(r["lost_work_cost_tick"] for r in transcript),
            "total_cost": sum(d["checkpoint"] for d in decisions) * cp_cost + sum(r["lost_work_cost_tick"] for r in transcript),
            "wall_ticks": len(decisions), "adaptive_active_at_end": active, "observations": seen,
            "disabled_by_tick": next((i for i in range(2, len(decisions) + 1)
                                       if decisions[i - 2]["adaptive_active"] and not decisions[i - 1]["adaptive_active"]), None),
            "decision_digest": hashlib.sha256(bytes(d["checkpoint"] for d in decisions)).hexdigest()}


def verify(payload, training, public, oracle, hashes):
    errors = []
    freeze = readj(ROOT / "FREEZE.json")
    if payload.get("main_sha") != freeze["base_commit"]:
        errors.append("base_commit_receipt")
    if payload.get("source_sha256") != freeze["source_sha256"]:
        errors.append("source_hash_receipt")
    if payload.get("input_sha256") != freeze["input_sha256"]:
        errors.append("input_hash_receipt")
    for name, expected in hashes.items():
        if sha(ROOT / name) != expected:
            errors.append(f"input_hash:{name}")
    probs, base, calibration = expected_fit(training)
    if payload.get("calibration") != calibration:
        errors.append("calibration_reconstruction")
    if payload.get("oracle_sha256") != hashes["oracle.json"]:
        errors.append("oracle_hash_receipt")
    if payload.get("worker_exit") != 0 or payload.get("ready", {}).get("calibrated") != calibration["calibration_pass"]:
        errors.append("candidate_worker_or_gate_receipt")
    hidden = {r["episode_id"]: r for r in oracle["episodes"]}
    if len(hidden) != len(oracle["episodes"]) or len(payload.get("episodes", [])) != len(public["episodes"]) * 6:
        errors.append("episode_cardinality")
    expected_rows, expected_transcript = [], []
    for case in public["episodes"]:
        h = hidden.get(case["episode_id"])
        if h is None:
            errors.append("oracle_join")
            continue
        for cp_cost in public["checkpoint_costs"]:
            for replay_cost in public["replay_costs"]:
                decisions, transcript, result = policy_decisions(case, h["interruptions"], probs, base,
                    calibration["calibration_pass"], cp_cost, replay_cost, public["task_event_interval"])
                fixed = simulate_baseline(case, h["interruptions"], cp_cost, replay_cost, public["fixed_interval"], public["task_event_interval"], "fixed")
                event = simulate_baseline(case, h["interruptions"], cp_cost, replay_cost, public["fixed_interval"], public["task_event_interval"], "event")
                row = {"episode_id": case["episode_id"], "checkpoint_cost": cp_cost, "replay_cost": replay_cost,
                       **{k: v for k, v in result.items() if k != "decision_digest"},
                       "cohort": h["cohort"], "fixed": fixed, "event": event}
                expected_rows.append(row)
                expected_transcript.extend(transcript)
    actual_rows = [{k: v for k, v in row.items() if k != "decision_digest"} for row in payload.get("episodes", [])]
    if actual_rows != expected_rows:
        errors.append("candidate_episode_replay")
    if any(row.get("decision_digest") is not None and row["decision_digest"] != expected["decision_digest"]
           for row, expected in zip(payload.get("episodes", []), [
               {"decision_digest": policy_decisions(case, hidden[case["episode_id"]]["interruptions"], probs, base,
                 calibration["calibration_pass"], cp, rw, public["task_event_interval"])[2]["decision_digest"]}
               for case in public["episodes"] for cp in public["checkpoint_costs"] for rw in public["replay_costs"]])):
        errors.append("decision_digest")
    got_transcript = payload.get("transcript", [])
    allowed = {"type", "signal", "legal", "progress", "age", "next_event", "checkpoint_cost", "replay_cost"}
    for r in got_transcript:
        if set(r.get("input", {})) != allowed:
            errors.append("input_information_boundary")
            break
    if got_transcript != expected_transcript:
        errors.append("stream_transcript_reconstruction")
    return errors, expected_rows, expected_transcript


def main():
    freeze = readj(ROOT / "FREEZE.json")
    source_hash_errors = [f"source_hash:{name}" for name, expected in freeze["source_sha256"].items()
                          if sha(ROOT / name) != expected]
    training, public, oracle = (readj(ROOT / n) for n in ("training.json", "public.json", "oracle.json"))
    payload = readj(FORMAL / "candidate.json")
    errors, rows, transcript = verify(payload, training, public, oracle, freeze["input_sha256"])
    errors.extend(source_hash_errors)
    hidden_by_id = {r["episode_id"]: r for r in oracle["episodes"]}
    public_by_id = {r["episode_id"]: r for r in public["episodes"]}

    # Four effective auditor mutations: changed event marginal, oracle/future input leak,
    # illegal checkpoint, and false final effects. Each is a distinct fail-closed path.
    mutations = {}
    changed_oracle = copy.deepcopy(oracle)
    changed_oracle["episodes"][0]["interruptions"][0] ^= 1
    mutations["changed_interruption_marginal"] = verify(payload, training, public, changed_oracle, freeze["input_sha256"])[0]
    leaked = copy.deepcopy(payload)
    leaked["transcript"][0]["input"]["future_interruption_labels"] = [0, 1]
    mutations["future_label_leak"] = verify(leaked, training, public, oracle, freeze["input_sha256"])[0]
    illegal = copy.deepcopy(payload)
    bad = next((i for i, row in enumerate(illegal["transcript"]) if not row["input"]["legal"]), None)
    if bad is not None:
        illegal["transcript"][bad]["decision"]["checkpoint"] = True
    mutations["illegal_checkpoint"] = verify(illegal, training, public, oracle, freeze["input_sha256"])[0]
    false_effect = copy.deepcopy(payload)
    false_effect["episodes"][0]["final_effects"] += 1
    mutations["false_final_effect"] = verify(false_effect, training, public, oracle, freeze["input_sha256"])[0]
    mutation_rejections = {k: bool(v) for k, v in mutations.items()}

    by_cell = defaultdict(list)
    for row in rows:
        by_cell[(row["cohort"], row["checkpoint_cost"], row["replay_cost"])].append(row)
    summary = []
    all_safe = True
    informative_benefit = True
    for (cohort, cp_cost, replay_cost), group in sorted(by_cell.items()):
        cand = [r["total_cost"] for r in group]
        fixed = [r["fixed"]["total_cost"] for r in group]
        event = [r["event"]["total_cost"] for r in group]
        med_c, med_f, med_e = map(statistics.median, (cand, fixed, event))
        completed = all(r["completed"] and r["final_effects"] == r["expected_effects"] for r in group)
        all_safe &= completed
        reduction_fixed = (med_f - med_c) / med_f if med_f else 0.0
        reduction_event = (med_e - med_c) / med_e if med_e else 0.0
        if cohort == "informative":
            informative_benefit &= reduction_fixed >= 0.10 and reduction_event >= 0.10
        summary.append({"cohort": cohort, "checkpoint_cost": cp_cost, "replay_cost": replay_cost,
                        "n": len(group), "median_candidate": med_c, "median_fixed": med_f,
                        "median_event": med_e, "reduction_vs_fixed": reduction_fixed,
                        "reduction_vs_event": reduction_event, "all_exact_complete": completed,
                        "median_clairvoyant_lower_bound": statistics.median([
                            clairvoyant_lower_bound(public_by_id[r["episode_id"]],
                                hidden_by_id[r["episode_id"]]["interruptions"], cp_cost, replay_cost) for r in group])})

    # Disabled-policy decisions must match the independently simulated event baseline from that tick onward.
    event_decisions_ok = True
    # The candidate driver's transcript has no precomputed event decision; reconstruct exact fallback from state.
    for r in transcript:
        if not r["decision"]["adaptive_active"]:
            fallback = bool(r["input"]["legal"] and r["input"]["progress"] >= r["input"]["next_event"])
            if r["decision"]["checkpoint"] != fallback:
                event_decisions_ok = False
    # Under the new-evidence-only activation gate, uninformative and reversed streams must never activate.
    disable_ok = True
    for row in rows:
        if row["cohort"] not in ("independent", "reversed"):
            continue
        trace = [r for r in transcript if r["episode_id"] == row["episode_id"] and
                 r["checkpoint_cost"] == row["checkpoint_cost"] and r["replay_cost"] == row["replay_cost"]]
        if any(x["adaptive_active_after_feedback"] or x["decision"]["adaptive_active"] for x in trace):
            disable_ok = False
    calibration_by_cohort = defaultdict(list)
    for r in transcript:
        if r["input"]["signal"] in ("HIGH", "LOW"):
            calibration_by_cohort[hidden_by_id[r["episode_id"]]["cohort"]].append(
                (r["decision"]["p"], r["observed_interruption"]))
    brier = {k: sum((p - y) ** 2 for p, y in v) / len(v) for k, v in calibration_by_cohort.items()}
    if errors:
        disposition = "FAIL_AUDIT"
    elif not all_safe or not event_decisions_ok:
        disposition = "FAIL_UNSAFE_RESUME"
    elif not calibration["calibration_pass"] or not disable_ok or not all(mutation_rejections.values()):
        disposition = "FAIL_CALIBRATION"
    elif informative_benefit:
        disposition = "PASS_ADAPTIVE_PLACEMENT_SCOPED"
    else:
        disposition = "PASS_SAFETY_NO_BENEFIT"
    audit = {"format": "7466-a03-independent-audit-v1", "disposition": disposition, "errors": errors,
             "candidate_rows_reconstructed": len(rows), "streamed_ticks_reconstructed": len(transcript),
             "mutations_rejected": mutation_rejections, "mutation_count": len(mutation_rejections),
             "informative_benefit_gate": informative_benefit, "uninformative_and_reversed_never_activated": disable_ok,
             "fallback_decisions_match_event_baseline": event_decisions_ok,
             "all_effects_exact_and_complete": all_safe, "brier_by_cohort": brier, "summary": summary}
    (FORMAL / "audit.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (FORMAL / "audit.stdout.json").write_text(json.dumps({"exit": 0 if not errors else 1, "disposition": disposition,
        "rows": len(rows), "ticks": len(transcript), "mutations_rejected": sum(mutation_rejections.values())}, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "errors": errors, "rows": len(rows), "ticks": len(transcript),
                      "mutations_rejected": mutation_rejections, "informative_benefit": informative_benefit,
                      "uninformative_and_reversed_never_activated": disable_ok}, sort_keys=True))
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
