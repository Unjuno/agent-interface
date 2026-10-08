#!/usr/bin/env python3
"""Independent exhaustive intervention oracle; does not import candidate.py."""
import itertools
import json
import sys
from pathlib import Path


def derive(case, world):
    levels = sorted(set(rule["stratum"] for rule in case["rules"]))
    head_level = {}
    for rule in case["rules"]:
        previous = head_level.setdefault(rule["head"], rule["stratum"])
        if previous != rule["stratum"]:
            raise ValueError("one head assigned to multiple strata")
    known = {}
    for level in levels:
        group = [r for r in case["rules"] if r["stratum"] == level]
        for rule in group:
            if any(atom in head_level and head_level[atom] >= level for atom, _ in rule["body"]):
                raise ValueError("non-stratified dependency")
        # All dependencies are lower-stratum or extensional facts, so this level is simultaneous.
        results = {}
        for rule in group:
            satisfied = True
            for atom, required in rule["body"]:
                value = known[atom] if atom in known else world[atom]
                if value != required:
                    satisfied = False
                    break
            results[rule["head"]] = results.get(rule["head"], False) or satisfied
        known.update(results)
    return known


def answer(case, world):
    if case["complete"] is not True:
        return "UNKNOWN"
    derived = derive(case, world)
    truth = False
    for term in case["query"]["or"]:
        term_true = True
        for atom, expected in term:
            value = derived[atom] if atom in derived else world[atom]
            if value != expected:
                term_true = False
                break
        truth = truth or term_true
    return "MATCH" if truth else "NO_MATCH"


def proof_facts(case):
    derived = derive(case, case["facts"])
    families = {}
    for rule in sorted(case["rules"], key=lambda r: (r["stratum"], r["name"])):
        if not all((derived[atom] if atom in derived else case["facts"][atom]) == expected
                   for atom, expected in rule["body"]):
            continue
        products = [frozenset()]
        for atom, expected in rule["body"]:
            if not expected:
                continue
            choices = families.get(atom, []) if atom in derived else [frozenset((atom,))]
            products = [left | right for left in products for right in choices]
        families.setdefault(rule["head"], []).extend(products)
        family = sorted(set(families[rule["head"]]), key=lambda s: (len(s), sorted(s)))
        families[rule["head"]] = [s for s in family if not any(t < s for t in family)]
    def minimize(family):
        ordered = sorted(set(family), key=lambda s: (len(s), sorted(s)))
        return [sorted(s) for s in ordered if not any(t < s for t in ordered)]
    query_products = []
    for term in case["query"]["or"]:
        products = [frozenset()]
        valid = True
        for atom, expected in term:
            value = derived[atom] if atom in derived else case["facts"][atom]
            if value != expected:
                valid = False
                break
            if expected:
                choices = families.get(atom, []) if atom in derived else [frozenset((atom,))]
                products = [left | right for left in products for right in choices]
        if valid:
            query_products.extend(products)
    return {"query": minimize(query_products),
            "eligible": minimize(families.get("eligible", []))}


def all_worlds(case):
    names = tuple(case["mutable"])
    for bits in itertools.product((False, True), repeat=len(names)):
        candidate = dict(case["facts"])
        candidate.update(zip(names, bits))
        yield candidate


def toggled(actual, other, domain):
    return sorted(name for name in domain if actual[name] != other[name])


