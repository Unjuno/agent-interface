#!/usr/bin/env python3
"""Run the frozen A/B/C reducers and retain every synthetic oracle call."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from simulator import (
    legal, one_sided_lower, one_sided_upper, reduced, replay,
)
from spec import (
    ALPHA_FAMILY, BASE_TRACE, BASELINE_N, CONFIRM_N_PER_STRATUM, EXIT_CODE, FIXED_N,
    INSTANCES, MARGIN, REMOVAL_GROUPS, SEQUENTIAL_MAX_N, SEQUENTIAL_MIN_N,
    SEQUENTIAL_STEP, TARGET, seed_for, strata_for_instance,
)

METHODS = ("single_run", "fixed_64", "sequential")
LOOKS = (SEQUENTIAL_MAX_N - SEQUENTIAL_MIN_N) // SEQUENTIAL_STEP + 1


def _record(events: tuple[str, ...], seed: int, stratum: int) -> dict:
    return {"seed": seed, "stratum": stratum, "events": list(events), **replay(events, seed, stratum)}


def _search(method: str, instance: int) -> dict:
    stratum = strata_for_instance(instance)[0]
    baseline_seeds = [seed_for(instance, j, "search_baseline") for j in range(BASELINE_N)]
    baseline_rows = [_record(BASE_TRACE, s, stratum) for s in baseline_seeds]
    for row in baseline_rows:
        row["stage"] = "baseline"
    base_successes = sum(r["fingerprint"] == TARGET for r in baseline_rows)
    base_alpha = ALPHA_FAMILY / (INSTANCES * 2)
    baseline_lower = one_sided_lower(base_successes, BASELINE_N, base_alpha)
    threshold = max(0.0, baseline_lower - MARGIN)
    current = tuple(BASE_TRACE)
    trials: list[dict] = []
    attempts: list[dict] = []
    candidate_index = 0
    for group_name, group in REMOVAL_GROUPS:
        proposed = reduced(current, group)
        raw_start = len(trials)
        if proposed == current:
            attempts.append({"group": group_name, "decision": "NO_OP", "n": 0, "trace_before": list(current), "trace_after": list(current), "looks": [], "raw_trial_start": raw_start, "raw_trial_count": 0})
            continue
        if not legal(proposed):
            attempts.append({"group": group_name, "decision": "INVALID_REJECT", "n": 0, "trace_before": list(current), "trace_after": list(current), "looks": [], "raw_trial_start": raw_start, "raw_trial_count": 0})
            continue
        look_rows: list[dict] = []
        if method == "single_run":
            seed = seed_for(instance, candidate_index, "search_candidate")
            row = _record(proposed, seed, stratum); row.update({"stage": "search", "group": group_name}); trials.append(row)
            accept = row["fingerprint"] == TARGET
            decision = "ACCEPT_ONE_HIT" if accept else "REJECT_ONE_MISS"
            look_rows.append({"n": 1, "successes": int(accept), "lower": None, "upper": None})
        else:
            alpha = ALPHA_FAMILY / (INSTANCES * len(REMOVAL_GROUPS) * 2)
            n_max = FIXED_N if method == "fixed_64" else SEQUENTIAL_MAX_N
            chunk = n_max if method == "fixed_64" else SEQUENTIAL_STEP
            n = 0; successes = 0; accept = False; decision = "REJECT_INCONCLUSIVE"
            while n < n_max:
                next_n = min(n_max, n + chunk)
                for offset in range(n, next_n):
                    seed = seed_for(instance, candidate_index * 1000 + offset, "search_candidate")
                    row = _record(proposed, seed, stratum); row.update({"stage": "search", "group": group_name}); trials.append(row)
                    successes += int(row["fingerprint"] == TARGET)
                n = next_n
                look_alpha = alpha if method == "fixed_64" else alpha / LOOKS
                lower = one_sided_lower(successes, n, look_alpha)
                upper = one_sided_upper(successes, n, look_alpha)
                look_rows.append({"n": n, "successes": successes, "lower": lower, "upper": upper})
                if method == "fixed_64":
                    accept = lower >= threshold
                    decision = "ACCEPT_FIXED_BOUND" if accept else "REJECT_FIXED_BOUND"
                    break
                if lower >= threshold:
                    accept = True; decision = "ACCEPT_SEQUENTIAL_BOUND"; break
                if upper < threshold:
                    decision = "REJECT_SEQUENTIAL_BOUND"; break
        before = list(current)
        if accept:
            current = proposed
        attempts.append({"group": group_name, "decision": decision, "n": len(look_rows) and look_rows[-1]["n"] or 0,
                         "trace_before": before, "trace_after": list(current), "proposed_trace": list(proposed),
                         "threshold": threshold, "looks": look_rows,
                         "raw_trial_start": raw_start, "raw_trial_count": len(trials)-raw_start})
        candidate_index += 1

    confirm: list[dict] = []
    for index in range(CONFIRM_N_PER_STRATUM):
        seed = seed_for(instance, index, "confirm")
        original = replay(BASE_TRACE, seed, stratum)
        final = replay(current, seed, stratum)
        confirm.append({"stratum": stratum, "seed": seed,
                        "original_fingerprint": original["fingerprint"],
                        "final_fingerprint": final["fingerprint"],
                        "delta": int(final["fingerprint"] == TARGET) - int(original["fingerprint"] == TARGET)})
    return {
        "method": method, "instance": instance, "stratum": stratum,
        "baseline_trials": baseline_rows, "baseline_target_successes": base_successes,
        "baseline_lower_bound": baseline_lower, "screen_threshold": threshold,
        "candidate_trials": trials, "attempts": attempts,
        "initial_trace": list(BASE_TRACE), "final_trace": list(current),
        "confirmations": confirm,
    }


def run(freeze_digest: str) -> dict:
    runs = [_search(method, instance) for method in METHODS for instance in range(INSTANCES)]
    return {"schema": "unjuno.issue8152.candidate.raw.v1", "freeze_digest": freeze_digest,
            "expected_freeze_digest": freeze_digest, "runs": runs,
            "method_order": list(METHODS), "query_summary": {
                method: sum(len(r["baseline_trials"]) + len(r["candidate_trials"]) + 2*len(r["confirmations"])
                            for r in runs if r["method"] == method)
                for method in METHODS}}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json FREEZE_SHA256")
    output = Path(argv[0]); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(run(argv[1]), sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
