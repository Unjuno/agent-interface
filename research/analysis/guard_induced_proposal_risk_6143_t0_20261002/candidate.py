"""Deterministic candidate accounting for the frozen synthetic T0 fixture."""
import json
import sys


def summarize_arm(arm, total, unsafe_reject_num, unsafe_reject_den,
                  safe_reject_num, safe_reject_den, guarded):
    unsafe = arm["unsafe_proposals"]
    safe = total - unsafe
    unsafe_rejected = (unsafe * unsafe_reject_num // unsafe_reject_den
                       if guarded else 0)
    safe_rejected = (safe * safe_reject_num // safe_reject_den
                     if guarded else 0)
    unsafe_admitted = unsafe - unsafe_rejected
    safe_admitted = safe - safe_rejected
    return {
        "arm_id": arm["id"],
        "opportunities": total,
        "proposals": unsafe + safe,
        "unsafe_proposals": unsafe,
        "safe_proposals": safe,
        "unsafe_rejected": unsafe_rejected,
        "safe_rejected": safe_rejected,
        "refusals": unsafe_rejected + safe_rejected,
        "unsafe_admitted": unsafe_admitted,
        "safe_admitted": safe_admitted,
        "harmful_admissions": unsafe_admitted,
        "unfinished": unsafe_admitted,
        "retries": arm["retries"],
        "harm_per_opportunity": unsafe_admitted / total,
        "unsafe_rejection_sensitivity": (
            unsafe_rejected / unsafe if unsafe else None),
        "safe_false_rejection_rate": safe_rejected / safe if safe else None,
    }


def run(fixture):
    total = fixture["opportunities_per_arm"]
    un = fixture["unsafe_rejection_numerator"]
    ud = fixture["unsafe_rejection_denominator"]
    sn = fixture["safe_rejection_numerator"]
    sd = fixture["safe_rejection_denominator"]
    worlds = []
    for world in fixture["worlds"]:
        arms = []
        for arm in world["arms"]:
            guarded = arm["id"] != "conservative_no_guard"
            arms.append(summarize_arm(arm, total, un, ud, sn, sd, guarded))
        worlds.append({"world_id": world["id"], "arms": arms})
    return {"schema": "guard-proposal-risk-result-v1", "worlds": worlds}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    print(json.dumps(run(fixture), sort_keys=True, separators=(",", ":")))
