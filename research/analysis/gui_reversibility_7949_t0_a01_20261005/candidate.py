"""Outcome-set certificate candidate. Standard library only."""
import itertools

LABELS = ("UNIVERSALLY_UNIFORM", "UNIVERSALLY_BRANCHING", "PARTIALLY_RECOVERABLE", "UNKNOWN")


def apply(table, action, state):
    return table[action].get(state, state)


def sequences(actions, horizon):
    for n in range(horizon + 1):
        yield from itertools.product(actions, repeat=n)


def evaluate(case, model):
    outcomes = case["outcomes"]
    if not case["coverage_complete"] or not case["receipt_valid"]:
        return {"label": "UNKNOWN", "reason": "incomplete_coverage" if not case["coverage_complete"] else "invalidated_receipt", "trace": []}
    if any(x not in model["schemas"][case["schema"]] for x in outcomes):
        return {"label": "UNKNOWN", "reason": "outcome_outside_schema", "trace": []}

    table = model["recovery"][case["recovery_table"]]
    actions = tuple(table)
    target = model["target"]
    h = model["horizon"]
    rows = []
    reachable_by_outcome = {}
    for outcome in outcomes:
        reached = []
        for seq in sequences(actions, h):
            state = outcome
            path = [state]
            for action in seq:
                state = apply(table, action, state)
                path.append(state)
            if state == target:
                reached.append((seq, path))
        reachable_by_outcome[outcome] = reached
        rows.append({"outcome": outcome, "receipt": case["receipt_classes"].get(outcome), "recoveries": [{"actions": list(s), "states": p} for s, p in reached]})

    if any(not reachable_by_outcome[o] for o in outcomes):
        return {"label": "PARTIALLY_RECOVERABLE", "reason": "unreachable_outcome", "trace": rows}

    # For a uniform plan, require one sequence to recover all possible outcomes.
    common = []
    for seq in sequences(actions, h):
        final_states = []
        for outcome in outcomes:
            state = outcome
            for action in seq:
                state = apply(table, action, state)
            final_states.append(state)
        if all(s == target for s in final_states):
            common.append(list(seq))
    if common:
        return {"label": "UNIVERSALLY_UNIFORM", "reason": "common_sequence", "common_sequences": common, "trace": rows}

    # A policy can branch only on the frozen receipt class. Each class must
    # admit one common sequence for every outcome within that class.
    groups = {}
    for outcome in outcomes:
        groups.setdefault(case["receipt_classes"].get(outcome), []).append(outcome)
    policies = {}
    for receipt, group in groups.items():
        possible = []
        for seq in sequences(actions, h):
            if all(_final(table, outcome, seq) == target for outcome in group):
                possible.append(list(seq))
        if not possible:
            return {"label": "UNKNOWN", "reason": "indistinguishable_outcomes_require_different_recovery", "trace": rows}
        policies[str(receipt)] = possible
    return {"label": "UNIVERSALLY_BRANCHING", "reason": "receipt_conditioned_policy", "policies": policies, "trace": rows}


def _final(table, outcome, seq):
    state = outcome
    for action in seq:
        state = apply(table, action, state)
    return state


def run(model):
    return [{"id": case["id"], **evaluate(case, model), "static_label": "UNIVERSALLY_UNIFORM" if case["static_reversible"] else "PARTIALLY_RECOVERABLE", "expected": case["expected"]} for case in model["cases"]]
