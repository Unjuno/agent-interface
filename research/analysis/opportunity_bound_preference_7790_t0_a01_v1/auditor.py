#!/usr/bin/env python3
"""Independent exhaustive oracle; deliberately does not import candidate.py."""
import itertools
import json
import sys


def oracle(fixture):
    events = [e for group in fixture["observations"] for e in group["events"]]
    valid_ids, grouped, raw_counts = [], {}, {}
    for event in events:
        choice = event["selected"]
        raw_counts[choice] = raw_counts.get(choice, 0) + 1
        candidate_options = set(event["menu_options"])
        if (event["consent_status"] != "active" or event["actor"] != "user"
            or event["actor_provenance"] != "verified" or event["event_type"] != "direct_selection"
            or event["capture_complete"] is not True or event["defaulted_option"] is not None
            or event["constraint_id"] is not None or choice not in candidate_options
            or len(candidate_options) < 2
            or any(set(event[k]) != candidate_options for k in
                   ("visible_options", "noticed_options", "enabled_options", "feasible_options"))):
            continue
        valid_ids.append(event["event_id"])
        key = tuple(event[k] for k in
                    ("principal", "task_id", "consent_scope", "context_id", "context_version"))
        grouped.setdefault(key, []).append(event)

    scope_data = []
    for key, records in grouped.items():
        pairs = set()
        for record in records:
            for other in set(record["enabled_options"]) - {record["selected"]}:
                pairs.add((record["selected"], other))
        consistent = []
        for perm in itertools.permutations(fixture["preference_domain"][0]):
            if all(perm.index(winner) < perm.index(loser) for winner, loser in pairs):
                consistent.append(list(perm))
        scope_data.append({"scope": list(key), "event_ids": sorted(r["event_id"] for r in records),
                           "entailed_relations": [list(pair) for pair in sorted(pairs)],
                           "identified_orders": consistent})

    mutation_data = []
    for mutation in fixture["mutations"]:
        # Apply each mutation to the one fully admissible base trace and independently
        # evaluate opportunity completeness and scope identity.
        base = next(e for e in events if e["event_id"] == "e01")
        changed = dict(base)
        changed[mutation["field"]] = mutation["value"]
        if mutation["mutation_id"] == "change-context-version":
            result = {"mutation_id": mutation["mutation_id"], "result": "SEPARATE_SCOPE",
                      "scope_version": changed["context_version"]}
        else:
            opt = set(changed["menu_options"])
            valid = (changed["consent_status"] == "active" and changed["actor"] == "user"
                     and changed["actor_provenance"] == "verified"
                     and changed["event_type"] == "direct_selection"
                     and changed["capture_complete"] is True and changed["defaulted_option"] is None
                     and changed["constraint_id"] is None and changed["selected"] in opt and len(opt) > 1
                     and all(set(changed[k]) == opt for k in
                             ("visible_options", "noticed_options", "enabled_options", "feasible_options")))
            result = {"mutation_id": mutation["mutation_id"],
                      "result": "IDENTIFIED" if valid else "NO_IDENTIFIED_COMPARISON"}
        mutation_data.append(result)
    return {"admissible_event_ids": sorted(valid_ids),
            "naive_action_counts": dict(sorted(raw_counts.items())),
            "scopes": sorted(scope_data, key=lambda s: s["scope"]),
            "mutations": mutation_data,
            "authority": "NONE_METHOD_ONLY"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        actual = json.load(f)
    expected = oracle(fixture)
    if actual.get("schema") != "opportunity-bound-preference-candidate-output-v1" or {
            k: v for k, v in actual.items() if k != "schema"} != expected:
        print(json.dumps({"expected": expected, "actual": actual}, sort_keys=True, indent=2))
        raise SystemExit(1)
    result = {"audit": "PASS", "scope_count": len(expected["scopes"]),
                      "admissible_event_count": len(expected["admissible_event_ids"]),
                      "mutation_count": len(expected["mutations"]),
                      "order_rows": sum(len(s["identified_orders"]) for s in expected["scopes"]),
                      "authority": expected["authority"]}
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(result, f, sort_keys=True, separators=(",", ":"))
            f.write("\n")
    else:
        print(json.dumps(result, sort_keys=True))
