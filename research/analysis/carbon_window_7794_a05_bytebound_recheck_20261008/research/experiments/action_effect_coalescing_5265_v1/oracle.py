"""Independent finite-case oracle; does not import the candidate experiment."""
import json


POLICIES = ("NO_CROSS_PRODUCER_COALESCING", "SEMANTIC_EFFECT_COALESCING")
SEMANTIC_FIELDS = (
    "intent_revision", "state_generation", "target_id", "target_incarnation",
    "operation", "effect_class", "effect_opportunity",
    "expected_postcondition", "parameters",
    "deadline_ms",
)


def materialize(workload, case):
    rows = []
    for spec in case["proposals"]:
        row = dict(workload["defaults"])
        row.update(spec["overrides"])
        row["proposal_id"] = spec["proposal_id"]
        row["producer_id"] = spec["producer_id"]
        rows.append(row)
    return rows


def _semantic_signature(row):
    values = tuple(row.get(name) for name in SEMANTIC_FIELDS)
    if any(value is None or value == "" for value in values):
        return None
    return json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def expected_outcome(rows, policy):
    applied = {}
    groups = []
    decisions = []
    for row in rows:
        if row.get("retry_of") is not None:
            decisions.append("DEFER_TO_ISSUE_24")
            continue
        if type(row.get("now_ms")) is not int or type(row.get("deadline_ms")) is not int:
            decisions.append("YIELD")
            continue
        if row["now_ms"] >= row["deadline_ms"]:
            decisions.append("YIELD_EXPIRED")
            continue
        if row.get("already_satisfied") is True:
            decisions.append("NO_ACTION")
            continue
        signature = _semantic_signature(row)
        if signature is None:
            decisions.append("YIELD")
            continue
        if policy == "SEMANTIC_EFFECT_COALESCING" and signature in applied:
            groups[applied[signature]]["members"].append({
                "proposal_id": row["proposal_id"], "producer_id": row["producer_id"]})
            decisions.append("COALESCED")
            continue
        group_index = len(groups)
        if policy == "SEMANTIC_EFFECT_COALESCING":
            applied[signature] = group_index
        groups.append({"members": [{"proposal_id": row["proposal_id"],
                                     "producer_id": row["producer_id"]}],
                       "deadline_ms": row["deadline_ms"]})
        decisions.append("EXECUTE")
    return {"decisions": decisions, "effects": decisions.count("EXECUTE"),
            "coalesced_groups": groups}


def oracle_for_case(workload, case):
    rows = materialize(workload, case)
    return {policy: expected_outcome(rows, policy) for policy in POLICIES}
