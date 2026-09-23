#!/usr/bin/env python3
import argparse
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

OPS = ("OBS0", "OBS1", "VALIDATE", "COMMIT", "ADVANCE", "CONTRADICT", "TRY_ACTION")
NONE, TENTATIVE, VALIDATED, COMMITTED, QUARANTINED = range(5)
PHASE_NAMES = {
    NONE: "NONE",
    TENTATIVE: "TENTATIVE",
    VALIDATED: "VALIDATED",
    COMMITTED: "COMMITTED",
    QUARANTINED: "QUARANTINED",
}
INITIAL = (NONE, 0, -1, -1, False, ())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_step(state, op):
    phase, cur_g, value, support_g, contradicted, history = state
    accepted = False
    action_safe = None

    if op == "OBS0" or op == "OBS1":
        value = 0 if op == "OBS0" else 1
        support_g = cur_g
        contradicted = False
        phase = TENTATIVE
        accepted = True
    elif op == "VALIDATE":
        if phase == TENTATIVE and support_g == cur_g and not contradicted:
            phase = VALIDATED
            accepted = True
    elif op == "COMMIT":
        if phase == VALIDATED and support_g == cur_g and not contradicted:
            phase = COMMITTED
            history = history + ((value, support_g),)
            accepted = True
    elif op == "ADVANCE":
        if cur_g == 0:
            cur_g = 1
            accepted = True
    elif op == "CONTRADICT":
        if support_g == cur_g and phase in (TENTATIVE, VALIDATED, COMMITTED) and not contradicted:
            contradicted = True
            phase = QUARANTINED
            accepted = True
    elif op == "TRY_ACTION":
        accepted = True
        action_safe = bool(
            phase == COMMITTED and support_g == cur_g and not contradicted
        )
    else:
        raise ValueError(op)

    return (phase, cur_g, value, support_g, contradicted, history), (accepted, action_safe)


def oracle_step(state, op):
    phase = state[0]
    current_generation = state[1]
    support_value = state[2]
    support_generation = state[3]
    contradiction = state[4]
    commits = state[5]

    accepted = False
    safe = None

    if op in ("OBS0", "OBS1"):
        support_value = int(op[-1])
        support_generation = current_generation
        contradiction = False
        phase = TENTATIVE
        accepted = True
    elif op == "VALIDATE":
        eligible = (
            phase == TENTATIVE
            and support_generation == current_generation
            and contradiction is False
        )
        if eligible:
            phase = VALIDATED
            accepted = True
    elif op == "COMMIT":
        eligible = (
            phase == VALIDATED
            and support_generation == current_generation
            and contradiction is False
        )
        if eligible:
            phase = COMMITTED
            commits = tuple(list(commits) + [(support_value, support_generation)])
            accepted = True
    elif op == "ADVANCE":
        if current_generation < 1:
            current_generation += 1
            accepted = True
    elif op == "CONTRADICT":
        has_current_support = support_generation == current_generation
        lifecycle_can_quarantine = phase in {TENTATIVE, VALIDATED, COMMITTED}
        if has_current_support and lifecycle_can_quarantine and not contradiction:
            contradiction = True
            phase = QUARANTINED
            accepted = True
    elif op == "TRY_ACTION":
        accepted = True
        safe = (
            phase == COMMITTED
            and support_generation == current_generation
            and contradiction is False
        )
    else:
        raise AssertionError(op)

    return (
        phase,
        current_generation,
        support_value,
        support_generation,
        contradiction,
        commits,
    ), (accepted, safe)


def encode_record(depth, code, state, result):
    phase, cur_g, value, support_g, contradicted, history = state
    accepted, action_safe = result
    action_code = 2 if action_safe is None else int(bool(action_safe))
    buf = bytearray(struct.pack("!BQ", depth, code))
    buf.extend(bytes((phase, cur_g, value + 1, support_g + 1, int(contradicted), len(history), int(accepted), action_code)))
    for hv, hg in history:
        buf.extend(bytes((hv + 1, hg + 1)))
    return bytes(buf)


