#!/usr/bin/env python3
"""Synthetic black-box model-stability canary study for Issue #6001.

No model/provider is contacted. The evaluator-only planted truth is kept in a
separate field from candidate-visible API metadata and probe responses.
"""
import json
import random
import sys

SEED = 6001002
N_TRIALS = 200
N_PER_PROBE_CLASS = 20
DECK = ("target_localization", "no_target_abstention", "action_schema",
        "temporal_cue", "negative_control")
SCENARIOS = ("stationary", "hidden_in_deck_between", "hidden_outside_deck_between",
             "schema_only", "prompt_context_drift", "visible_snapshot_change",
             "hidden_in_deck_mid_B")
POLICIES = ("alias_only", "metadata_only", "bracketed_canary")


def _bernoulli(rng, probability):
    return [int(rng.random() < probability) for _ in range(N_PER_PROBE_CLASS)]


def _metadata(scenario):
    changed = scenario == "visible_snapshot_change"
    return {
        "alias_A": "provider/model-x", "alias_B": "provider/model-x",
        "snapshot_A": "snapshot-17" if changed else None,
        "snapshot_B": "snapshot-18" if changed else None,
        "schema_A": "action-schema-v3",
        "schema_B": "action-schema-v4" if scenario == "schema_only" else "action-schema-v3",
        "prompt_hash_A": "prompt-fixed-v1",
        "prompt_hash_B": "prompt-drift-v2" if scenario == "prompt_context_drift" else "prompt-fixed-v1",
        "context_hash_A": "context-fixed-v1",
        "context_hash_B": "context-drift-v2" if scenario == "prompt_context_drift" else "context-fixed-v1",
    }


def candidate_decision(policy, metadata, probes):
    if metadata["alias_A"] != metadata["alias_B"]:
        return "HOLD_ALIAS_CHANGED"
    if policy == "alias_only":
        return "ALIAS_MATCH_ONLY; MODEL_BEHAVIOR_UNVERIFIED"
    if metadata["schema_A"] != metadata["schema_B"]:
        return "HOLD_SCHEMA_CHANGE"
    if (metadata["prompt_hash_A"], metadata["context_hash_A"]) != (
            metadata["prompt_hash_B"], metadata["context_hash_B"]):
        return "HOLD_PROMPT_CONTEXT_DRIFT"
    if metadata["snapshot_A"] != metadata["snapshot_B"] and (
            metadata["snapshot_A"] is not None or metadata["snapshot_B"] is not None):
        return "HOLD_SNAPSHOT_CHANGED"
    if policy == "metadata_only":
        return "NO_METADATA_CHANGE; MODEL_BEHAVIOR_UNVERIFIED"

    before = probes["before_A"]
    between = probes["between_A_B"]
    after = probes["after_B"]
    for task in DECK:
        b0 = sum(sum(x[task]) for x in before) / (len(before) * N_PER_PROBE_CLASS)
        b1 = sum(sum(x[task]) for x in between) / (len(between) * N_PER_PROBE_CLASS)
        b2 = sum(sum(x[task]) for x in after) / (len(after) * N_PER_PROBE_CLASS)
        if b0 - b1 >= 0.20:
            return "HOLD_BEHAVIOR_SHIFT_BEFORE_B"
        if b1 - b2 >= 0.20:
            return "HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT"
    return "NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED"


def make_group(scenario, policy):
    probe_rng = random.Random(SEED + SCENARIOS.index(scenario) * 101 + POLICIES.index(policy) * 1009)
    route_rng = random.Random(SEED + SCENARIOS.index(scenario) * 103 + POLICIES.index(policy) * 1013)
    probes = {"before_A": [], "between_A_B": [], "after_B": []}
    route = {"A": [], "B": []}
    for trial in range(N_TRIALS):
        if policy == "bracketed_canary":
            for phase in probes:
                phase_map = {}
                for task in DECK:
                    p = 0.90
                    if task == "target_localization" and scenario in (
                            "hidden_in_deck_between", "hidden_in_deck_mid_B"):
                        if phase == "after_B" or (phase == "between_A_B" and scenario.endswith("between")):
                            p = 0.55
                    phase_map[task] = _bernoulli(probe_rng, p)
                probes[phase].append(phase_map)
        a_success = route_rng.random() < 0.90
        route["A"].append({"trial": trial, "success": int(a_success)})
        b_rows = []
        for position in range(4):
            p = 0.90
            if scenario in ("hidden_in_deck_between", "hidden_outside_deck_between"):
                p = 0.55
            elif scenario == "hidden_in_deck_mid_B" and position >= 2:
                p = 0.55
            elif scenario == "prompt_context_drift":
                p = 0.55
            b_rows.append({"position": position, "success": int(route_rng.random() < p)})
        route["B"].append({"trial": trial, "rows": b_rows})

    metadata = _metadata(scenario)
    observed_probes = probes if policy == "bracketed_canary" else {}
    record = {
        "scenario": scenario,
        "policy": policy,
        "n_trials": N_TRIALS,
        "probe_attempts_per_class_per_phase": N_TRIALS * N_PER_PROBE_CLASS if policy == "bracketed_canary" else 0,
        "candidate_observations": metadata,
        "route_rows": route,
        "canary_attempts": observed_probes,
        "candidate_disposition": candidate_decision(policy, metadata, observed_probes) if policy == "bracketed_canary" else candidate_decision(policy, metadata, {}),
        # Evaluator-only fields; the candidate function never reads these.
        "evaluator_truth": {
            "latent_snapshot_changed": scenario in (
                "hidden_in_deck_between", "hidden_outside_deck_between", "hidden_in_deck_mid_B",
                "visible_snapshot_change"),
            "semantic_shift": scenario in (
                "hidden_in_deck_between", "hidden_outside_deck_between", "hidden_in_deck_mid_B"),
            "shift_coverage": "outside_deck" if scenario == "hidden_outside_deck_between" else (
                "in_deck" if scenario in ("hidden_in_deck_between", "hidden_in_deck_mid_B") else "none"),
            "switch_interval": "between_A_B" if scenario.endswith("between") else (
                "inside_B" if scenario == "hidden_in_deck_mid_B" else "none"),
        },
    }
    return record


def main(path):
    rows = [make_group(s, p) for s in SCENARIOS for p in POLICIES]
    with open(path, "w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"groups": len(rows), "scenarios": len(SCENARIOS),
                      "policies": len(POLICIES), "trials_per_group": N_TRIALS,
                      "seed": SEED, "output": path}))


if __name__ == "__main__":
    main(sys.argv[1])
