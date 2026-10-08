"""Candidate belief-state safety synthesis for Issue #5550 T1."""

from itertools import combinations

PLANT = (
    ("READY", "ACT", "ACTED"),
    ("READY", "FOCUS_LOST", "FOCUS_LOST"),
    ("READY", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("ACTED", "COMMIT", "COMMITTED"),
    ("ACTED", "FOCUS_LOST", "FOCUS_LOST"),
    ("ACTED", "TARGET_CHANGED", "STALE"),
    ("ACTED", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("ACTED", "REVALIDATE", "READY"),
    ("FOCUS_LOST", "REACQUIRE", "READY"),
    ("FOCUS_LOST", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("STALE", "REACQUIRE", "READY"),
    ("STALE", "COMMIT", "UNSAFE_STALE_COMMIT"),
    ("STALE", "WINDOW_CLOSE", "BLOCKED_UNCONTROLLABLE"),
    ("STALE", "REVALIDATE", "READY"),
    ("COMMITTED", "ACT", "UNSAFE_DOUBLE_EFFECT"),
)
BELIEF = frozenset({"ACTED", "STALE"})
CONTROLLABLE = frozenset({"ACT", "COMMIT", "REACQUIRE", "REVALIDATE"})
UNSAFE = frozenset({"UNSAFE_STALE_COMMIT", "UNSAFE_DOUBLE_EFFECT"})


def safe_actions(belief=BELIEF, plant=PLANT):
    """Return controllable events defined and safe from every belief state."""
    edges = {(src, event): dest for src, event, dest in plant}
    result = set()
    for event in CONTROLLABLE:
        destinations = [edges.get((state, event)) for state in belief]
        if all(dest is not None and dest not in UNSAFE for dest in destinations):
            result.add(event)
    return result


def enumerate_subsets():
    """Enumerate every edge subset and select all maximal safe belief policies."""
    eligible = sorted((s, e, d) for s, e, d in PLANT
                      if e in CONTROLLABLE and s in BELIEF)
    valid = []
    for size in range(len(eligible) + 1):
        for subset in combinations(eligible, size):
            by_event = {}
            for src, event, dest in subset:
                by_event.setdefault(event, {})[src] = dest
            if all(
                event in by_event
                and all(state in by_event[event] and by_event[event][state] not in UNSAFE
                        for state in BELIEF)
                for event in by_event
            ):
                valid.append(frozenset(subset))
    maximal = [candidate for candidate in valid if not any(
        candidate < other for other in valid
    )]
    return eligible, valid, maximal


def result():
    enabled = sorted(safe_actions())
    eligible, valid, maximal = enumerate_subsets()
    return {
        "schema": "issue-5550-t1-belief-observability-v1",
        "observation_class": "TARGET_STATE_UNCERTAIN",
        "belief_states": sorted(BELIEF),
        "candidate_enabled_actions": enabled,
        "eligible_controllable_edges": len(eligible),
        "safe_edge_subsets": len(valid),
        "maximal_safe_edge_subsets": len(maximal),
        "maximal_policy_actions": sorted({event for _, event, _ in next(iter(maximal))}) if maximal else [],
        "commit_disabled_due_to_stale_member": "COMMIT" not in enabled,
        "revalidate_retained": "REVALIDATE" in enabled,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(result(), sort_keys=True, separators=(",", ":")))