def classify_before_action(state):
    phase, cur_g, _value, support_g, contradicted, history = state
    return {
        "has_history": bool(history),
        "stale_committed": phase == COMMITTED and support_g != cur_g,
        "contradicted": contradicted or phase == QUARANTINED,
        "not_currently_committed": bool(history) and phase != COMMITTED,
    }


def run_directed(step_fn):
    controls = {
        "commit_then_act": ["OBS0", "VALIDATE", "COMMIT", "TRY_ACTION"],
        "commit_advance_act": ["OBS0", "VALIDATE", "COMMIT", "ADVANCE", "TRY_ACTION"],
        "commit_contradict_act": ["OBS0", "VALIDATE", "COMMIT", "CONTRADICT", "TRY_ACTION"],
        "stale_commit_reobserve_no_recommit_act": ["OBS0", "VALIDATE", "COMMIT", "ADVANCE", "OBS1", "TRY_ACTION"],
        "fresh_recommit_act": ["OBS0", "VALIDATE", "COMMIT", "ADVANCE", "OBS1", "VALIDATE", "COMMIT", "TRY_ACTION"],
        "commit_from_tentative": ["OBS0", "COMMIT"],
        "duplicate_advance": ["ADVANCE", "ADVANCE"],
    }
    out = {}
    for name, trace in controls.items():
        state = INITIAL
        steps = []
        for op in trace:
            before = state
            state, result = step_fn(state, op)
            steps.append({
                "op": op,
                "before_phase": PHASE_NAMES[before[0]],
                "after_phase": PHASE_NAMES[state[0]],
                "accepted": result[0],
                "action_safe": result[1],
                "current_generation": state[1],
                "support_generation": state[3],
                "history": [list(x) for x in state[5]],
            })
        out[name] = {"trace": trace, "final": steps[-1], "steps": steps}
    return out


def directed_pass(controls):
    return all((
        controls["commit_then_act"]["final"]["action_safe"] is True,
        controls["commit_advance_act"]["final"]["action_safe"] is False,
        controls["commit_contradict_act"]["final"]["action_safe"] is False,
        controls["stale_commit_reobserve_no_recommit_act"]["final"]["action_safe"] is False,
        controls["fresh_recommit_act"]["final"]["action_safe"] is True,
        controls["commit_from_tentative"]["final"]["accepted"] is False,
        controls["duplicate_advance"]["final"]["accepted"] is False,
    ))


def enumerate_corpus(max_depth):
    metrics = {
        "trace_count_including_empty": 1,
        "transition_count": 0,
        "candidate_oracle_mismatch": 0,
        "stale_action_opportunities": 0,
        "stale_generation_action_safe_admissions": 0,
        "contradicted_action_opportunities": 0,
        "contradicted_action_safe_admissions": 0,
        "commit_from_unvalidated_attempts": 0,
        "commit_from_unvalidated_admissions": 0,
        "fresh_recommit_action_safe": 0,
        "provenance_retained_across_generation_change": 0,
        "committed_only_unsafe_total": 0,
        "committed_only_unsafe_stale_or_contradicted": 0,
        "candidate_action_safe_total": 0,
    }
    cand_digest = hashlib.sha256()
    oracle_digest = hashlib.sha256()
    first_mismatch = None
    path = [None] * max_depth

    sys.setrecursionlimit(10000)

    def walk(depth, code, cand_state, oracle_state):
        nonlocal first_mismatch
        if depth >= max_depth:
            return
        for op_idx, op in enumerate(OPS):
            path[depth] = op
            next_code = code * len(OPS) + (op_idx + 1)
            c_before = cand_state
            c_after, c_result = candidate_step(cand_state, op)
            o_after, o_result = oracle_step(oracle_state, op)
            d = depth + 1
            metrics["transition_count"] += 1
            metrics["trace_count_including_empty"] += 1

            cand_digest.update(encode_record(d, next_code, c_after, c_result))
            oracle_digest.update(encode_record(d, next_code, o_after, o_result))

            if c_after != o_after or c_result != o_result:
                metrics["candidate_oracle_mismatch"] += 1
                if first_mismatch is None:
                    first_mismatch = {
                        "trace": path[:d],
                        "candidate_state": c_after,
                        "oracle_state": o_after,
                        "candidate_result": c_result,
                        "oracle_result": o_result,
                    }

            if op == "COMMIT" and c_before[0] != VALIDATED:
                metrics["commit_from_unvalidated_attempts"] += 1
                if c_result[0]:
                    metrics["commit_from_unvalidated_admissions"] += 1

            if op == "ADVANCE" and c_result[0] and c_before[5]:
                if c_after[5] == c_before[5]:
                    metrics["provenance_retained_across_generation_change"] += 1

            if op == "TRY_ACTION":
                cls = classify_before_action(c_before)
                if cls["stale_committed"]:
                    metrics["stale_action_opportunities"] += 1
                    if c_result[1]:
                        metrics["stale_generation_action_safe_admissions"] += 1
                if cls["contradicted"] and cls["has_history"]:
                    metrics["contradicted_action_opportunities"] += 1
                    if c_result[1]:
                        metrics["contradicted_action_safe_admissions"] += 1
                if c_result[1]:
                    metrics["candidate_action_safe_total"] += 1
                    history_gens = [g for _v, g in c_after[5]]
                    if c_after[1] == 1 and 0 in history_gens and history_gens[-1] == 1:
                        metrics["fresh_recommit_action_safe"] += 1

                committed_only_safe = bool(c_before[5])
                if committed_only_safe and not c_result[1]:
                    metrics["committed_only_unsafe_total"] += 1
                    if cls["stale_committed"] or cls["contradicted"]:
                        metrics["committed_only_unsafe_stale_or_contradicted"] += 1

            walk(d, next_code, c_after, o_after)

    walk(0, 0, INITIAL, INITIAL)
    return metrics, cand_digest.hexdigest(), oracle_digest.hexdigest(), first_mismatch


