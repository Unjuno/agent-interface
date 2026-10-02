"""Finite route-feasibility enumerator for Issue #6417; no model or effects."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).parent


def variant_result(case, variant):
    intent = variant.get("intent", case["intent"])
    lease = variant.get("lease_seconds", case["lease_seconds"])
    feasible = []
    for route in case["routes"]:
        total = route["action_seconds"] + route["verification_seconds"]
        if route["safe"] and route["effect"] == case["effect"] and total <= variant["deadline_seconds"] and total <= lease:
            feasible.append((route["id"], total))
    route_by_id = {route["id"]: route for route in case["routes"]}
    feasible.sort(key=lambda item: (route_by_id[item[0]].get("quality_cost", 0), item[1], item[0]))
    return {"variant": variant["id"], "intent": intent, "lease_seconds": lease,
            "feasible": [route_id for route_id, _ in feasible],
            "choice": feasible[0][0] if feasible else "YIELD"}


def pair_result(case):
    long_variant, short_variant = case["variants"]
    long = variant_result(case, long_variant)
    short = variant_result(case, short_variant)
    reasons = []
    if long["intent"] != short["intent"]:
        reasons.append("INTENT_DIFFERS")
    if long["lease_seconds"] != short["lease_seconds"]:
        reasons.append("LEASE_BUDGET_DIFFERS")
    if long["feasible"] != short["feasible"]:
        reasons.append("FEASIBLE_SET_DIFFERS")
    if long["choice"] != short["choice"]:
        reasons.append("ORACLE_CHOICE_DIFFERS")
    return {"case_id": case["id"], "kind": case["kind"], "long": long, "short": short,
            "equivalent": not reasons, "reasons": reasons}


def mutate(case, mutation):
    result = copy.deepcopy(case)
    short = result["variants"][1]
    if mutation == "set_short_deadline_seconds_to_6":
        short["deadline_seconds"] = 6
    elif mutation == "set_short_lease_seconds_to_9":
        short["lease_seconds"] = 9
    elif mutation == "set_short_intent_to_delete_download":
        short["intent"] = "delete_required_download"
    else:
        raise ValueError(mutation)
    result["kind"] = "slack_equivalent"
    return pair_result(result)


def run():
    data = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    return {"allocation": data["allocation"], "pairs": [pair_result(case) for case in data["cases"]],
            "invalid_claimed_equivalent": [
                {"id": mutation["id"], "expected_reject": mutation["expected_reject"],
                 "result": mutate(next(case for case in data["cases"] if case["id"] == mutation["base_case"]), mutation["mutation"])}
                for mutation in data["invalid_claimed_equivalent"]]}


if __name__ == "__main__":
    output = run()
    (ROOT / "candidate.raw.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
