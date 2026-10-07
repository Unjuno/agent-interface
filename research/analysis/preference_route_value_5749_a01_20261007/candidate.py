import json
import sys
from pathlib import Path


def best_actions(ranking, allowed):
    best = max(ranking[a] for a in allowed)
    return {a for a in allowed if ranking[a] == best}


def disagreement(rankings, allowed):
    return len(set.union(*(best_actions(r, allowed) for r in rankings))) > 1


def worst_regret(rankings, allowed, action):
    return max(max(r[a] for a in allowed) - r[action] for r in rankings)


def source_route(case):
    rankings = case["rankings"]
    if not rankings:
        return "YIELD_UNKNOWN_PREFERENCE_MODEL", None, None
    allowed = case["authorized_actions"]
    if disagreement(rankings, allowed) and case["query_available"]:
        return "CLARIFY", None, None
    if case["world_unknown"]:
        if case["verify_available"]:
            return "VERIFY", None, None
        return "YIELD_UNKNOWN_WORLD", None, None
    common = set.intersection(*(best_actions(r, allowed) for r in rankings))
    if common:
        action = sorted(common)[0]
        if case.get("consensus_authorized", False):
            return "ACT_PROPOSAL", action, worst_regret(rankings, allowed, action)
    default = case.get("authorized_default")
    if default in allowed:
        return "ACT_PROPOSAL", default, worst_regret(rankings, allowed, default)
    return "YIELD_NO_AUTHORIZED_ACTION", None, None


def regret_route(case):
    rankings = case["rankings"]
    if not rankings:
        return "YIELD_UNKNOWN_PREFERENCE_MODEL", None, None
    allowed = case["authorized_actions"]
    if case["world_unknown"]:
        if case["verify_available"]:
            return "VERIFY", None, None
        return "YIELD_UNKNOWN_WORLD", None, None
    common = set.intersection(*(best_actions(r, allowed) for r in rankings))
    if common:
        action = sorted(common)[0]
        if case.get("consensus_authorized", False):
            return "ACT_PROPOSAL", action, worst_regret(rankings, allowed, action)
    default = case.get("authorized_default")
    if default in allowed:
        regret = worst_regret(rankings, allowed, default)
    else:
        regret = min(worst_regret(rankings, allowed, action) for action in allowed)
    if regret > case["query_cost"] and case["query_available"] and case["query_resolves"]:
        return "CLARIFY", None, regret
    if default not in allowed:
        return "YIELD_NO_AUTHORIZED_ACTION", None, regret
    return "ACT_PROPOSAL", default, regret


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            route, action, regret = (source_route(case) if policy == "source_router"
                                     else regret_route(case))
            rows.append({"case_id": case["id"], "policy": policy, "route": route,
                         "proposed_action": action, "worst_case_regret": regret,
                         "question_cost": case["query_cost"] if route == "CLARIFY" else 0,
                         "verification_cost": case["verify_cost"] if route == "VERIFY" else 0,
                         "authority_granted": False})
    return {"schema": "5749-route-regret-raw-a01-v1",
            "allocation": fixture["allocation"], "rows": rows}


if __name__ == "__main__":
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("fixture.json")
    print(json.dumps(run(json.loads(source.read_text())), sort_keys=True,
                     separators=(",", ":")))
