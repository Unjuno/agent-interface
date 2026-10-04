import json
from pathlib import Path

OUT = Path("/out/raw.jsonl")
POLICIES = ("backend", "upstream", "reserved", "control")
CONDITIONS = ("storm", "zero_reject", "bounded", "planted_drop")
TICKS = 30
CAPACITY = 20


def row(policy, condition, tick, offered, admitted, deferred, completed,
        safety, cost, dropped, authority):
    return {"policy": policy, "condition": condition, "tick": tick,
            "offered": offered, "admitted": admitted, "deferred": deferred,
            "completed": completed, "safety": safety,
            "cost": cost, "dropped": dropped, "authority": authority,
            "capacity": CAPACITY}


def main():
    rows = []
    for condition in CONDITIONS:
        backlog = {p: 0 for p in POLICIES}
        for tick in range(TICKS):
            offered = 8 if condition in ("storm", "zero_reject", "planted_drop") and tick < 8 else (2 if tick < 8 else 0)
            reject_cost = 0 if condition == "zero_reject" else (3 if condition == "storm" else 0)
            for policy in POLICIES:
                old = backlog[policy]
                demand = old + offered
                cost = {"ingress": 0, "parse": 0, "reject": 0,
                        "quarantine": 0, "optional_service": 0,
                        "safety_service": 1}
                if policy == "upstream":
                    # Admission work is charged for every offered optional request.
                    cost["ingress"] = offered
                    admitted = min(demand, 2)
                    deferred = demand - admitted
                    cost["optional_service"] = 3 * admitted
                elif policy == "reserved":
                    cost["ingress"] = min(demand, 19)
                    admitted = cost["ingress"]
                    deferred = demand - admitted
                    cost["optional_service"] = 2 * admitted
                    cost["reject"] = reject_cost * (demand - admitted)
                else:
                    cost["ingress"] = demand
                    cost["parse"] = demand
                    admitted = demand
                    deferred = 0
                    cost["optional_service"] = 2 * demand
                    # On an open breaker, every request pays reject and quarantine cost.
                    if condition == "storm" and tick >= 1:
                        cost["reject"] = reject_cost * demand
                        cost["quarantine"] = demand
                        cost["optional_service"] = 0
                total = sum(cost.values())
                safety = int(total <= CAPACITY)
                if not safety:
                    cost["safety_service"] = 0
                    total -= 1
                completed = admitted if safety and policy == "upstream" else 0
                dropped = int(condition == "planted_drop" and policy == "upstream" and tick == 2)
                if dropped:
                    deferred = max(0, deferred - 1)
                backlog[policy] = deferred
                rows.append({**row(policy, condition, tick, offered, admitted,
                                   deferred, completed, safety, cost, dropped, 0),
                             "total_cost": total})
    OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()

