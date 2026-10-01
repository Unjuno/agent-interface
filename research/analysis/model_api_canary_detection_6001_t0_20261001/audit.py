#!/usr/bin/env python3
"""Independent auditor for the Issue #6001 hidden-shift mock T0."""
import json
import sys

SCENARIOS = ("stationary", "hidden_in_deck_between", "hidden_outside_deck_between",
             "schema_only", "prompt_context_drift", "visible_snapshot_change",
             "hidden_in_deck_mid_B")
POLICIES = ("alias_only", "metadata_only", "bracketed_canary")
DECK = ("target_localization", "no_target_abstention", "action_schema",
        "temporal_cue", "negative_control")
N_TRIALS = 200
N_PER_PROBE = 20
THRESHOLD = 0.20


def recompute(policy, metadata, probes):
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
    for task in DECK:
        phase_means = []
        for phase in ("before_A", "between_A_B", "after_B"):
            attempts = [bit for trial in probes[phase] for bit in trial[task]]
            phase_means.append(sum(attempts) / len(attempts))
        if phase_means[0] - phase_means[1] >= THRESHOLD:
            return "HOLD_BEHAVIOR_SHIFT_BEFORE_B"
        if phase_means[1] - phase_means[2] >= THRESHOLD:
            return "HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT"
    return "NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED"


def _truth_for(scenario):
    return {
        "latent_snapshot_changed": scenario in (
            "hidden_in_deck_between", "hidden_outside_deck_between", "hidden_in_deck_mid_B",
            "visible_snapshot_change"),
        "semantic_shift": scenario in (
            "hidden_in_deck_between", "hidden_outside_deck_between", "hidden_in_deck_mid_B"),
        "shift_coverage": "outside_deck" if scenario == "hidden_outside_deck_between" else (
            "in_deck" if scenario in ("hidden_in_deck_between", "hidden_in_deck_mid_B") else "none"),
        "switch_interval": "between_A_B" if scenario.endswith("between") else (
            "inside_B" if scenario == "hidden_in_deck_mid_B" else "none"),
    }


def audit(path):
    rows, errors = {}, []
    try:
        with open(path, encoding="utf-8") as stream:
            for lineno, line in enumerate(stream, 1):
                row = json.loads(line)
                key = (row["scenario"], row["policy"])
                if key in rows:
                    errors.append(f"duplicate group at line {lineno}: {key}")
                rows[key] = row
    except Exception as exc:
        return {"verdict": "FAIL_AUDIT", "errors": [f"read/parse: {exc}"]}
    expected = {(s, p) for s in SCENARIOS for p in POLICIES}
    if set(rows) != expected:
        errors.append(f"group coverage mismatch: expected {len(expected)}, got {len(rows)}")

    route_retained = True
    for (scenario, policy), row in rows.items():
        try:
            if row["n_trials"] != N_TRIALS:
                errors.append(f"trial denominator mismatch: {scenario}/{policy}")
            if "evaluator_truth" in row["candidate_observations"]:
                errors.append(f"oracle truth leaked to candidate: {scenario}/{policy}")
            if row["evaluator_truth"] != _truth_for(scenario):
                errors.append(f"planted truth provenance mismatch: {scenario}/{policy}")
            if len(row["route_rows"]["A"]) != N_TRIALS or len(row["route_rows"]["B"]) != N_TRIALS:
                route_retained = False
                errors.append(f"route rows missing: {scenario}/{policy}")
            for arm in ("A", "B"):
                indices = [r["trial"] for r in row["route_rows"][arm]]
                if indices != list(range(N_TRIALS)):
                    errors.append(f"route trial ordering/cardinality: {scenario}/{policy}/{arm}")
            if any(len(r["rows"]) != 4 or [x["position"] for x in r["rows"]] != list(range(4))
                   for r in row["route_rows"]["B"]):
                route_retained = False
                errors.append(f"B route block incomplete: {scenario}/{policy}")
            probes = row["canary_attempts"]
            if policy == "bracketed_canary":
                if set(probes) != {"before_A", "between_A_B", "after_B"}:
                    errors.append(f"probe phase coverage: {scenario}")
                else:
                    for phase, trials in probes.items():
                        if len(trials) != N_TRIALS:
                            errors.append(f"probe trial count: {scenario}/{phase}")
                            continue
                        for trial in trials:
                            if set(trial) != set(DECK) or any(len(trial[t]) != N_PER_PROBE for t in DECK):
                                errors.append(f"probe deck/denominator: {scenario}/{phase}")
                                break
                            if any(v not in (0, 1) for t in DECK for v in trial[t]):
                                errors.append(f"probe outcome type: {scenario}/{phase}")
                                break
            elif probes:
                errors.append(f"unassigned canary workload in control policy: {scenario}/{policy}")
            expected_decision = recompute(policy, row["candidate_observations"], probes)
            if row["candidate_disposition"] != expected_decision:
                errors.append(f"decision does not recompute: {scenario}/{policy}")
        except Exception as exc:
            errors.append(f"malformed group {scenario}/{policy}: {exc}")

    decisions = {s: rows[(s, "bracketed_canary")]["candidate_disposition"]
                 for s in SCENARIOS if (s, "bracketed_canary") in rows}
    gates = {
        "in_deck_between_shift_caught_before_B": decisions.get("hidden_in_deck_between") == "HOLD_BEHAVIOR_SHIFT_BEFORE_B",
        "in_deck_mid_B_shift_holds_whole_block": decisions.get("hidden_in_deck_mid_B") == "HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT",
        "stationary_not_flagged_and_scope_limited": decisions.get("stationary") == "NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED",
        "out_of_deck_not_mislabeled_stable": decisions.get("hidden_outside_deck_between") == "NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED",
        "schema_context_snapshot_controls_typed_separately": (
            decisions.get("schema_only") == "HOLD_SCHEMA_CHANGE" and
            decisions.get("prompt_context_drift") == "HOLD_PROMPT_CONTEXT_DRIFT" and
            decisions.get("visible_snapshot_change") == "HOLD_SNAPSHOT_CHANGED"),
        "all_route_attempts_retained": route_retained,
        "no_policy_proves_identity_from_alias_or_clean_deck": all(
            "MODEL_BEHAVIOR_UNVERIFIED" in rows[(s, p)]["candidate_disposition"] or
            "MODEL_IDENTITY_UNVERIFIED" in rows[(s, p)]["candidate_disposition"] or
            rows[(s, p)]["candidate_disposition"].startswith("HOLD_")
            for s in SCENARIOS for p in POLICIES if (s, p) in rows),
    }
    if errors:
        return {"verdict": "FAIL_AUDIT", "errors": errors[:30], "n_errors": len(errors), "gates": gates}
    verdict = "PASS_METHOD_SCOPED" if all(gates.values()) else "FAIL_METHOD"
    summaries = {f"{s}/{p}": {"decision": rows[(s, p)]["candidate_disposition"],
                 "route_A_n": len(rows[(s, p)]["route_rows"]["A"]),
                 "route_B_n": len(rows[(s, p)]["route_rows"]["B"])}
                 for s in SCENARIOS for p in POLICIES}
    return {"verdict": verdict, "n_groups": len(rows), "n_trials_per_group": N_TRIALS,
            "gates": gates, "decisions": decisions, "summary": summaries, "errors": []}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, sort_keys=True, indent=2))
    sys.exit(0 if result["verdict"] == "PASS_METHOD_SCOPED" else 1)
