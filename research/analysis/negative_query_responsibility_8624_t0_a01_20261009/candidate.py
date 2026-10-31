#!/usr/bin/env python3
"""Candidate signed-fact responsibility analysis for a finite stratified query."""
import itertools
import json
import sys
from pathlib import Path


def rule_body_true(body, facts, derived):
    for name, expected in body:
        actual = derived[name] if name in derived else facts[name]
        if actual != expected:
            return False
    return True


def evaluate(case, assignment):
    heads = {}
    for rule in case["rules"]:
        if rule["head"] in heads and heads[rule["head"]] != rule["stratum"]:
            raise ValueError("a derived head has multiple strata")
        heads[rule["head"]] = rule["stratum"]
    derived = {}
    strata = sorted({rule["stratum"] for rule in case["rules"]})
    for level in strata:
        level_rules = [rule for rule in case["rules"] if rule["stratum"] == level]
        for rule in level_rules:
            for name, _ in rule["body"]:
                if name in heads and heads[name] >= level:
                    raise ValueError("derived dependency is not in a lower stratum")
            derived.setdefault(rule["head"], False)
            if rule_body_true(rule["body"], assignment, derived):
                derived[rule["head"]] = True
    return derived


def outcome(case, assignment):
    if case["complete"] is not True:
        return "UNKNOWN"
    derived = evaluate(case, assignment)
    matched = any(rule_body_true(term, assignment, derived)
                  for term in case["query"]["or"])
    return "MATCH" if matched else "NO_MATCH"


def minimal_positive_supports(case, assignment):
    derived = evaluate(case, assignment)
    proof_sets = {}
    for level in sorted({rule["stratum"] for rule in case["rules"]}):
        for rule in case["rules"]:
            if rule["stratum"] != level or not rule_body_true(rule["body"], assignment, derived):
                continue
            combos = [set()]
            for name, expected in rule["body"]:
                if not expected:
                    continue
                if name in derived:
                    options = proof_sets.get(name, [])
                    combos = [left | right for left in combos for right in options]
                elif assignment[name]:
                    for combo in combos:
                        combo.add(name)
            proof_sets.setdefault(rule["head"], []).extend(combos)
        for head, family in list(proof_sets.items()):
            unique = sorted({tuple(sorted(s)) for s in family}, key=lambda s: (len(s), s))
            proof_sets[head] = [set(s) for s in unique if not any(set(t) < set(s) for t in unique)]
    query_supports = []
    for term in case["query"]["or"]:
        options = [set()]
        satisfied = True
        for name, expected in term:
            value = derived[name] if name in derived else assignment[name]
            if value != expected:
                satisfied = False
                break
            if expected:
                support_options = proof_sets.get(name, []) if name in derived else [{name}]
                options = [left | right for left in options for right in support_options]
        if satisfied:
            query_supports.extend(options)
    def minimal(family):
        unique = sorted({tuple(sorted(s)) for s in family}, key=lambda s: (len(s), s))
        return [list(s) for s in unique if not any(set(t) < set(s) for t in unique)]
    return {"query": minimal(query_supports),
            "eligible": minimal(proof_sets.get("eligible", []))}


def assignments(case):
    names = list(case["mutable"])
    for bits in itertools.product((False, True), repeat=len(names)):
        state = dict(case["facts"])
        state.update(zip(names, bits))
        yield state


def flip_set(actual, state, mutable):
    return sorted(name for name in mutable if actual[name] != state[name])


def analyze(case, max_worlds):
    if case.get("endpoint") != "final_match_v1":
        raise ValueError("unknown outcome endpoint")
    if case.get("mutable") != case.get("declared_mutable_universe"):
        raise ValueError("intervention domain differs from frozen mutable universe")
    if set(case["facts"]) != set(case.get("fact_universe", [])):
        raise ValueError("invalid fact domain")
    if not set(case["mutable"]).issubset(case["fact_universe"]):
        raise ValueError("intervention fact is outside the fact universe")
    mutable = case["mutable"]
    signed = [f"{name}={'true' if case['facts'][name] else 'false'}" for name in sorted(case["facts"])]
    worlds = 1 << len(mutable)
    supports = minimal_positive_supports(case, case["facts"])
    base = {"case_id": case["id"], "scope": case["scope"], "epoch": case["epoch"],
            "signed_facts": signed, "minimal_positive_match_supports": supports["query"],
            "positive_eligibility_supports": supports["eligible"],
            "enumerated_worlds": 0, "explanation_complete": False}
    if case["complete"] is not True:
        return {**base, "status": "UNKNOWN_INCOMPLETE", "outcome": "UNKNOWN",
                "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    if worlds > max_worlds:
        return {**base, "status": "UNKNOWN_TOO_LARGE", "outcome": outcome(case, case["facts"]),
                "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    observed = outcome(case, case["facts"])
    all_states = list(assignments(case))
    base.update({"status": "READY", "outcome": observed, "enumerated_worlds": len(all_states),
                 "explanation_complete": True})
    if observed != "NO_MATCH":
        return {**base, "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    matches = [(state, flip_set(case["facts"], state, mutable)) for state in all_states
               if outcome(case, state) == "MATCH"]
    if matches:
        radius = min(len(toggles) for _, toggles in matches)
        min_flips = sorted([toggles for _, toggles in matches if len(toggles) == radius])
    else:
        radius, min_flips = None, []
    causes = {}
    for fact in mutable:
        witnesses = []
        others = [name for name in mutable if name != fact]
        for state in all_states:
            if state[fact] != case["facts"][fact] or outcome(case, state) != "NO_MATCH":
                continue
            flipped = dict(state)
            flipped[fact] = not flipped[fact]
            if outcome(case, flipped) == "MATCH":
                witnesses.append(flip_set(case["facts"], state, others))
        if witnesses:
            minimum = min(len(w) for w in witnesses)
            contingencies = sorted({tuple(w) for w in witnesses if len(w) == minimum})
            causes[fact] = {"literal": case["facts"][fact], "minimum_contingency": minimum,
                            "contingencies": [list(w) for w in contingencies],
                            "responsibility": 1.0 / (1 + minimum)}
    base.update({"robustness_radius": radius, "minimum_flip_sets": min_flips,
                 "actual_causes": causes})
    return base


def main():
    source, dest = map(Path, sys.argv[1:3])
    packet = json.loads(source.read_text())
    rows = [analyze(case, packet["max_worlds"]) for case in packet["cases"]]
    dest.write_text(json.dumps({"schema": "negative-query-responsibility-candidate-v1",
                                "rows": rows}, sort_keys=True, indent=2) + "\n")
    print(f"candidate rows={len(rows)} statuses=" + ",".join(row["status"] for row in rows))


if __name__ == "__main__":
    main()
