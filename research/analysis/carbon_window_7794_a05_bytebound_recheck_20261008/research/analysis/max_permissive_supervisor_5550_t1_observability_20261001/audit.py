"""Independent raw-only audit for Issue #5550 T1; does not import candidate."""

import copy
import json
import sys
from itertools import combinations
from pathlib import Path

BELIEF = {"ACTED", "STALE"}
CONTROLLED = {"ACT", "COMMIT", "REACQUIRE", "REVALIDATE"}
UNSAFE = {"UNSAFE_STALE_COMMIT", "UNSAFE_DOUBLE_EFFECT"}
# Independently transcribed from the preregistered T1 plant.
EDGES = (
    ("ACTED", "COMMIT", "COMMITTED"),
    ("ACTED", "REVALIDATE", "READY"),
    ("STALE", "COMMIT", "UNSAFE_STALE_COMMIT"),
    ("STALE", "REACQUIRE", "READY"),
    ("STALE", "REVALIDATE", "READY"),
)


def oracle():
    valid = []
    for size in range(len(EDGES) + 1):
        for subset in combinations(EDGES, size):
            by_event = {}
            for source, event, target in subset:
                by_event.setdefault(event, {})[source] = target
            safe = True
            for event, transitions in by_event.items():
                if set(transitions) != BELIEF:
                    safe = False
                if any(target in UNSAFE for target in transitions.values()):
                    safe = False
            if safe:
                valid.append(frozenset(subset))
    maximal = [item for item in valid if not any(item < other for other in valid)]
    actions = sorted({event for item in maximal for _, event, _ in item})
    return {
        "belief_states": sorted(BELIEF),
        "candidate_enabled_actions": actions,
        "eligible_controllable_edges": len(EDGES),
        "safe_edge_subsets": len(valid),
        "maximal_safe_edge_subsets": len(maximal),
        "maximal_policy_actions": actions,
        "commit_disabled_due_to_stale_member": "COMMIT" not in actions,
        "revalidate_retained": "REVALIDATE" in actions,
    }


def assess(raw):
    expected = oracle()
    errors = []
    if raw.get("schema") != "issue-5550-t1-belief-observability-v1":
        errors.append("schema")
    for key, value in expected.items():
        if raw.get(key) != value:
            errors.append(key)
    if raw.get("observation_class") != "TARGET_STATE_UNCERTAIN":
        errors.append("observation_class")
    return errors


def corruption_controls(raw):
    mutations = []
    bad = copy.deepcopy(raw)
    bad["candidate_enabled_actions"] = ["COMMIT", "REVALIDATE"]
    mutations.append(bad)
    bad = copy.deepcopy(raw)
    bad["candidate_enabled_actions"] = []
    mutations.append(bad)
    bad = copy.deepcopy(raw)
    bad["belief_states"] = ["ACTED"]
    mutations.append(bad)
    bad = copy.deepcopy(raw)
    bad["safe_edge_subsets"] += 1
    mutations.append(bad)
    return sum(bool(assess(item)) for item in mutations), len(mutations)


def main(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = assess(raw)
    rejected, total = corruption_controls(raw)
    result = {
        "schema": "issue-5550-t1-independent-audit-v1",
        "disposition": "PASS_T1_SYNTHETIC_SCOPE" if not errors and rejected == total else "STOP_AUDIT",
        "errors": errors,
        "oracle": oracle(),
        "corruption_controls_rejected": rejected,
        "corruption_controls_total": total,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["disposition"] == "PASS_T1_SYNTHETIC_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
