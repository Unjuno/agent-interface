#!/usr/bin/env python3
"""Deterministic mock-API experiment for Issue #6001 T0; no provider calls."""
import json
import math
import random
import sys
from pathlib import Path

N = 128
NULL_TRIALS = 256
DECK = ("localization", "abstention", "schema")
LATER_PHASES = ("post_A", "pre_B", "mid_B", "post_B")
SEED = 600120261003
THRESHOLD = 24


def bits(rng, error_probability):
    return "".join("0" if rng.random() < error_probability else "1" for _ in range(N))


def stream(trial, phase, cue, p_error):
    # Independent, explicitly keyed deterministic streams make row order irrelevant.
    key = f"{SEED}:{trial}:{phase}:{cue}".encode()
    seed = int.from_bytes(key, "big") % (2**63 - 1)
    return bits(random.Random(seed), p_error)


def null_trials():
    rows = []
    for trial in range(NULL_TRIALS):
        phases = {"pre_A": {c: stream(trial, "pre_A", c, .10) for c in DECK}}
        for phase in LATER_PHASES:
            phases[phase] = {c: stream(trial, phase, c, .10) for c in DECK}
        rows.append({"trial": trial, "responses": phases})
    return rows


def scenario(case_id, prompt_drift=False, metadata_drift=False, schema_drift=False,
             in_deck_drift_at=None, out_of_deck_drift=False, route_delta=.12):
    phases = {}
    for phase in ("pre_A", "post_A", "pre_B", "mid_B", "post_B"):
        cue_rows = {}
        for cue in DECK:
            shifted = in_deck_drift_at is not None and phase in in_deck_drift_at.get(cue, ())
            cue_rows[cue] = stream(case_id, phase, cue, .35 if shifted else .10)
        phases[phase] = cue_rows
    return {
        "case_id": case_id,
        "alias": "frontier-stable-alias",
        "exposed_model_version": "v17",
        "fingerprint": "fp-stable-001",
        "schema_hash": "tool-schema-001" if not schema_drift else "tool-schema-002",
        "prompt_hash_A": "prompt-A-001",
        "prompt_hash_B": "prompt-B-002" if prompt_drift else "prompt-A-001",
        "out_of_deck_digest_A": "heldout-task-A",
        "out_of_deck_digest_B": "heldout-task-B-shifted" if out_of_deck_drift else "heldout-task-B",
        "fingerprint_B": "fp-stable-002" if metadata_drift else "fp-stable-001",
        "route_effect_delta": route_delta,
        "responses": phases,
    }


def scenarios():
    return [
        scenario("stationary_control", route_delta=.12),
        scenario("in_deck_behavior_shift", in_deck_drift_at={"localization": ("post_A", "pre_B", "mid_B", "post_B")}),
        scenario("metadata_only_change", metadata_drift=True),
        scenario("schema_only_break", schema_drift=True),
        scenario("prompt_context_drift", prompt_drift=True, in_deck_drift_at={"localization": ("pre_B", "mid_B", "post_B")}),
        scenario("out_of_deck_change", out_of_deck_drift=True),
        scenario("within_block_switch", in_deck_drift_at={"localization": ("mid_B", "post_B")}),
    ]


def errors(bits_value):
    return len(bits_value) - bits_value.count("1")


def disposition(row):
    if row["schema_hash"] != "tool-schema-001":
        return "HOLD_SCHEMA_CHANGE"
    if row["prompt_hash_A"] != row["prompt_hash_B"]:
        return "HOLD_PROMPT_CONTEXT_DRIFT"
    if row["fingerprint"] != row["fingerprint_B"]:
        return "HOLD_MODEL_METADATA_CHANGE"
    baseline = row["responses"]["pre_A"]
    for phase in LATER_PHASES:
        for cue in DECK:
            if errors(row["responses"][phase][cue]) - errors(baseline[cue]) >= THRESHOLD:
                return "HOLD_MODEL_STABILITY"
    if row["out_of_deck_digest_A"] != row["out_of_deck_digest_B"]:
        return "UNKNOWN_COVERAGE"
    return "NO_SHIFT_DETECTED_IN_DECK"


def exact_tail(n, p, threshold):
    pmf = [math.comb(n, k) * p**k * (1-p)**(n-k) for k in range(n+1)]
    return sum(pmf[i] * pmf[j] for i in range(n+1) for j in range(n+1) if j-i >= threshold)


def run():
    null = null_trials()
    null_false_alarms = 0
    for row in null:
        baseline = row["responses"]["pre_A"]
        alarm = any(
            errors(row["responses"][phase][cue]) - errors(baseline[cue]) >= THRESHOLD
            for phase in LATER_PHASES for cue in DECK
        )
        null_false_alarms += int(alarm)
    cases = []
    for row in scenarios():
        alias_only = row["alias"] == "frontier-stable-alias" and row["route_effect_delta"] > 0
        metadata_only = (
            row["fingerprint"] == row["fingerprint_B"]
            and row["schema_hash"] == "tool-schema-001"
            and row["route_effect_delta"] > 0
        )
        cases.append({"case_id": row["case_id"], "alias_only_would_promote": alias_only,
                      "metadata_only_would_promote": metadata_only,
                      "bracketed_disposition": disposition(row), "trace": row})
    single_tail = exact_tail(N, .10, THRESHOLD)
    return {
        "schema": "issue6001-t0-mock-api-v1", "seed": SEED, "samples_per_cue_phase": N,
        "null_trials": NULL_TRIALS, "error_delta_threshold": THRESHOLD,
        "familywise_comparisons": len(DECK) * len(LATER_PHASES),
        "stationary_false_alarms": null_false_alarms,
        "stationary_empirical_rate": null_false_alarms / NULL_TRIALS,
        "stationary_union_bound": single_tail * len(DECK) * len(LATER_PHASES),
        "shift_power_at_error_0_35": 1 - (1-exact_tail(N, .10, THRESHOLD))**(len(DECK)*len(LATER_PHASES)),
        "null_raw": null, "cases": cases,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT_JSON")
    result = run()
    path = Path(sys.argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "null_trials": len(result["null_raw"]),
                      "cases": len(result["cases"]), "output": str(path)}, sort_keys=True))
