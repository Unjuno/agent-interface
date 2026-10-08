"""Independent literal-table audit for Issue #5550 raw output."""

import json
from itertools import combinations
import sys

EVENTS = ("ACT", "COMMIT", "REACQUIRE", "FOCUS_LOST", "TARGET_CHANGED", "WINDOW_CLOSE")
CONTROLLED = {"ACT", "COMMIT", "REACQUIRE"}
PLANT_ROWS = (
    ("READY", "ACT", "ACTED"), ("READY", "FOCUS_LOST", "FOCUS_LOST"),
    ("READY", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("ACTED", "COMMIT", "COMMITTED"), ("ACTED", "FOCUS_LOST", "FOCUS_LOST"),
    ("ACTED", "TARGET_CHANGED", "STALE"), ("ACTED", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("FOCUS_LOST", "REACQUIRE", "READY"),
    ("FOCUS_LOST", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("STALE", "REACQUIRE", "READY"), ("STALE", "COMMIT", "UNSAFE_STALE_COMMIT"),
    ("STALE", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("COMMITTED", "ACT", "UNSAFE_DOUBLE_EFFECT"),
)
TABLE = {(a, b): c for a, b, c in PLANT_ROWS}
SAFE_POLICY = {
    "READY": {"ACT"}, "ACTED": {"COMMIT"}, "FOCUS_LOST": {"REACQUIRE"},
    "STALE": {"REACQUIRE"}, "COMMITTED": set(), "BLOCKED_UNCONTROLLABLE": set(),
}
UNSAFE = {"UNSAFE_STALE_COMMIT", "UNSAFE_DOUBLE_EFFECT"}
TERMINAL = {"COMMITTED", "BLOCKED_UNCONTROLLABLE", *UNSAFE}


def expected():
    # Independent breadth-first replay from literals; no candidate import.
    result = []
    for policy in ("fail_closed", "greedy_allow_list", "synthesized"):
        queue = [("READY", (), 0)]
        cursor = 0
        visited = {("READY", ())}
        while cursor < len(queue):
            state, trace, depth = queue[cursor]
            cursor += 1
            terminal = state in {"BLOCKED_UNCONTROLLABLE", *UNSAFE} or (
                state == "COMMITTED" and policy != "greedy_allow_list"
            )
            if depth == 5 or terminal:
                continue
            for event in EVENTS:
                dest = TABLE.get((state, event))
                if dest is None:
                    continue
                if event in CONTROLLED:
                    if policy == "synthesized" and event not in SAFE_POLICY.get(state, set()):
                        continue
                    if policy == "fail_closed" and state in {"FOCUS_LOST", "STALE"}:
                        continue
                new_trace = trace + (event,)
                result.append({
                    "policy": policy, "trace": list(new_trace), "source": state,
                    "event": event, "controllable": event in CONTROLLED,
                    "destination": dest, "unsafe": dest in UNSAFE,
                    "completed": dest == "COMMITTED",
                    "blocked": dest == "BLOCKED_UNCONTROLLABLE",
                })
                key = (dest, new_trace)
                if key not in visited:
                    visited.add(key)
                    queue.append((dest, new_trace, depth + 1))
    return result


def maximal_policy_by_enumeration():
    """Brute-force every subset of controllable plant edges; union valid policies."""
    controllable_edges = [(s, e, d) for s, e, d in PLANT_ROWS if e in CONTROLLED]
    valid = []
    for count in range(len(controllable_edges) + 1):
        for chosen in combinations(controllable_edges, count):
            allowed = set(chosen)
            outgoing = {}
            for source, event, dest in PLANT_ROWS:
                if event not in CONTROLLED or (source, event, dest) in allowed:
                    outgoing.setdefault(source, []).append(dest)
            reachable = {"READY"}
            frontier = ["READY"]
            while frontier:
                source = frontier.pop()
                for dest in outgoing.get(source, []):
                    if dest not in reachable:
                        reachable.add(dest)
                        frontier.append(dest)
            if reachable & UNSAFE:
                continue
            can_finish = {"COMMITTED", "BLOCKED_UNCONTROLLABLE"}
            changed = True
            while changed:
                before = len(can_finish)
                can_finish.update(
                    source for source, destinations in outgoing.items()
                    if any(dest in can_finish for dest in destinations)
                )
                changed = len(can_finish) != before
            if not reachable <= can_finish:
                continue
            valid.append(allowed)
    union = set().union(*valid) if valid else set()
    all_states = {"READY"} | {s for s, _, _ in PLANT_ROWS} | {d for _, _, d in PLANT_ROWS}
    winning = set(all_states)
    for _, _, dest in PLANT_ROWS:
        if dest in UNSAFE:
            winning.discard(dest)
    enabled = {
        state: sorted(event for source, event, dest in union if source == state and dest in winning)
        for state in sorted(all_states)
    }
    return winning, enabled, len(valid)


def audit(raw):
    errors = []
    if raw.get("schema") != "issue-5550-finite-supervisor-raw-v1":
        errors.append("schema")
    if raw.get("max_depth") != 5 or raw.get("plant_transition_count") != len(PLANT_ROWS):
        errors.append("frozen_parameters")
    if raw.get("policies") != ["fail_closed", "greedy_allow_list", "synthesized"]:
        errors.append("policy_set")
    winning, enabled, valid_count = maximal_policy_by_enumeration()
    if raw.get("synthesized_winning_states") != sorted(winning):
        errors.append("synthesized_winning_region")
    if raw.get("synthesized_enabled") != enabled:
        errors.append("maximally_permissive_enabled_set")
    actual = raw.get("rows")
    if not isinstance(actual, list) or actual != expected():
        errors.append("complete_independent_replay")
    if isinstance(actual, list):
        synth = [r for r in actual if r.get("policy") == "synthesized"]
        if any(r.get("unsafe") for r in synth):
            errors.append("synthesized_unsafe_transition")
        if not any(r.get("destination") == "COMMITTED" for r in synth):
            errors.append("no_safe_completion")
        if not any(r.get("destination") == "BLOCKED_UNCONTROLLABLE" for r in synth):
            errors.append("missing_uncontrollable_block")
        if not any(r.get("destination") == "UNSAFE_STALE_COMMIT" and r.get("policy") == "greedy_allow_list" for r in actual):
            errors.append("greedy_stale_mutant_not_exposed")
        if not any(r.get("destination") == "UNSAFE_DOUBLE_EFFECT" and r.get("policy") == "greedy_allow_list" for r in actual):
            errors.append("greedy_duplicate_mutant_not_exposed")
    summary = {
        "rows": len(actual) if isinstance(actual, list) else None,
        "unsafe_greedy": sum(bool(r.get("unsafe")) for r in actual or [] if r.get("policy") == "greedy_allow_list"),
        "unsafe_synthesized": sum(bool(r.get("unsafe")) for r in actual or [] if r.get("policy") == "synthesized"),
        "completed_synthesized": sum(bool(r.get("completed")) for r in actual or [] if r.get("policy") == "synthesized"),
        "blocked_synthesized": sum(bool(r.get("blocked")) for r in actual or [] if r.get("policy") == "synthesized"),
        "valid_supervisors_exhaustively_enumerated": valid_count,
        "errors": errors,
        "status": "PASS_T0_SYNTHETIC_SCOPE" if not errors else "FAIL_AUDIT",
    }
    return summary


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(json.dumps(audit(json.load(f)), sort_keys=True, separators=(",", ":")))
