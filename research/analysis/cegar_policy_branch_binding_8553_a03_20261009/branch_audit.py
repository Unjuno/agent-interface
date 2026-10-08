#!/usr/bin/env python3
"""Independent finite replay of retained CEGAR policy branches; imports no A01 code."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def evaluate_policy(case, node, features, belief=None, remaining=None):
    states = case["states"]
    belief = tuple(sorted(case["start"] if belief is None else belief))
    remaining = case["horizon"] if remaining is None else remaining
    if not isinstance(node, dict):
        return False, "policy node is not an object"
    action = node.get("action")
    branches = node.get("branches")
    if not isinstance(branches, list):
        return False, "branches is not an array"
    if action == "GOAL":
        return (all(states[s]["goal"] for s in belief) and not branches,
                "goal leaf does not cover an all-goal belief" if not all(states[s]["goal"] for s in belief) else "")
    if remaining <= 0:
        return False, "policy exceeds horizon"
    if not isinstance(action, str):
        return False, "action is not a string"

    successors = {}
    for state in belief:
        edge = states[state].get("actions", {}).get(action)
        if not isinstance(edge, dict) or not edge.get("enabled") or not edge.get("safe"):
            return False, f"{action} is not enabled and safe in every belief state"
        signature = ()
        if action == "inspect" and features:
            observed = edge.get("observations", {})
            if not isinstance(observed, dict) or any(feature not in observed for feature in features):
                return False, f"{action} does not expose every selected feature"
            signature = tuple(observed[feature] for feature in features)
        successors.setdefault(signature, set()).add(edge["next"])

    observed_branches = {}
    for branch in branches:
        if not isinstance(branch, dict) or not isinstance(branch.get("observation"), list):
            return False, "branch observation is not an array"
        signature = tuple(branch["observation"])
        if signature in observed_branches:
            return False, "duplicate policy observation branch"
        observed_branches[signature] = branch.get("policy")
    if set(observed_branches) != set(successors):
        return False, "policy branches do not exactly cover emitted observations"

    for signature, next_belief in successors.items():
        ok, reason = evaluate_policy(case, observed_branches[signature], features,
                                     next_belief, remaining - 1)
        if not ok:
            return False, f"branch {signature!r}: {reason}"
    return True, ""


def validate(fixture, raw):
    errors = []
    if raw.get("schema") != "recovery-abstraction-candidate-v1":
        errors.append("candidate schema mismatch")
    if raw.get("fixture_sha256") != hashlib.sha256(canonical(fixture)).hexdigest():
        errors.append("fixture hash mismatch")
    rows = {row.get("case_id"): row for row in raw.get("cases", []) if isinstance(row, dict)}
    expected_ids = {case["id"] for case in fixture["cases"]}
    if set(rows) != expected_ids:
        errors.append("case set mismatch")
    checked = 0
    safe_ids = {p["id"] for p in fixture["predicate_catalog"] if p["safe_for_policy"]}
    for case in fixture["cases"]:
        row = rows.get(case["id"])
        if row is None:
            continue
        cegar = row.get("cegar", {})
        policy = cegar.get("policy")
        features = cegar.get("predicates_used", [])
        if not isinstance(features, list) or not set(features) <= safe_ids:
            errors.append(f"{case['id']}: selected policy features are unsafe or undeclared")
            continue
        if policy is not None:
            checked += 1
            ok, reason = evaluate_policy(case, policy, features)
            if cegar.get("verdict") != "RECOVERABLE" or not ok:
                errors.append(f"{case['id']}: policy replay failed: {reason or 'policy/verdict mismatch'}")
        elif cegar.get("verdict") == "RECOVERABLE":
            errors.append(f"{case['id']}: recoverable verdict has no policy")
    return {"passed": not errors, "cases_reconstructed": len(rows),
            "policies_replayed": checked, "errors": errors}


def diagnostic_mutations(raw):
    baseline = copy.deepcopy(raw)
    target = next(row for row in baseline["cases"] if row["case_id"] == "spurious_loss_safe_separator")
    branches = target["cegar"]["policy"]["branches"]

    unsupported = copy.deepcopy(raw)
    ub = next(row for row in unsupported["cases"] if row["case_id"] == "spurious_loss_safe_separator")["cegar"]["policy"]["branches"]
    ub[0]["observation"] = ["secret-a"]
    ub[1]["observation"] = ["secret-b"]

    swapped = copy.deepcopy(raw)
    sb = next(row for row in swapped["cases"] if row["case_id"] == "spurious_loss_safe_separator")["cegar"]["policy"]["branches"]
    sb[0]["policy"], sb[1]["policy"] = sb[1]["policy"], sb[0]["policy"]
    return {"unchanged": baseline, "unsupported_observation_values": unsupported,
            "swapped_observation_routes": swapped}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing to overwrite output")
    fixture = json.loads(Path(args.fixture).read_text())
    raw = json.loads(Path(args.candidate).read_text())
    results = {name: validate(fixture, mutant) for name, mutant in diagnostic_mutations(raw).items()}
    passed = (results["unchanged"]["passed"] and
              not results["unsupported_observation_values"]["passed"] and
              not results["swapped_observation_routes"]["passed"] and
              all(results["unchanged"][key] == expected for key, expected in
                  [("cases_reconstructed", 5), ("policies_replayed", 2)]))
    result = {"schema": "issue8553-a03-branch-binding-audit-v1",
              "freeze_sha256": args.freeze_sha256, "passed": passed,
              "disposition": "CONFIRMED_AUDIT_GAP" if passed else "HOLD",
              "results": results,
              "mutation_controls": {"rejected": sum(not results[name]["passed"] for name in
                  ("unsupported_observation_values", "swapped_observation_routes")), "total": 2}}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("branch-audit-pass" if passed else "branch-audit-hold")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
