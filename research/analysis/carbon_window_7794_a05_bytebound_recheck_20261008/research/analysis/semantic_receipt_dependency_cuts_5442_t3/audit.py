"""Raw-only independent receipt dependency audit; does not import candidate."""

import json
import sys


EXPECTED = {
    "no_fault": (True, True, "SEMANTICALLY_CONFIRMED", True),
    "parser_a_fault": (False, True, "SEMANTICALLY_CONFIRMED", True),
    "parser_b_fault": (False, True, "SEMANTICALLY_CONFIRMED", True),
    "shared_cache_common_lie": (True, False, "SEMANTICALLY_CONTRADICTED", False),
    "actuator_readback_fault": (True, False, "UNKNOWN", False),
}
EXPECTED_INPUTS = {
    "no_fault": ([], "doc:v9", {"observer_a": "doc:v9", "observer_b": "doc:v9", "observer_c": "doc:v9"}),
    "parser_a_fault": (["parser_a"], "doc:v9", {"observer_a": "doc:v8", "observer_b": "doc:v9", "observer_c": "doc:v9"}),
    "parser_b_fault": (["parser_b"], "doc:v9", {"observer_a": "doc:v9", "observer_b": "doc:v8", "observer_c": "doc:v9"}),
    "shared_cache_common_lie": (["shared_cache"], "doc:v8", {"observer_a": "doc:v9", "observer_b": "doc:v9", "observer_c": "doc:v8"}),
    "actuator_readback_fault": (["actuator_readback"], "doc:v9", {"observer_a": "doc:v9", "observer_b": "doc:v9", "observer_c": "doc:v8"}),
}
EXPECTED_PROVENANCE = {
    "observer_a": ["parser_a"],
    "parser_a": ["shared_cache"],
    "observer_b": ["parser_b"],
    "parser_b": ["shared_cache"],
    "observer_c": ["actuator_readback"],
    "shared_cache": ["semantic_state"],
    "actuator_readback": ["semantic_state"],
    "semantic_state": [],
}
EXPECTED_FAULTABLE = ["parser_a", "parser_b", "shared_cache", "actuator_readback"]


def closure(graph, start):
    result, pending = set(), list(graph[start])
    while pending:
        current = pending.pop()
        if current in result:
            continue
        if current not in graph:
            raise ValueError("provenance edge targets an undeclared node")
        result.add(current)
        pending.extend(graph[current])
    return result


def recompute(row):
    graph = row["provenance"]
    faultable = set(row["faultable_nodes"])
    observers = sorted(name for name in graph if name.startswith("observer_"))
    closures = {name: closure(graph, name) & faultable for name in observers}
    reports, failed, goal = row["observer_reports"], set(row["failed_dependencies"]), row["goal"]
    healthy = [name for name in observers if not (closures[name] & failed)]
    excluded = sorted(set(observers) - set(healthy))
    pairs = [
        [a, b]
        for i, a in enumerate(healthy)
        for b in healthy[i + 1:]
        if closures[a].isdisjoint(closures[b]) and reports[a] == goal and reports[b] == goal
    ]
    ab = reports["observer_a"] == reports["observer_b"] == goal
    pair_commit = bool(pairs)
    c = row["trusted_endpoint"]
    if c in healthy:
        c_status = "SEMANTICALLY_CONFIRMED" if reports[c] == goal else "SEMANTICALLY_CONTRADICTED"
    else:
        c_status = "SEMANTICALLY_CONFIRMED" if pair_commit else "UNKNOWN"
    return {
        "dependency_closures": {name: sorted(value) for name, value in closures.items()},
        "ab_agreement_commit": ab,
        "provenance_pair_commit": pair_commit,
        "independent_pairs": pairs,
        "excluded_observers": excluded,
        "trusted_c_status": c_status,
        "trusted_c_commit": c_status == "SEMANTICALLY_CONFIRMED",
    }


def audit(rows):
    errors, seen = [], set()
    for index, row in enumerate(rows):
        case = row.get("case_id")
        if case in seen:
            errors.append(f"row {index}: duplicate case")
            continue
        seen.add(case)
        try:
            expected_failed, expected_actual, expected_reports = EXPECTED_INPUTS[case]
            if row.get("failed_dependencies") != expected_failed or row.get("actual") != expected_actual or row.get("observer_reports") != expected_reports:
                errors.append(f"row {index}: frozen scenario input mismatch")
            if row.get("goal") != "doc:v9" or row.get("provenance") != EXPECTED_PROVENANCE or row.get("faultable_nodes") != EXPECTED_FAULTABLE:
                errors.append(f"row {index}: frozen provenance/goal mismatch")
            result = recompute(row)
            for key, value in result.items():
                if row.get(key) != value:
                    errors.append(f"row {index}: {key} mismatch")
            got = (result["ab_agreement_commit"], result["provenance_pair_commit"], result["trusted_c_status"], result["trusted_c_commit"])
            if got != EXPECTED.get(case):
                errors.append(f"row {index}: unexpected disposition {got}")
            if row["actual"] != row["goal"] and (result["provenance_pair_commit"] or result["trusted_c_commit"]):
                errors.append(f"row {index}: false goal confirmation")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row {index}: invalid evidence: {exc}")
    if seen != set(EXPECTED):
        errors.append("scenario inventory mismatch")
    return {"rows": len(rows), "errors": errors, "audit": "PASS" if not errors else "FAIL"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    print(json.dumps(audit(rows), sort_keys=True, separators=(",", ":")))