def decide(metrics, directed_ok, max_depth):
    if metrics["candidate_oracle_mismatch"] != 0:
        return "FAIL_INTEGRITY"
    if metrics["stale_generation_action_safe_admissions"] != 0 or metrics["contradicted_action_safe_admissions"] != 0:
        return "FAIL_BELIEF_AUTHORITY_LEAK"
    if metrics["commit_from_unvalidated_admissions"] != 0:
        return "FAIL_BELIEF_AUTHORITY_LEAK"
    if not directed_ok:
        return "FAIL_BELIEF_OVERINVALIDATION"
    if max_depth >= 8 and metrics["fresh_recommit_action_safe"] <= 0:
        return "FAIL_BELIEF_OVERINVALIDATION"
    if metrics["provenance_retained_across_generation_change"] <= 0:
        return "FAIL_INTEGRITY"
    if metrics["committed_only_unsafe_stale_or_contradicted"] <= 0:
        return "FAIL_DISCRIMINATOR"
    return "PASS_CONSTRUCTION_ELIGIBLE" if max_depth < 8 else "PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_A2_SCOPED"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--construction", action="store_true")
    g.add_argument("--formal", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()

    max_depth = 5 if args.construction else 8
    start = time.perf_counter()
    cand_controls = run_directed(candidate_step)
    oracle_controls = run_directed(oracle_step)
    directed_ok = directed_pass(cand_controls) and cand_controls == oracle_controls
    metrics, cand_digest, oracle_digest, first_mismatch = enumerate_corpus(max_depth)
    elapsed = time.perf_counter() - start
    decision = decide(metrics, directed_ok, max_depth)

    here = Path(__file__).resolve().parent
    result = {
        "task": "TRANSACTIONAL-BELIEF-ACTION-SAFE-A2-20260919-002",
        "mode": "construction" if args.construction else "formal",
        "max_depth": max_depth,
        "operation_alphabet": list(OPS),
        "directed_controls_pass": directed_ok,
        "metrics": metrics,
        "candidate_digest": cand_digest,
        "oracle_digest": oracle_digest,
        "digests_equal": cand_digest == oracle_digest,
        "first_mismatch": first_mismatch,
        "decision": decision,
        "elapsed_seconds": elapsed,
        "formal_invocations": 1 if args.formal else 0,
        "reruns": 0,
        "replacements": 0,
        "tuning_after_freeze": 0,
        "formal_source_sha256": sha256_file(here / "formal.py"),
        "directed_controls": cand_controls,
    }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
