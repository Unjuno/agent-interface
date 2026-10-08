"""Finite synthetic verifier-cascade replay; emits one JSON object per tick."""
import json
import sys


def replay(fixture):
    rows = []
    capacity = fixture["total_capacity_per_tick"]
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            primary = retry = safety = 0
            for tick in range(fixture["ticks"]):
                fault = tick < case["fault_ticks"]
                primary_before, retry_before, safety_before = primary, retry, safety
                external = case["external_primary_per_tick"]
                safety_arrival = fixture["safety_arrival_per_tick"]
                trigger_retry = fixture["trigger_retry_arrival_per_fault_tick"] if fault else 0
                feedback_retry = 0
                if (not fault and policy == "legacy_shared_retry"
                        and case["feedback_after_trigger"] and retry_before > 0):
                    feedback_retry = fixture["feedback_retry_arrival_per_tick"]
                retry_dropped = 0
                if policy == "debt_shed_reserved" and tick == case["fault_ticks"]:
                    retry_dropped = retry_before

                p_available = primary_before + external
                r_available = retry_before + trigger_retry + feedback_retry - retry_dropped
                s_available = safety_before + safety_arrival
                failed_use = fixture["outage_failed_attempt_resource_per_tick"] if fault else 0
                if fault:
                    p_service = r_service = 0
                    safety_service = min(s_available, 1) if policy == "debt_shed_reserved" else min(s_available, capacity - failed_use)
                elif policy == "debt_shed_reserved":
                    safety_service = min(s_available, 1)
                    budget = capacity - safety_service
                    p_service = min(p_available, budget)
                    r_service = min(r_available, budget - p_service)
                else:
                    budget = capacity
                    p_service = min(p_available, budget)
                    r_service = min(r_available, budget - p_service)
                    safety_service = min(s_available, capacity - p_service - r_service)

                primary = p_available - p_service
                retry = r_available - r_service
                safety = s_available - safety_service
                used = p_service + r_service + safety_service + failed_use
                rows.append({
                    "case": case["id"], "policy": policy, "tick": tick,
                    "fault_active": fault,
                    "primary_before": primary_before, "external_primary_arrival": external,
                    "primary_service": p_service, "primary_after": primary,
                    "retry_before": retry_before, "trigger_retry_arrival": trigger_retry,
                    "feedback_retry_arrival": feedback_retry, "retry_dropped": retry_dropped,
                    "retry_service": r_service, "retry_after": retry,
                    "safety_before": safety_before, "safety_arrival": safety_arrival,
                    "safety_service": safety_service, "safety_after": safety,
                    "failed_attempt_resource": failed_use,
                    "total_capacity": capacity, "total_resource_used": used,
                    "authority_admissions": 0,
                })
                if max(primary, retry, safety) > fixture["queue_limit"]:
                    raise ValueError("QUEUE_LIMIT_EXCEEDED")
                if used > capacity:
                    raise ValueError("JOINT_CAPACITY_EXCEEDED")
    return rows


if __name__ == "__main__":
    source, destination = sys.argv[1:3]
    with open(source, encoding="utf-8") as stream:
        fixture = json.load(stream)
    rows = replay(fixture)
    with open(destination, "w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "cases": len(fixture["cases"]), "policies": len(fixture["policies"])}))
