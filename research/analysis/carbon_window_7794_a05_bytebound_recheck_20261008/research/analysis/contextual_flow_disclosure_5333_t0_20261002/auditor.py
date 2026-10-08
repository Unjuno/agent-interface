import argparse
from collections import Counter
import json
import sys
from pathlib import Path


def independently_derive(case, mode, policy):
    if mode == "ACTOR_ONLY":
        return ("ALLOWED", case["requested_fields"]) if case["actor_authorized"] else ("BLOCKED_FLOW", [])
    if mode == "LABEL_ONLY":
        return ("ALLOWED", case["requested_fields"]) if case["source_label"] != policy["sensitive_label"] else ("BLOCKED_FLOW", [])
    if not case["actor_authorized"]:
        return "BLOCKED_FLOW", []
    if case["recipient"] in policy["protected_sinks"] and case["integrity"] != policy["minimum_integrity"]:
        return "BLOCKED_FLOW", []
    if case["source_label"] not in policy["known_source_labels"]:
        return "UNKNOWN_FLOW", []
    if case["source_label"] != policy["sensitive_label"]:
        return "ALLOWED", case["requested_fields"]
    if case["recipient"] is None or case["purpose"] is None:
        return "UNKNOWN_FLOW", []
    matching_rules = []
    for rule in policy["allowed_contexts"]:
        if rule["recipient"] != case["recipient"] or rule["purpose"] != case["purpose"]:
            continue
        if rule["fields"] != case["requested_fields"] or rule["minimum_integrity"] != case["integrity"]:
            continue
        if "explicit_release_revision" in rule and rule["explicit_release_revision"] != case["release_revision"]:
            continue
        matching_rules.append(rule)
    if not matching_rules:
        return "BLOCKED_FLOW", []
    if any("explicit_release_revision" in rule for rule in matching_rules):
        return "DECLASSIFIED", case["requested_fields"]
    return "ALLOWED", case["requested_fields"]


def audit(fixture, policy, oracle, actual):
    cases = {case["id"]: case for case in fixture["cases"]}
    expected = oracle["expected"]
    if len(actual) != len(cases) * 3:
        raise ValueError("row count mismatch")
    for left_id, right_id, changed in [
        ("F01_ALLOWED_SCHEDULER", "F02_WRONG_RECIPIENT", "recipient"),
        ("F01_ALLOWED_SCHEDULER", "F03_WRONG_PURPOSE", "purpose"),
    ]:
        left, right = cases[left_id], cases[right_id]
        if any(left[key] != right[key] for key in left if key not in ("id", changed)):
            raise ValueError("matched pair changes more than declared context axis")
        if left[changed] == right[changed]:
            raise ValueError("matched pair does not change declared context axis")
    keys = set()
    for row in actual:
        required_fields = {
            "case_id", "mode", "decision", "released_fields", "source_digest", "actor",
            "actor_authorized", "source_label", "integrity", "requested_fields",
            "release_revision", "recipient", "purpose"
        }
        if set(row) != required_fields:
            raise ValueError("candidate output schema mismatch")
        key = (row["case_id"], row["mode"])
        if key in keys or row["case_id"] not in cases:
            raise ValueError("duplicate or unknown row")
        keys.add(key)
        case = cases[row["case_id"]]
        derived_decision, derived_release = independently_derive(case, row["mode"], policy)
        if derived_decision != expected[case["id"]][row["mode"]]:
            raise ValueError("frozen oracle and independent policy replay disagree")
        if row["mode"] == "CONTEXT_BOUND" and derived_release != oracle["released_fields"].get(case["id"], []):
            raise ValueError("frozen oracle and independent released-field replay disagree")
        if row["decision"] != derived_decision:
            raise ValueError("decision mismatch")
        for field in ("source_digest", "actor", "actor_authorized", "source_label", "integrity",
                      "requested_fields", "release_revision", "recipient", "purpose"):
            if row[field] != case[field]:
                raise ValueError(field + " provenance mismatch")
        if sorted(row["released_fields"]) != sorted(derived_release):
            raise ValueError("released field scope mismatch")
        if row["decision"] in ("BLOCKED_FLOW", "UNKNOWN_FLOW") and row["released_fields"]:
            raise ValueError("blocked or unknown flow disclosed fields")
    if len(keys) != len(cases) * 3:
        raise ValueError("incomplete policy coverage")
    counts = Counter((row["mode"], row["decision"]) for row in actual)
    return {
        "status":"PASS_METHOD_SCOPED", "rows":len(actual), "cases":len(cases), "errors":0,
        "decision_counts": {mode: {decision: count for (m, decision), count in sorted(counts.items()) if m == mode}
                            for mode in ("ACTOR_ONLY", "LABEL_ONLY", "CONTEXT_BOUND")}
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="fixture.json")
    parser.add_argument("--policy", default="policy.json")
    parser.add_argument("--oracle", default="expected.json")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    oracle = json.loads(Path(args.oracle).read_text(encoding="utf-8"))
    actual = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    try:
        result = audit(fixture, policy, oracle, actual)
    except Exception as exc:
        result = {"status":"FAIL_METHOD","error":type(exc).__name__ + ": " + str(exc)}
    Path(args.out).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_METHOD_SCOPED":
        sys.exit(1)


if __name__ == "__main__":
    main()
