#!/usr/bin/env python3
"""Candidate opportunity-bound inference for a finite synthetic fixture."""
import json
import sys
from collections import Counter, defaultdict


def scope_key(event):
    return (event["principal"], event["task_id"], event["consent_scope"],
            event["context_id"], event["context_version"])


def admissible(event):
    options = set(event["menu_options"])
    selected = event["selected"]
    return all((
        event["consent_status"] == "active",
        event["actor"] == "user",
        event["actor_provenance"] == "verified",
        event["event_type"] == "direct_selection",
        event["capture_complete"] is True,
        event["defaulted_option"] is None,
        event["constraint_id"] is None,
        options == set(event["visible_options"]) == set(event["noticed_options"])
        == set(event["enabled_options"]) == set(event["feasible_options"]),
        selected in options,
        len(options) >= 2,
    ))


def run(fixture):
    by_scope = defaultdict(list)
    naive = Counter()
    all_events = [e for case in fixture["observations"] for e in case["events"]]
    for event in all_events:
        naive[event["selected"]] += 1
        if admissible(event):
            by_scope[scope_key(event)].append(event)

    scopes = []
    for key, events in sorted(by_scope.items()):
        constraints = sorted({(e["selected"], x)
                              for e in events for x in e["enabled_options"]
                              if x != e["selected"]})
        orders = [order for order in fixture["preference_domain"]
                  if all(order.index(a) < order.index(b) for a, b in constraints)]
        orders.sort()
        scopes.append({"scope": list(key), "event_ids": sorted(e["event_id"] for e in events),
                       "entailed_relations": [list(x) for x in constraints],
                       "identified_orders": orders})

    mutation_results = []
    base = next(e for e in all_events if e["event_id"] == "e01")
    for mutation in fixture["mutations"]:
        changed = dict(base)
        changed[mutation["field"]] = mutation["value"]
        if mutation["mutation_id"] == "change-context-version":
            mutation_results.append({"mutation_id": mutation["mutation_id"],
                                     "result": "SEPARATE_SCOPE",
                                     "scope_version": changed["context_version"]})
        else:
            mutation_results.append({"mutation_id": mutation["mutation_id"],
                                     "result": "IDENTIFIED" if admissible(changed) else "NO_IDENTIFIED_COMPARISON"})
    return {"schema": "opportunity-bound-preference-candidate-output-v1",
            "naive_action_counts": dict(sorted(naive.items())),
            "admissible_event_ids": sorted(e["event_id"] for e in all_events if admissible(e)),
            "scopes": scopes, "mutations": mutation_results,
            "authority": "NONE_METHOD_ONLY"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    output = json.dumps(run(fixture), sort_keys=True, separators=(",", ":")) + "\n"
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output, end="")
