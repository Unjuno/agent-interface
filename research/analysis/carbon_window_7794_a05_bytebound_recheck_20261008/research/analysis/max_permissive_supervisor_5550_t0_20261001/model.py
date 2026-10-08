"""Finite, explicit DES fixture for Issue #5550 T0 (synthetic only)."""

from collections import deque

EVENTS = ("ACT", "COMMIT", "REACQUIRE", "FOCUS_LOST", "TARGET_CHANGED", "WINDOW_CLOSE")
CONTROLLABLE = {"ACT", "COMMIT", "REACQUIRE"}
INITIAL = "READY"
MARKED = {"COMMITTED", "BLOCKED_UNCONTROLLABLE"}
UNSAFE = {"UNSAFE_STALE_COMMIT", "UNSAFE_DOUBLE_EFFECT"}

# Plant transitions; each row is (source, event, destination).
PLANT = (
    ("READY", "ACT", "ACTED"),
    ("READY", "FOCUS_LOST", "FOCUS_LOST"),
    ("READY", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("ACTED", "COMMIT", "COMMITTED"),
    ("ACTED", "FOCUS_LOST", "FOCUS_LOST"),
    ("ACTED", "TARGET_CHANGED", "STALE"),
    ("ACTED", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("FOCUS_LOST", "REACQUIRE", "READY"),
    ("FOCUS_LOST", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("STALE", "REACQUIRE", "READY"),
    ("STALE", "COMMIT", "UNSAFE_STALE_COMMIT"),
    ("STALE", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("COMMITTED", "ACT", "UNSAFE_DOUBLE_EFFECT"),
)
TRANSITIONS = {(s, e): d for s, e, d in PLANT}

# Greatest safe, nonblocking permissive policy for this declared plant/spec.
SYNTHESIZED = {
    # Populated by synthesize(); placeholder only for module initialization.
}


def synthesize():
    """Compute the supremal safe, nonblocking region for this fully observed DFA."""
    states = {INITIAL} | {s for s, _, _ in PLANT} | {d for _, _, d in PLANT}
    safe = states - UNSAFE
    marked = set(MARKED)
    while True:
        controllable_safe = {
            state for state in safe
            if all(dest in safe for src, event, dest in PLANT
                   if src == state and event not in CONTROLLABLE)
        }
        coaccessible = marked & controllable_safe
        changed = True
        while changed:
            before = len(coaccessible)
            coaccessible.update(
                src for src, event, dest in PLANT
                if src in controllable_safe and dest in coaccessible
                and (event not in CONTROLLABLE or dest in controllable_safe)
            )
            changed = len(coaccessible) != before
        next_safe = controllable_safe & coaccessible
        if next_safe == safe:
            break
        safe = next_safe
    enabled = {
        state: {
            event for src, event, dest in PLANT
            if src == state and event in CONTROLLABLE
            and src in safe and dest in safe
        }
        for state in states
    }
    return safe, enabled


_WINNING_STATES, SYNTHESIZED = synthesize()


def enabled(state, policy):
    if policy == "synthesized":
        return SYNTHESIZED.get(state, set())
    events = {e for s, e, _ in PLANT if s == state}
    if policy == "greedy_allow_list":
        return events
    if policy == "fail_closed":
        return set() if state in {"FOCUS_LOST", "STALE"} else events
    raise ValueError(policy)


def explore(policy, max_depth=5):
    """Enumerate all distinct reachable traces to the declared depth."""
    queue = deque([(INITIAL, (), False)])
    seen = {(INITIAL, (), False)}
    rows = []
    while queue:
        state, trace, committed = queue.popleft()
        terminal = state in {"BLOCKED_UNCONTROLLABLE", *UNSAFE} or (
            state == "COMMITTED" and policy != "greedy_allow_list"
        )
        if len(trace) >= max_depth or terminal:
            continue
        for event in EVENTS:
            dest = TRANSITIONS.get((state, event))
            if dest is None:
                continue
            if event in CONTROLLABLE and event not in enabled(state, policy):
                continue
            next_trace = trace + (event,)
            row = {
                "policy": policy,
                "trace": list(next_trace),
                "source": state,
                "event": event,
                "controllable": event in CONTROLLABLE,
                "destination": dest,
                "unsafe": dest in UNSAFE,
                "completed": dest == "COMMITTED",
                "blocked": dest == "BLOCKED_UNCONTROLLABLE",
            }
            rows.append(row)
            item = (dest, next_trace, committed or dest == "COMMITTED")
            if item not in seen:
                seen.add(item)
                queue.append(item)
    return rows


def run():
    rows = [row for policy in ("fail_closed", "greedy_allow_list", "synthesized")
            for row in explore(policy)]
    return {
        "schema": "issue-5550-finite-supervisor-raw-v1",
        "max_depth": 5,
        "plant_transition_count": len(PLANT),
        "policies": ["fail_closed", "greedy_allow_list", "synthesized"],
        "synthesized_winning_states": sorted(_WINNING_STATES),
        "synthesized_enabled": {state: sorted(events) for state, events in sorted(SYNTHESIZED.items())},
        "rows": rows,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
