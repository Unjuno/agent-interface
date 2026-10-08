"""Deterministic queue-feedback toy model for Issue #5375, allocation a1.

All values are synthetic integer work units. This is not a production model.
"""
import json
from pathlib import Path

OUT = Path(__file__).with_name("candidate.jsonl")
POLICIES = ("breaker", "debt_shed_reserve", "no_retry")
CASES = (
    # (name, external arrival/tick, transient fault ticks, feedback ratio)
    ("underload_control", 1, 4, 0),
    ("fault_only_control", 2, 4, 0),
    ("feedback_low", 2, 4, 1),
    ("feedback_high", 2, 4, 2),
)
CAPACITY = 3
HORIZON = 24
TRIGGER_END = 4
POST_START = 8
RUNS = []


def run(case, policy):
    name, external, fault_ticks, feedback = case
    backlog = 0
    retry_debt = 0
    rows = []
    for tick in range(HORIZON):
        fault = tick < fault_ticks
        offered = external + (feedback * backlog if tick >= fault_ticks else 0)
        if policy == "debt_shed_reserve" and not fault:
            shed = min(retry_debt, max(0, offered - external))
            retry_debt -= shed
            offered -= shed
        else:
            shed = 0
        service = 0 if fault else CAPACITY
        safety_service = 0 if fault else (1 if policy == "debt_shed_reserve" else 0)
        ordinary_capacity = max(0, service - safety_service)
        admitted = min(backlog + offered, ordinary_capacity)
        backlog = backlog + offered - admitted
        # Fault-generated retries are debt; after fault, breaker/no-retry do not add retries.
        retry_added = min(external, 1) if fault and policy != "no_retry" else 0
        retry_debt += retry_added
        # Reserved policy uses one unit for safety recovery when healthy.
        if not fault and policy != "debt_shed_reserve":
            safety_service = min(service, 1)
        rows.append({
            "tick": tick, "case": name, "policy": policy,
            "external": external, "feedback": feedback,
            "fault": fault, "offered": offered, "shed": shed,
            "queue_before": backlog + admitted - offered,
            "service_capacity": service, "admitted": admitted,
            "queue_after": backlog, "retry_added": retry_added,
            "retry_debt": retry_debt, "safety_service": safety_service,
            "authority_admissions": 0,
        })
    post = rows[POST_START:]
    impairment = all(r["queue_after"] >= 12 and r["safety_service"] == 0 for r in post[-8:])
    rows[-1]["summary"] = {
        "post_trigger_impairment": impairment,
        "final_backlog": backlog,
        "post_trigger_safety_served": sum(r["safety_service"] for r in post),
    }
    RUNS.append({"case": name, "policy": policy, "rows": rows})
    return rows


for case in CASES:
    for policy in POLICIES:
        run(case, policy)

with OUT.open("w", encoding="utf-8", newline="\n") as f:
    for item in RUNS:
        for row in item["rows"]:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps({"runs": len(RUNS), "rows": sum(len(x["rows"]) for x in RUNS), "output": OUT.name}))
