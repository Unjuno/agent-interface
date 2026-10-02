"""Candidate finite-state model for history-dependent join safety."""
from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class State:
    authorized: frozenset = frozenset()
    commits: frozenset = frozenset()


INITIAL = State()
COMMANDS = (
    ("AUTHORIZE", "effect-a"),
    ("AUTHORIZE", "effect-b"),
    ("COMMIT", "dispatch-0", "effect-a"),
    ("COMMIT", "dispatch-1", "effect-a"),
)


def apply(state, command):
    if command[0] == "AUTHORIZE" and len(command) == 2:
        return State(state.authorized | {command[1]}, state.commits)
    if command[0] == "COMMIT" and len(command) == 3:
        dispatch, effect = command[1:]
        if effect not in state.authorized:
            return None
        if any(existing_effect == effect for _, existing_effect in state.commits):
            return None
        return State(state.authorized, state.commits | {(dispatch, effect)})
    return None


def join(left, right):
    return State(left.authorized | right.authorized, left.commits | right.commits)


def violations(state):
    errors = []
    counts = {}
    for _, effect in state.commits:
        counts[effect] = counts.get(effect, 0) + 1
    if any(count > 1 for count in counts.values()):
        errors.append("duplicate_semantic_effect")
    if any(effect not in state.authorized for _, effect in state.commits):
        errors.append("commit_without_authorization")
    return sorted(errors)


def as_dict(state):
    return {"authorized": sorted(state.authorized),
            "commits": [list(x) for x in sorted(state.commits)]}


def enumerate_states(max_depth=2):
    frontier = {INITIAL}
    seen = {INITIAL}
    for _ in range(max_depth):
        next_frontier = set()
        for state in frontier:
            for command in COMMANDS:
                result = apply(state, command)
                if result is not None and result not in seen:
                    seen.add(result)
                    next_frontier.add(result)
        frontier = next_frontier
    return sorted(seen, key=lambda s: (len(s.authorized), len(s.commits), as_dict(s)["authorized"], as_dict(s)["commits"]))


def serial_pair(base, left_command, right_command):
    outcomes = []
    for first, second in ((left_command, right_command), (right_command, left_command)):
        first_state = apply(base, first)
        if first_state is None:
            outcomes.append((base, "first_rejected"))
            continue
        second_state = apply(first_state, second)
        outcomes.append((first_state if second_state is None else second_state,
                         "second_rejected" if second_state is None else "both_accepted"))
    return outcomes


def execute():
    states = enumerate_states(2)
    rows = []
    conflicts = []
    for base_index, base in enumerate(states):
        enabled = [(cmd, apply(base, cmd)) for cmd in COMMANDS]
        enabled = [(cmd, result) for cmd, result in enabled if result is not None]
        for (left_cmd, left_state), (right_cmd, right_state) in product(enabled, repeat=2):
            merged = join(left_state, right_state)
            errors = violations(merged)
            serial = serial_pair(base, left_cmd, right_cmd)
            row = {
                "base": as_dict(base),
                "left_command": list(left_cmd),
                "right_command": list(right_cmd),
                "left_state": as_dict(left_state),
                "right_state": as_dict(right_state),
                "joined_state": as_dict(merged),
                "join_errors": errors,
                "serial_orders": [{"state": as_dict(state), "second_outcome": outcome,
                                   "errors": violations(state)} for state, outcome in serial],
            }
            rows.append(row)
            if errors:
                conflicts.append(row)
    root_commit_enabled = any(apply(INITIAL, cmd) is not None and cmd[0] == "COMMIT" for cmd in COMMANDS)
    serial_safe = all(not order["errors"] for row in rows for order in row["serial_orders"])
    witness = next((row for row in conflicts
                    if row["base"] == {"authorized": ["effect-a"], "commits": []}
                    and row["left_command"][0] == "COMMIT"
                    and row["right_command"][0] == "COMMIT"), None)
    return {
        "schema": "issue-5547-history-closure-raw-v1",
        "allocation": "ic-history-closure-5547-20261001-02",
        "source_main": "2b2166da7e1e3b4e60e435b6c7857484797a23ec",
        "state_count": len(states),
        "max_history_depth": 2,
        "root_commit_enabled": root_commit_enabled,
        "root_only_commit_classification": "COORDINATION_REQUIRED" if root_commit_enabled else "NOT_PROVEN_PRECONDITION_FALSE",
        "pair_row_count": len(rows),
        "pair_rows": rows,
        "counterexample_count": len(conflicts),
        "counterexamples": conflicts,
        "expected_witness_found": witness is not None,
        "serializable_all_orders_safe": serial_safe,
        "disposition": "PASS_HISTORY_DEPENDENT_COUNTEREXAMPLE" if witness and not root_commit_enabled and serial_safe else "FAIL_OR_UNCERTAIN",
    }
