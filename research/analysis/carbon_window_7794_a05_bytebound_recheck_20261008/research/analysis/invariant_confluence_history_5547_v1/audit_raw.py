"""Separate raw-only audit. Does not import model.py or run_model.py."""
import json
import sys
from copy import deepcopy
from pathlib import Path


def state_errors(state):
    errors = []
    by_effect = {}
    for _, effect in state["commits"]:
        by_effect[effect] = by_effect.get(effect, 0) + 1
    if any(n > 1 for n in by_effect.values()):
        errors.append("duplicate_semantic_effect")
    if any(effect not in state["authorized"] for _, effect in state["commits"]):
        errors.append("commit_without_authorization")
    return sorted(errors)


def joined(left, right):
    return {"authorized": sorted(set(left["authorized"]) | set(right["authorized"])),
            "commits": [list(x) for x in sorted({tuple(x) for x in left["commits"]} | {tuple(x) for x in right["commits"]})]}


def reference_transition(state, command):
    authorized, commits = state
    if command[0] == "AUTHORIZE" and len(command) == 2:
        return frozenset(set(authorized) | {command[1]}), commits
    if command[0] == "COMMIT" and len(command) == 3:
        dispatch, effect = command[1], command[2]
        if effect not in authorized or any(existing == effect for _, existing in commits):
            return None
        return authorized, frozenset(set(commits) | {(dispatch, effect)})
    return None


def reference_matrix(commands, depth):
    states = {(frozenset(), frozenset())}
    frontier = set(states)
    for _ in range(depth):
        following = set()
        for state in frontier:
            for command in commands:
                next_state = reference_transition(state, command)
                if next_state is not None and next_state not in states:
                    states.add(next_state)
                    following.add(next_state)
        frontier = following
    pairs = set()
    for authorized, commits in states:
        base = {"authorized": sorted(authorized), "commits": [list(x) for x in sorted(commits)]}
        enabled = [command for command in commands if reference_transition((authorized, commits), command) is not None]
        for left in enabled:
            for right in enabled:
                pairs.add(json.dumps([base, left, right], sort_keys=True, separators=(",", ":")))
    return states, pairs


def audit(raw, expected):
    errors = []
    if raw.get("source_main") != expected.get("source_main"):
        errors.append("source_main")
    rows = raw.get("pair_rows")
    if not isinstance(rows, list) or len(rows) != raw.get("pair_row_count"):
        return ["pair_row_count"]
    observed_conflicts = []
    row_keys = set()
    serial_safe = True
    for i, row in enumerate(rows):
        key = json.dumps([row["base"], row["left_command"], row["right_command"]], sort_keys=True, separators=(",", ":"))
        if key in row_keys:
            errors.append(f"row:{i}:duplicate_pair")
        row_keys.add(key)
        expected_join = joined(row["left_state"], row["right_state"])
        if row.get("joined_state") != expected_join:
            errors.append(f"row:{i}:join_reconstruction")
        found = state_errors(expected_join)
        if row.get("join_errors") != found:
            errors.append(f"row:{i}:invariant_receipt")
        if found:
            observed_conflicts.append(row)
        for j, order in enumerate(row.get("serial_orders", [])):
            independent = state_errors(order["state"])
            if independent != order.get("errors"):
                errors.append(f"row:{i}:serial:{j}")
            if independent:
                serial_safe = False
    reference_states, reference_pairs = reference_matrix(expected["commands"], 2)
    if len(reference_states) != expected["reachable_state_count"] or len(reference_pairs) != expected["pair_row_count"]:
        errors.append("frozen_reference_matrix")
    if len(rows) != expected["pair_row_count"] or row_keys != reference_pairs:
        errors.append("enumeration_completeness")
    if raw.get("state_count") != expected["reachable_state_count"]:
        errors.append("state_count")
    if len(observed_conflicts) != raw.get("counterexample_count"):
        errors.append("counterexample_count")
    if raw.get("counterexamples") != observed_conflicts:
        errors.append("counterexample_rows")
    left_expected = expected["expected_counterexample"]["left"]
    right_expected = expected["expected_counterexample"]["right"]
    history = expected["expected_counterexample"]["history"]
    base_expected = {"authorized": sorted({event[1] for event in history if event[0] == "AUTHORIZE"}), "commits": []}
    witnesses = [row for row in observed_conflicts
                 if row["base"] == base_expected
                 and row["left_command"] == left_expected
                 and row["right_command"] == right_expected]
    reverse_witnesses = [row for row in observed_conflicts
                         if row["base"] == base_expected
                         and row["left_command"] == right_expected
                         and row["right_command"] == left_expected]
    if not witnesses or not reverse_witnesses:
        errors.append("expected_witness_missing")
    elif any(order.get("second_outcome") != "second_rejected" for order in witnesses[0]["serial_orders"]):
        errors.append("serial_baseline")
    if raw.get("root_commit_enabled") is not False or raw.get("root_only_commit_classification") != expected["root_only_commit_classification"]:
        errors.append("root_only_gate")
    if raw.get("serializable_all_orders_safe") is not serial_safe or not serial_safe:
        errors.append("serial_summary")
    if raw.get("disposition") != "PASS_HISTORY_DEPENDENT_COUNTEREXAMPLE":
        errors.append("disposition")
    return errors


def mutation_controls(raw, expected):
    mutations = {}
    x = deepcopy(raw); x["counterexamples"] = []; x["counterexample_count"] = 0; mutations["drop_counterexample"] = x
    x = deepcopy(raw); x["pair_rows"][0]["joined_state"]["commits"] = []; mutations["erase_merged_commit"] = x
    x = deepcopy(raw); x["pair_rows"][0]["join_errors"] = []; mutations["hide_join_violation"] = x
    x = deepcopy(raw); x["root_only_commit_classification"] = "MONOTONE_SAFE"; mutations["certify_root_commit_safe"] = x
    x = deepcopy(raw); x["serializable_all_orders_safe"] = False; mutations["flip_serializable_summary"] = x
    return {name: bool(audit(candidate, expected)) for name, candidate in mutations.items()}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))
    errors = audit(raw, expected)
    controls = mutation_controls(raw, expected)
    passed = not errors and all(controls.values())
    print(json.dumps({"passed": passed, "errors": errors,
                      "mutation_controls": {"rejected": sum(controls.values()), "total": len(controls), "results": controls},
                      "counterexamples": raw.get("counterexample_count")}, sort_keys=True))
    raise SystemExit(0 if passed else 1)