def oracle_row(case, limit):
    if case.get("endpoint") != "final_match_v1":
        raise ValueError("unrecognized outcome endpoint")
    if case.get("mutable") != case.get("declared_mutable_universe"):
        raise ValueError("mutable intervention domain changed")
    if set(case["facts"]) != set(case.get("fact_universe", [])):
        raise ValueError("fact universe changed")
    if not set(case["mutable"]).issubset(case["fact_universe"]):
        raise ValueError("toggle outside declared fact universe")
    signed = [f"{name}={'true' if case['facts'][name] else 'false'}" for name in sorted(case["facts"])]
    worlds_n = 2 ** len(case["mutable"])
    supports = proof_facts(case)
    result = {"case_id": case["id"], "scope": case["scope"], "epoch": case["epoch"],
              "signed_facts": signed, "minimal_positive_match_supports": supports["query"],
              "positive_eligibility_supports": supports["eligible"],
              "enumerated_worlds": 0, "explanation_complete": False}
    if case["complete"] is not True:
        return {**result, "status": "UNKNOWN_INCOMPLETE", "outcome": "UNKNOWN",
                "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    actual_outcome = answer(case, case["facts"])
    if worlds_n > limit:
        return {**result, "status": "UNKNOWN_TOO_LARGE", "outcome": actual_outcome,
                "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    states = list(all_worlds(case))
    result.update({"status": "READY", "outcome": actual_outcome,
                   "enumerated_worlds": len(states), "explanation_complete": True})
    if actual_outcome != "NO_MATCH":
        return {**result, "robustness_radius": None, "minimum_flip_sets": [], "actual_causes": {}}
    changed_to_match = [(state, toggled(case["facts"], state, case["mutable"]))
                        for state in states if answer(case, state) == "MATCH"]
    if changed_to_match:
        distance = min(len(diff) for _, diff in changed_to_match)
        flip_sets = sorted(diff for _, diff in changed_to_match if len(diff) == distance)
    else:
        distance, flip_sets = None, []
    cause_rows = {}
    for variable in case["mutable"]:
        contingency_sets = []
        for state in states:
            if state[variable] != case["facts"][variable] or answer(case, state) != "NO_MATCH":
                continue
            counterfactual = dict(state)
            counterfactual[variable] = not counterfactual[variable]
            if answer(case, counterfactual) == "MATCH":
                contingency_sets.append(toggled(case["facts"], state,
                                                [x for x in case["mutable"] if x != variable]))
        if contingency_sets:
            k = min(map(len, contingency_sets))
            minimal = sorted({tuple(s) for s in contingency_sets if len(s) == k})
            cause_rows[variable] = {"literal": case["facts"][variable], "minimum_contingency": k,
                                    "contingencies": [list(s) for s in minimal],
                                    "responsibility": 1.0 / (k + 1)}
    result.update({"robustness_radius": distance, "minimum_flip_sets": flip_sets,
                   "actual_causes": cause_rows})
    return result


def main():
    src, raw_path, out_path = map(Path, sys.argv[1:4])
    packet = json.loads(src.read_text())
    raw = json.loads(raw_path.read_text())
    expected = [oracle_row(case, packet["max_worlds"]) for case in packet["cases"]]
    checks = []
    checks.append(("row_count", len(raw.get("rows", [])) == len(expected)))
    fields = ("case_id", "scope", "epoch", "signed_facts", "minimal_positive_match_supports",
              "positive_eligibility_supports",
              "enumerated_worlds", "explanation_complete", "status", "outcome",
              "robustness_radius", "minimum_flip_sets", "actual_causes")
    for index, want in enumerate(expected):
        got = raw["rows"][index] if index < len(raw.get("rows", [])) else {}
        for field in fields:
            checks.append((f"row[{index}].{field}", got.get(field) == want.get(field)))
    by_id = {row["case_id"]: row for row in expected}
    # Positive-only summaries are identical although the exception changes the result.
    left, right = (by_id["same_positive_support_no_exception"],
                   by_id["same_positive_support_with_exception"])
    checks.append(("same_positive_support_different_negation",
                   left["positive_eligibility_supports"] == right["positive_eligibility_supports"]
                   and left["minimal_positive_match_supports"] != right["minimal_positive_match_supports"]
                   and left["outcome"] == "MATCH" and right["outcome"] == "NO_MATCH"))
    contingency = by_id["contingency_only_exception"]
    checks.append(("contingency_only_cause_not_in_positive_support",
                   "exception" in contingency["actual_causes"]
                   and "exception" not in contingency["positive_eligibility_supports"]))
    designated = by_id["robustness_vs_contingency"]
    checks.append(("robustness_and_contingency_separate",
                   designated["robustness_radius"] == 1
                   and designated["actual_causes"].get("exception", {}).get("minimum_contingency") == 2))
    dense = by_id["dense_budget_control"]
    checks.append(("dense_case_explicit_unknown",
                   dense["status"] == "UNKNOWN_TOO_LARGE" and not dense["explanation_complete"]))
    mono = by_id["monotone_positive_control"]
    checks.append(("monotone_positive_control", mono["outcome"] == "MATCH"
                   and mono["minimal_positive_match_supports"] == [sorted(
                       name for name, value in json.loads(src.read_text())["cases"][0]["facts"].items()
                       if value)]))
    failures = [name for name, passed in checks if not passed]
    report = {"schema": "negative-query-responsibility-audit-v1",
              "status": "PASS_METHOD_SCOPED" if not failures else "FAIL_METHOD",
              "checks_passed": sum(ok for _, ok in checks), "checks_total": len(checks),
              "failures": failures, "independent_world_evaluations": sum(
                  row["enumerated_worlds"] for row in expected),
              "rows": len(expected), "scope": "finite stratified Boolean query fixtures only"}
    out_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(f"{report['status']} checks={report['checks_passed']}/{report['checks_total']} failures={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
