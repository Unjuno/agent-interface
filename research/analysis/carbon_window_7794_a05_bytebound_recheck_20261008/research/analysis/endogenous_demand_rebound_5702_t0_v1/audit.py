"""Independent raw-only audit; deliberately does not import candidate.py."""
from copy import deepcopy
import json
import sys


TABLE = {
    "no_rebound": {
        "policy": "frozen_start", "budget": 12, "verifier_capacity": 8,
        "opportunities": [
            ("A", 0, 10, 10, True, True, 2, 1, 1),
            ("U", 1, 0, "UNKNOWN", True, True, 2, 1, 1),
            ("B", 2, 100, 100, False, True, 1, 1, 1),
            ("D", 3, 1000, 1000, False, False, 1, 1, 1),
        ],
    },
    "beneficial_expansion": {
        "policy": "positive_ex_ante_net_value", "budget": 5, "verifier_capacity": 4,
        "opportunities": [
            ("A", 0, 10, 10, True, True, 2, 1, 1),
            ("B", 1, 7, 7, False, True, 4, 2, 1),
            ("D", 2, 1000, 1000, False, False, 1, 1, 1),
        ],
    },
    "adverse_mix": {
        "policy": "positive_ex_ante_net_value", "budget": 7, "verifier_capacity": 3,
        "opportunities": [
            ("A", 0, 10, 10, True, True, 2, 1, 1),
            ("B", 1, 4, 1, False, True, 4, 1, 2),
            ("C", 2, 8, 8, False, True, 3, 2, 1),
            ("D", 3, 1000, 1000, False, False, 1, 1, 1),
        ],
    },
}


def _expected():
    rows = []
    for case_id, spec in TABLE.items():
        for route in ("slow", "fast"):
            budget = spec["budget"]
            capacity = spec["verifier_capacity"]
            for oid, arrival, value, endpoint, mandatory, safe, slow_cost, fast_cost, verify in spec["opportunities"]:
                cost = slow_cost if route == "slow" else fast_cost
                surplus = value - cost - verify
                if not safe:
                    decision = "BLOCKED_UNSAFE"
                elif mandatory:
                    decision = "MANDATORY"
                elif spec["policy"] == "frozen_start":
                    decision = "SKIP_FIXED_WORKLOAD"
                elif surplus <= 0:
                    decision = "SKIP_NONPOSITIVE_EX_ANTE_NET"
                elif cost + verify > budget or verify > capacity:
                    decision = "SKIP_BUDGET_OR_VERIFIER_CAPACITY"
                else:
                    decision = "START_OPTIONAL"
                started = decision in ("MANDATORY", "START_OPTIONAL")
                spent = cost + verify if started else 0
                if started:
                    budget -= spent
                    capacity -= verify
                rows.append({
                    "case_id": case_id, "route": route, "policy": spec["policy"],
                    "budget": spec["budget"], "verifier_capacity": spec["verifier_capacity"],
                    "opportunity_id": oid, "arrival": arrival, "offered": True,
                    "ex_ante_value": value, "endpoint": endpoint if started else "NOT_STARTED",
                    "mandatory": mandatory, "safe": safe, "decision": decision,
                    "started": started, "completed": started and endpoint != "UNKNOWN",
                    "action_cost_if_started": cost, "verifier_demand_if_started": verify,
                    "realized_resource_spend": spent,
                    "forbidden_effect": started and not safe,
                })
    summaries = []
    for case_id in TABLE:
        for route in ("slow", "fast"):
            arm = [r for r in rows if r["case_id"] == case_id and r["route"] == route]
            active = [r for r in arm if r["started"]]
            value = sum(r["endpoint"] for r in active if isinstance(r["endpoint"], int))
            spend = sum(r["realized_resource_spend"] for r in arm)
            summaries.append({
                "case_id": case_id, "route": route, "offered": len(arm),
                "started": len(active), "completed": sum(r["completed"] for r in arm),
                "unknown_started": sum(r["started"] and r["endpoint"] == "UNKNOWN" for r in arm),
                "verified_useful_value": value, "resource_spend": spend,
                "verified_net_useful_value": value - spend,
                "forbidden_effects": sum(r["forbidden_effect"] for r in arm),
                "skipped_offered": sum(not r["started"] for r in arm),
                "verifier_demand": sum(r["verifier_demand_if_started"] for r in active),
            })
    return {"schema": "endogenous-demand-rebound-5702-t0-v1",
            "opportunity_set_id": "frozen-5702-t0-opportunities-v1",
            "cases": list(TABLE), "rows": rows, "summaries": summaries}


def _core(raw):
    if raw != _expected():
        return ["raw opportunity rows or independent session summaries differ from the frozen table"]
    summaries = {(s["case_id"], s["route"]): s for s in raw["summaries"]}
    no_slow, no_fast = summaries[("no_rebound", "slow")], summaries[("no_rebound", "fast")]
    ben_slow, ben_fast = summaries[("beneficial_expansion", "slow")], summaries[("beneficial_expansion", "fast")]
    adv_slow, adv_fast = summaries[("adverse_mix", "slow")], summaries[("adverse_mix", "fast")]
    errors = []
    if (no_slow["started"], no_slow["completed"], no_slow["unknown_started"]) != (2, 1, 1):
        errors.append("frozen-start arm changed fixed task/UNKNOWN accounting")
    if (no_fast["started"], no_fast["completed"], no_fast["unknown_started"]) != (2, 1, 1):
        errors.append("frozen-start fast arm changed fixed task/UNKNOWN accounting")
    if not (ben_fast["verified_net_useful_value"] > ben_slow["verified_net_useful_value"]):
        errors.append("beneficial expansion control did not improve verified net value")
    if not (adv_fast["verified_net_useful_value"] < adv_slow["verified_net_useful_value"]):
        errors.append("adverse task-mix control did not reduce verified net value")
    if adv_slow["forbidden_effects"] or adv_fast["forbidden_effects"]:
        errors.append("forbidden effect occurred")
    if adv_fast["verifier_demand"] > TABLE["adverse_mix"]["verifier_capacity"]:
        errors.append("verifier capacity exceeded")
    return errors


def _controls(raw):
    mutations = {
        "drop_skipped_opportunity": lambda x: x["rows"].pop(),
        "change_opportunity_identity": lambda x: x["rows"][0].__setitem__("opportunity_id", "forged"),
        "start_forbidden_task": lambda x: x["rows"][3].__setitem__("started", True),
        "score_unknown_as_success": lambda x: x["rows"][1].__setitem__("endpoint", 0),
        "corrupt_session_net_value": lambda x: x["summaries"][0].__setitem__("verified_net_useful_value", 999),
        "alter_ex_ante_value": lambda x: x["rows"][8].__setitem__("ex_ante_value", 999),
        "mismatched_opportunity_set": lambda x: x.__setitem__("opportunity_set_id", "route-specific"),
        "change_route_policy": lambda x: x["rows"][0].__setitem__("policy", "posthoc-selected"),
    }
    results = {}
    for name, mutation in mutations.items():
        altered = deepcopy(raw)
        mutation(altered)
        results[name] = bool(_core(altered))
    return results


def audit(raw):
    errors = _core(raw)
    controls = _controls(raw) if not errors else {}
    if controls and not all(controls.values()):
        errors.append("a mutation control was accepted")
    return {"status": "PASS" if not errors and len(controls) == 8 else "FAIL",
            "errors": errors, "corruption_controls_passed": sum(controls.values()),
            "corruption_controls": controls, "auditor": "independent-raw-only-5702-t0-v1"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as source:
        print(json.dumps(audit(json.load(source)), sort_keys=True, separators=(",", ":")))
