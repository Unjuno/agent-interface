import json
import sys
from pathlib import Path


def make_row(spec, scenario, policy):
    capacity = spec["capacity"]
    offered = scenario["offered"]
    cost = {k: 0 for k in ("admission", "ingress", "parse", "normal_service",
                           "refusal", "quarantine", "safety")}
    completed = refused = deferred = dropped = 0
    if policy == "upstream":
        cost["admission"] = offered * spec["upstream_admission_cost_per_offered"]
        completed = min(offered, spec["upstream_limit"])
        deferred = offered - completed
        cost["normal_service"] = completed * spec["upstream_verifier_cost_per_completed"]
        cost["safety"] = spec["mandatory_safety_cost"]
    else:
        cost["ingress"] = offered
        cost["parse"] = offered
        is_open = scenario["id"] != "bounded"
        if is_open:
            per_refusal = scenario["reject_cost"] + scenario["quarantine_cost"]
            reserved = spec["mandatory_safety_cost"] if policy == "reserved" else 0
            fixed = cost["ingress"] + cost["parse"]
            room = max(0, capacity - reserved - fixed)
            refused = offered if per_refusal == 0 else min(offered, room // per_refusal)
            deferred = offered - refused
            cost["refusal"] = refused * scenario["reject_cost"]
            cost["quarantine"] = refused * scenario["quarantine_cost"]
        else:
            completed = offered
            cost["normal_service"] = completed * spec["normal_service_cost_per_request"]
        used = sum(cost.values())
        if used + spec["mandatory_safety_cost"] <= capacity:
            cost["safety"] = spec["mandatory_safety_cost"]
    return {
        "scenario": scenario["id"], "policy": policy, "eligible": True,
        "offered": offered, "completed": completed, "refused": refused,
        "deferred": deferred, "dropped": dropped, "authority": 0,
        "capacity": capacity, "cost": cost, "total_cost": sum(cost.values())
    }


def run(spec):
    rows = [make_row(spec, s, p) for s in spec["scenarios"] for p in spec["policies"]]
    # Deliberate invalid negative control: the auditor must reject its dropped obligation.
    fault = make_row(spec, spec["scenarios"][0], "upstream")
    fault.update({"scenario": "fault_drop", "eligible": False,
                  "deferred": fault["deferred"] - 1, "dropped": 1})
    rows.append(fault)
    return {"schema": "rejection-cost-raw-a02-v1", "allocation": spec["allocation"], "rows": rows}


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = run(spec)
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in raw["rows"]), encoding="utf-8")
    print(json.dumps({"allocation": raw["allocation"], "rows": len(raw["rows"]), "result": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
