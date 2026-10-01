"""Deterministic finite opportunity-stream fixture for Issue #5702 T0."""
import json


CASES = {
    "no_rebound": {
        "policy": "frozen_start",
        "budget": 12,
        "verifier_capacity": 8,
        "opportunities": [
            {"id": "A", "arrival": 0, "value": 10, "endpoint": 10, "mandatory": True, "safe": True,
             "slow_action": 2, "fast_action": 1, "verifier": 1},
            {"id": "U", "arrival": 1, "value": 0, "endpoint": "UNKNOWN", "mandatory": True, "safe": True,
             "slow_action": 2, "fast_action": 1, "verifier": 1},
            {"id": "B", "arrival": 2, "value": 100, "endpoint": 100, "mandatory": False, "safe": True,
             "slow_action": 1, "fast_action": 1, "verifier": 1},
            {"id": "D", "arrival": 3, "value": 1000, "endpoint": 1000, "mandatory": False, "safe": False,
             "slow_action": 1, "fast_action": 1, "verifier": 1},
        ],
    },
    "beneficial_expansion": {
        "policy": "positive_ex_ante_net_value",
        "budget": 5,
        "verifier_capacity": 4,
        "opportunities": [
            {"id": "A", "arrival": 0, "value": 10, "endpoint": 10, "mandatory": True, "safe": True,
             "slow_action": 2, "fast_action": 1, "verifier": 1},
            {"id": "B", "arrival": 1, "value": 7, "endpoint": 7, "mandatory": False, "safe": True,
             "slow_action": 4, "fast_action": 2, "verifier": 1},
            {"id": "D", "arrival": 2, "value": 1000, "endpoint": 1000, "mandatory": False, "safe": False,
             "slow_action": 1, "fast_action": 1, "verifier": 1},
        ],
    },
    "adverse_mix": {
        "policy": "positive_ex_ante_net_value",
        "budget": 7,
        "verifier_capacity": 3,
        "opportunities": [
            {"id": "A", "arrival": 0, "value": 10, "endpoint": 10, "mandatory": True, "safe": True,
             "slow_action": 2, "fast_action": 1, "verifier": 1},
            {"id": "B", "arrival": 1, "value": 4, "endpoint": 1, "mandatory": False, "safe": True,
             "slow_action": 4, "fast_action": 1, "verifier": 2},
            {"id": "C", "arrival": 2, "value": 8, "endpoint": 8, "mandatory": False, "safe": True,
             "slow_action": 3, "fast_action": 2, "verifier": 1},
            {"id": "D", "arrival": 3, "value": 1000, "endpoint": 1000, "mandatory": False, "safe": False,
             "slow_action": 1, "fast_action": 1, "verifier": 1},
        ],
    },
}


def _arm(case_id, spec, route):
    remaining = spec["budget"]
    verifier_remaining = spec["verifier_capacity"]
    records = []
    for opportunity in sorted(spec["opportunities"], key=lambda row: row["arrival"]):
        action_cost = opportunity[f"{route}_action"]
        verifier = opportunity["verifier"]
        expected_net = opportunity["value"] - action_cost - verifier
        if not opportunity["safe"]:
            decision = "BLOCKED_UNSAFE"
        elif opportunity["mandatory"]:
            decision = "MANDATORY"
        elif spec["policy"] == "frozen_start":
            decision = "SKIP_FIXED_WORKLOAD"
        elif expected_net <= 0:
            decision = "SKIP_NONPOSITIVE_EX_ANTE_NET"
        elif action_cost + verifier > remaining or verifier > verifier_remaining:
            decision = "SKIP_BUDGET_OR_VERIFIER_CAPACITY"
        else:
            decision = "START_OPTIONAL"
        started = decision == "MANDATORY" or decision == "START_OPTIONAL"
        spent = action_cost + verifier if started else 0
        if started:
            remaining -= spent
            verifier_remaining -= verifier
        records.append({
            "case_id": case_id,
            "route": route,
            "policy": spec["policy"],
            "budget": spec["budget"],
            "verifier_capacity": spec["verifier_capacity"],
            "opportunity_id": opportunity["id"],
            "arrival": opportunity["arrival"],
            "offered": True,
            "ex_ante_value": opportunity["value"],
            "endpoint": opportunity["endpoint"] if started else "NOT_STARTED",
            "mandatory": opportunity["mandatory"],
            "safe": opportunity["safe"],
            "decision": decision,
            "started": started,
            "completed": started and opportunity["endpoint"] != "UNKNOWN",
            "action_cost_if_started": action_cost,
            "verifier_demand_if_started": verifier,
            "realized_resource_spend": spent,
            "forbidden_effect": started and not opportunity["safe"],
        })
    return records


def build():
    rows = [row for case_id, spec in CASES.items() for route in ("slow", "fast")
            for row in _arm(case_id, spec, route)]
    summaries = []
    for case_id in CASES:
        for route in ("slow", "fast"):
            arm_rows = [row for row in rows if row["case_id"] == case_id and row["route"] == route]
            started = [row for row in arm_rows if row["started"]]
            useful = sum(row["endpoint"] for row in started if isinstance(row["endpoint"], int))
            spend = sum(row["realized_resource_spend"] for row in arm_rows)
            summaries.append({
                "case_id": case_id,
                "route": route,
                "offered": len(arm_rows),
                "started": len(started),
                "completed": sum(row["completed"] for row in arm_rows),
                "unknown_started": sum(row["started"] and row["endpoint"] == "UNKNOWN" for row in arm_rows),
                "verified_useful_value": useful,
                "resource_spend": spend,
                "verified_net_useful_value": useful - spend,
                "forbidden_effects": sum(row["forbidden_effect"] for row in arm_rows),
                "skipped_offered": sum(not row["started"] for row in arm_rows),
                "verifier_demand": sum(row["verifier_demand_if_started"] for row in started),
            })
    return {
        "schema": "endogenous-demand-rebound-5702-t0-v1",
        "opportunity_set_id": "frozen-5702-t0-opportunities-v1",
        "cases": list(CASES),
        "rows": rows,
        "summaries": summaries,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, separators=(",", ":")))
