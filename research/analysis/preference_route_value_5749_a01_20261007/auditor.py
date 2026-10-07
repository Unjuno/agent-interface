import copy
import json
import sys
from pathlib import Path


def _best(profile, actions):
    top = max(profile[x] for x in actions)
    return {x for x in actions if profile[x] == top}


def _audit_route(case, policy):
    profiles = case["rankings"]
    if len(profiles) == 0:
        return "YIELD_UNKNOWN_PREFERENCE_MODEL", None, None
    choices = [_best(p, case["authorized_actions"]) for p in profiles]
    disagreement = len(set().union(*choices)) > 1
    if policy == "source_router" and disagreement and case["query_available"]:
        return "CLARIFY", None, None
    if case["world_unknown"]:
        return ("VERIFY", None, None) if case["verify_available"] else ("YIELD_UNKNOWN_WORLD", None, None)
    agreed = set.intersection(*choices)
    if agreed and case.get("consensus_authorized", False):
        action = min(agreed)
        loss = max(max(p[x] for x in case["authorized_actions"]) - p[action] for p in profiles)
        return "ACT_PROPOSAL", action, loss
    fallback = case.get("authorized_default")
    if fallback in case["authorized_actions"]:
        loss = max(max(p[x] for x in case["authorized_actions"]) - p[fallback] for p in profiles)
    else:
        loss = min(max(max(p[x] for x in case["authorized_actions"]) - p[a] for p in profiles)
                   for a in case["authorized_actions"])
    if policy == "regret_cost" and loss > case["query_cost"] and case["query_available"] and case["query_resolves"]:
        return "CLARIFY", None, loss
    if fallback not in case["authorized_actions"]:
        return "YIELD_NO_AUTHORIZED_ACTION", None, loss
    return "ACT_PROPOSAL", fallback, loss


def audit(raw, fixture):
    errors = []
    expected_keys = {(c["id"], p) for c in fixture["cases"] for p in fixture["policies"]}
    seen = set()
    case_map = {c["id"]: c for c in fixture["cases"]}
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in seen or key not in expected_keys:
            errors.append("duplicate_or_unknown_row")
            continue
        seen.add(key)
        case = case_map[key[0]]
        expected = _audit_route(case, key[1])
        observed = (row.get("route"), row.get("proposed_action"), row.get("worst_case_regret"))
        if observed != expected:
            errors.append("route_or_regret_mismatch:" + ":".join(key))
        if row.get("authority_granted") is not False:
            errors.append("authority_granted")
        if row.get("question_cost") != (case["query_cost"] if expected[0] == "CLARIFY" else 0):
            errors.append("question_cost_mismatch")
        if row.get("verification_cost") != (case["verify_cost"] if expected[0] == "VERIFY" else 0):
            errors.append("verification_cost_mismatch")
    if seen != expected_keys:
        errors.append("incomplete_or_extra_matrix")
    return {"rows": len(seen), "errors": errors,
            "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT"}


def mutations(raw, fixture):
    probes = [
        ("invent_action", lambda d: d["rows"][0].update(proposed_action="Z")),
        ("erase_query_cost", lambda d: next(r for r in d["rows"] if r["policy"] == "source_router" and r["route"] == "CLARIFY").update(question_cost=0)),
        ("score_world_uncertainty_as_clarification", lambda d: next(r for r in d["rows"] if r["case_id"] == "world_only_uncertainty" and r["policy"] == "regret_cost").update(route="CLARIFY", question_cost=2, verification_cost=0)),
        ("act_without_authorized_default", lambda d: next(r for r in d["rows"] if r["case_id"] == "high_regret_no_authorized_default" and r["policy"] == "regret_cost").update(route="ACT_PROPOSAL", proposed_action="A")),
        ("grant_authority", lambda d: d["rows"][0].update(authority_granted=True)),
        ("drop_row", lambda d: d["rows"].pop()),
    ]
    results = []
    for name, change in probes:
        altered = copy.deepcopy(raw)
        change(altered)
        results.append({"name": name, "rejected": bool(audit(altered, fixture)["errors"])})
    return results


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text())
    fixture = json.loads(Path(sys.argv[2]).read_text())
    result = audit(raw, fixture)
    result["mutations"] = mutations(raw, fixture)
    if not all(x["rejected"] for x in result["mutations"]):
        result["errors"].append("mutation_escaped")
    result["disposition"] = "PASS_METHOD_SCOPED" if not result["errors"] else "FAIL_AUDIT"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not result["errors"] else 1)
