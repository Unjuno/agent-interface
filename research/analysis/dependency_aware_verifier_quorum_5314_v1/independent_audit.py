import json
from pathlib import Path

BASE = Path(__file__).parent
raw = json.loads((BASE / "raw.json").read_text(encoding="utf-8"))
errors = []


def oracle(votes, labels, known, threshold=3):
    if not all(known):
        return "UNCERTAIN"
    yes = {labels[i] for i, vote in enumerate(votes) if vote == "PASS"}
    no = {labels[i] for i, vote in enumerate(votes) if vote == "FAIL"}
    if len(yes) >= threshold:
        return "PASS"
    if len(no) >= threshold:
        return "FAIL"
    return "UNCERTAIN"


totals = {}
for policy in ("COUNT_QUORUM", "DECLARED_INDEPENDENT", "DEPENDENCY_AWARE", "FAIL_CLOSED_UNKNOWN_DEPENDENCY"):
    totals[policy] = {"false_pass": 0, "false_fail": 0, "uncertain": 0, "correct": 0}

for row in raw["rows"]:
    votes = row["votes"]
    truth = row["truth"]
    count_pass = votes.count("PASS") >= 3
    count_out = "PASS" if count_pass else "FAIL"
    declared_out = oracle(votes, row["declared_labels"], [True] * len(votes))
    dep_out = oracle(votes, row["dependency_labels"], row["metadata_known"])
    closed_out = "UNCERTAIN" if not all(row["metadata_known"]) else dep_out
    expected = {
        "COUNT_QUORUM": count_out,
        "DECLARED_INDEPENDENT": declared_out,
        "DEPENDENCY_AWARE": dep_out,
        "FAIL_CLOSED_UNKNOWN_DEPENDENCY": closed_out,
    }
    for policy, value in expected.items():
        if row["outputs"].get(policy) != value:
            errors.append({"case": row["case_id"], "truth": truth, "policy": policy, "expected": value, "observed": row["outputs"].get(policy)})
        bucket = totals[policy]
        if value == "UNCERTAIN":
            bucket["uncertain"] += 1
        elif value == "PASS" and not truth:
            bucket["false_pass"] += 1
        elif value == "FAIL" and truth:
            bucket["false_fail"] += 1
        else:
            bucket["correct"] += 1

# Effective mutation probes use hand-constructed receipts, independent of the enumerator.
probe1_votes = ["PASS", "PASS", "PASS", "FAIL", "FAIL"]
probe1_actual = ["shared", "shared", "shared", "f1", "f2"]
probe1_forged = ["a", "b", "c", "d", "e"]
mutation_probes = {
    "duplicate_same_domain_does_not_create_independent_quorum": {
        "count": "PASS" if probe1_votes.count("PASS") >= 3 else "FAIL",
        "aware": oracle(probe1_votes, probe1_actual, [True] * 5),
    },
    "forged_distinct_labels_are_not_verified_dependencies": {
        "declared": oracle(probe1_votes, probe1_forged, [True] * 5),
        "aware": oracle(probe1_votes, probe1_actual, [True] * 5),
    },
    "missing_dependency_blocks_authority": {
        "count": "PASS" if ["PASS", "PASS", "PASS", "FAIL", "FAIL"].count("PASS") >= 3 else "FAIL",
        "closed": oracle(["PASS", "PASS", "PASS", "FAIL", "FAIL"], ["x", "y", "z", "u", "v"], [False, True, True, True, True]),
    },
    "accurate_metadata_equates_declared_and_verified_domain_policy": {
        "declared": oracle(["PASS", "PASS", "FAIL", "FAIL", "FAIL"], ["x", "x", "y", "z", "w"], [True] * 5),
        "aware": oracle(["PASS", "PASS", "FAIL", "FAIL", "FAIL"], ["x", "x", "y", "z", "w"], [True] * 5),
    },
}

checks = [
    mutation_probes["duplicate_same_domain_does_not_create_independent_quorum"]["count"] == "PASS" and mutation_probes["duplicate_same_domain_does_not_create_independent_quorum"]["aware"] == "UNCERTAIN",
    mutation_probes["forged_distinct_labels_are_not_verified_dependencies"]["declared"] == "PASS" and mutation_probes["forged_distinct_labels_are_not_verified_dependencies"]["aware"] == "UNCERTAIN",
    mutation_probes["missing_dependency_blocks_authority"]["count"] == "PASS" and mutation_probes["missing_dependency_blocks_authority"]["closed"] == "UNCERTAIN",
    mutation_probes["accurate_metadata_equates_declared_and_verified_domain_policy"]["declared"] == mutation_probes["accurate_metadata_equates_declared_and_verified_domain_policy"]["aware"],
]

audit = {
    "study": raw["study"],
    "raw_sha256": __import__("hashlib").sha256((BASE / "raw.json").read_bytes()).hexdigest(),
    "rows_checked": len(raw["rows"]),
    "totals": totals,
    "mutation_probes": mutation_probes,
    "mutation_controls_passed": sum(checks),
    "mutation_controls_total": len(checks),
    "discrepancies": errors,
    "disposition": "PASS_FINITE_CONTRACT_ONLY" if not errors and all(checks) else "HOLD_AUDIT",
    "limits": ["enumeration counts are not probabilities", "domains are stipulated complete and correct", "no empirical independence or deployment efficacy demonstrated"],
}
(BASE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"rows_checked": audit["rows_checked"], "discrepancies": len(errors), "controls": [sum(checks), len(checks)], "disposition": audit["disposition"]}))
