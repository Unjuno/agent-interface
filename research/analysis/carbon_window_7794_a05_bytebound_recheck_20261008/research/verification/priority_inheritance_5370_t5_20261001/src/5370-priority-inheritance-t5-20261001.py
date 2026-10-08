"""T5 host-only discrete scheduler experiment for Issue #5370.

The formal interface is JSON in / stdout.  This file intentionally uses only
the Python standard library so the frozen source can be run offline.
"""
import json


ALLOCATION = "G5370-PRIORITY-INHERITANCE-T5-20261001-01"
BASE_MAIN = "1b561c2978f020ff784480880ac8e7c908ddadfe"
HOLDER_WORK = 2
MEDIUM_WORK = 5
INHERITANCE_BUDGET = 2
HORIZON = 20

CASES = {
    "deadline_order_conflict": [
        {"id": "H1", "arrival": 0, "deadline": 5, "priority": 3, "authenticated": True},
        {"id": "H2", "arrival": 1, "deadline": 3, "priority": 4, "authenticated": True},
    ],
    "equal_deadline_control": [
        {"id": "H1", "arrival": 0, "deadline": 4, "priority": 3, "authenticated": True},
        {"id": "H2", "arrival": 1, "deadline": 4, "priority": 4, "authenticated": True},
    ],
    "forged_urgency_control": [
        {"id": "H1", "arrival": 0, "deadline": 5, "priority": 3, "authenticated": True},
        {"id": "H2", "arrival": 1, "deadline": 3, "priority": 99, "authenticated": False},
    ],
}


def simulate(case_name, jobs, inheritance, waiter_order):
    arrivals = sorted((dict(job) for job in jobs), key=lambda job: (job["arrival"], job["id"]))
    waiters = []
    rejected = []
    completed = []
    stale = []
    schedule = []
    now = 0
    holder_remaining = HOLDER_WORK
    medium_remaining = MEDIUM_WORK
    inherited_ticks = 0
    max_inherited_priority = 1
    holder_release = None

    while now < HORIZON and (holder_remaining or waiters or arrivals or medium_remaining):
        while arrivals and arrivals[0]["arrival"] <= now:
            job = arrivals.pop(0)
            if job["authenticated"]:
                waiters.append(job)
            else:
                rejected.append({"id": job["id"], "reason": "UNAUTHENTICATED_URGENCY"})

        if holder_remaining:
            inherited = [j["priority"] for j in waiters] if inheritance and inherited_ticks < INHERITANCE_BUDGET else []
            effective_holder_priority = max([1] + inherited)
            max_inherited_priority = max(max_inherited_priority, effective_holder_priority)
            medium_priority = 2 if medium_remaining else -1
            if effective_holder_priority >= medium_priority:
                schedule.append({"tick": now, "run": "L", "effective_priority": effective_holder_priority})
                holder_remaining -= 1
                if inheritance and inherited:
                    inherited_ticks += 1
                now += 1
                if holder_remaining == 0:
                    holder_release = now
            else:
                schedule.append({"tick": now, "run": "M"})
                medium_remaining -= 1
                now += 1
            continue

        if waiters:
            if waiter_order == "edf":
                waiters.sort(key=lambda job: (job["deadline"], job["arrival"], job["id"]))
            else:
                waiters.sort(key=lambda job: (job["arrival"], job["id"]))
            job = waiters.pop(0)
            finish = now + 1
            if finish <= job["deadline"]:
                completed.append({"id": job["id"], "finish": finish, "deadline": job["deadline"]})
                schedule.append({"tick": now, "run": job["id"]})
            else:
                stale.append({"id": job["id"], "observed_at": now, "deadline": job["deadline"], "reason": "STALE_ABSTAIN"})
            now = finish
            continue

        if medium_remaining:
            schedule.append({"tick": now, "run": "M"})
            medium_remaining -= 1
            now += 1
        else:
            break

    return {
        "case": case_name,
        "policy": {"inheritance": inheritance, "waiter_order": waiter_order},
        "holder_release": holder_release,
        "inherited_owner_ticks": inherited_ticks,
        "max_inherited_priority": max_inherited_priority,
        "medium_service": MEDIUM_WORK - medium_remaining,
        "completed_before_deadline": completed,
        "stale_abstentions": stale,
        "rejected_unauthenticated": rejected,
        "schedule": schedule,
    }


def main():
    rows = []
    for name in ("deadline_order_conflict", "equal_deadline_control"):
        jobs = CASES[name]
        rows.extend([
            simulate(name, jobs, False, "fifo"),
            simulate(name, jobs, True, "fifo"),
            simulate(name, jobs, True, "edf"),
        ])
    rows.append(simulate("forged_urgency_control", CASES["forged_urgency_control"], True, "edf"))
    print(json.dumps({"allocation": ALLOCATION, "base_main": BASE_MAIN, "rows": rows}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
