#!/usr/bin/env python3
"""Independent reconstruction and policy audit; intentionally imports no candidate code."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def oracle(case, features):
    states = case["states"]
    seen = set()

    def visit(belief, remaining):
        belief = tuple(sorted(belief))
        key = (belief, remaining)
        if key in seen:
            return False
        seen.add(key)
        if all(states[s]["goal"] for s in belief):
            return True
        if remaining <= 0:
            return False
        common = None
        for state in belief:
            allowed = {name for name, edge in states[state]["actions"].items()
                       if edge["enabled"] and edge["safe"]}
            common = allowed if common is None else common & allowed
        for name in sorted(common or ()):
            groups = {}
            for state in belief:
                edge = states[state]["actions"][name]
                nxt = edge["next"]
                sig = ()
                if features and name == "inspect":
                    available = states[state]["actions"]
                    visible = next((a.get("observations", {}) for a in available.values()
                                    if all(f in a.get("observations", {}) for f in features)), {})
                    sig = tuple(visible[f] for f in features)
                groups.setdefault(sig, set()).add(nxt)
            if all(visit(group, remaining - 1) for group in groups.values()):
                return True
        return False

    return "RECOVERABLE" if visit(case["start"], case["horizon"]) else "NOT_RECOVERABLE"


def policy_safe(node, case, features):
    if node is None or node.get("action") == "GOAL":
        return True
    action = node.get("action")
    if not isinstance(action, str) or action not in {name for s in case["states"].values() for name in s["actions"]}:
        return False
    allowed = {p["id"] for p in features}
    for branch in node.get("branches", []):
        if any(feature not in allowed for feature in branch.get("observation_features", [])):
            return False
        if not policy_safe(branch.get("policy"), case, features):
            return False
    serialized = json.dumps(node, sort_keys=True)
    mentioned = set(case["states"]) & set(serialized.replace('"', ' ').replace(':', ' ').replace(',', ' ').split())
    return not mentioned


def validate(fixture, candidate):
    errors = []
    safe_catalog = [p for p in fixture["predicate_catalog"] if p["safe_for_policy"]]
    safe_ids = {p["id"] for p in safe_catalog}
    expected_hash = digest(fixture)
    if candidate.get("schema") != "recovery-abstraction-candidate-v1":
        errors.append("candidate schema mismatch")
    if candidate.get("fixture_sha256") != expected_hash:
        errors.append("fixture hash mismatch")
    rows = {row.get("case_id"): row for row in candidate.get("cases", [])}
    if set(rows) != {case["id"] for case in fixture["cases"]}:
        errors.append("case set mismatch")
    for case in fixture["cases"]:
        row = rows.get(case["id"])
        if row is None:
            continue
        truth = oracle(case, safe_ids)
        if row.get("concrete_validation_verdict") != truth:
            errors.append(f"{case['id']}: concrete oracle mismatch")
        used = row.get("cegar", {}).get("predicates_used", [])
        if not set(used) <= safe_ids:
            errors.append(f"{case['id']}: unsafe or undeclared predicate")
        if case["id"] == "spurious_loss_safe_separator" and (
                used != ["p_color"] or
                row.get("cegar", {}).get("refinements") != [{"added": "p_color", "verdict": "RECOVERABLE"}]):
            errors.append("safe-separator refinement lineage mismatch")
        policy = row.get("cegar", {}).get("policy")
        if not policy_safe(policy, case, safe_catalog):
            errors.append(f"{case['id']}: hidden-state or malformed policy")
        verdict = row.get("cegar", {}).get("verdict")
        if verdict == "RECOVERABLE" and (truth != "RECOVERABLE" or policy is None):
            errors.append(f"{case['id']}: false recoverable claim")
        if verdict not in {"RECOVERABLE", "NOT_RECOVERABLE", "UNKNOWN"}:
            errors.append(f"{case['id']}: invalid verdict")
    return {"schema": "recovery-abstraction-audit-v1", "passed": not errors,
            "fixture_sha256": expected_hash, "errors": errors,
            "cases_reconstructed": len(rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if out.exists():
        raise SystemExit("refusing to overwrite output")
    result = validate(json.loads(Path(args.fixture).read_text(encoding="utf-8")),
                      json.loads(Path(args.candidate).read_text(encoding="utf-8")))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("audit-passed" if result["passed"] else "audit-failed")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
