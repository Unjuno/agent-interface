"""Independent raw-only integer auditor; does not import candidate code."""
import json
import sys


EXPECTED = {
    "compensation": [("conservative_no_guard", 50, 0),
                     ("aggressive_guard_adapted", 600, 100)],
    "null_adaptation": [("conservative_no_guard", 50, 0),
                        ("conservative_guard", 50, 0)],
    "protective_adaptation": [("conservative_no_guard", 50, 0),
                              ("more_conservative_guard_adapted", 20, 0)],
}


def expected_arm(arm_id, unsafe, retries, total, numerator, denominator,
                 guarded):
    rejected = unsafe * numerator // denominator if guarded else 0
    admitted = unsafe - rejected
    return {
        "arm_id": arm_id,
        "opportunities": total,
        "proposals": total,
        "unsafe_proposals": unsafe,
        "safe_proposals": total - unsafe,
        "unsafe_rejected": rejected,
        "safe_rejected": 0,
        "refusals": rejected,
        "unsafe_admitted": admitted,
        "safe_admitted": total - unsafe,
        "harmful_admissions": admitted,
        "unfinished": admitted,
        "retries": retries,
        "harm_per_opportunity": admitted / total,
        "unsafe_rejection_sensitivity": rejected / unsafe if unsafe else None,
        "safe_false_rejection_rate": 0.0,
    }


def audit(fixture, candidate):
    errors = []
    total = fixture.get("opportunities_per_arm")
    if type(total) is not int or total != 1000:
        errors.append("opportunity_denominator_mismatch")
        total = 1000
    n = fixture.get("unsafe_rejection_numerator")
    d = fixture.get("unsafe_rejection_denominator")
    if type(n) is not int or type(d) is not int or (n, d) != (9, 10):
        errors.append("guard_unsafe_rejection_contract_mismatch")
        n, d = 9, 10
    sn = fixture.get("safe_rejection_numerator")
    sd = fixture.get("safe_rejection_denominator")
    if type(sn) is not int or type(sd) is not int or (sn, sd) != (0, 1):
        errors.append("guard_safe_rejection_contract_mismatch")

    source = {world.get("id"): world for world in fixture.get("worlds", [])}
    observed = {world.get("world_id"): world for world in candidate.get("worlds", [])}
    if set(source) != set(EXPECTED) or set(observed) != set(EXPECTED):
        errors.append("world_set_mismatch")
    rows = {}
    for wid, specs in EXPECTED.items():
        world = source.get(wid, {})
        arms_in = {arm.get("id"): arm for arm in world.get("arms", [])}
        out_world = observed.get(wid, {})
        arms_out = {arm.get("arm_id"): arm for arm in out_world.get("arms", [])}
        if set(arms_in) != {s[0] for s in specs}:
            errors.append(wid + ":source_arm_set_mismatch")
        if set(arms_out) != {s[0] for s in specs}:
            errors.append(wid + ":result_arm_set_mismatch")
        expected_rows = []
        for arm_id, unsafe, retries in specs:
            a = arms_in.get(arm_id, {})
            if type(a.get("unsafe_proposals")) is not int or a.get("unsafe_proposals") != unsafe:
                errors.append(wid + ":unsafe_proposal_count_mismatch:" + arm_id)
            if type(a.get("retries")) is not int or a.get("retries") != retries:
                errors.append(wid + ":retry_count_mismatch:" + arm_id)
            row = expected_arm(arm_id, unsafe, retries, total, n, d,
                               arm_id != "conservative_no_guard")
            expected_rows.append(row)
            if arms_out.get(arm_id) != row:
                errors.append(wid + ":summary_mismatch:" + arm_id)
        rows[wid] = expected_rows

    # Frozen method-gate conditions, derived independently from integer rows.
    comp = rows.get("compensation", [])
    null = rows.get("null_adaptation", [])
    prot = rows.get("protective_adaptation", [])
    if len(comp) == 2 and [x["harmful_admissions"] for x in comp] != [50, 60]:
        errors.append("compensation_harm_gate")
    if len(null) == 2 and [x["unsafe_proposals"] for x in null] != [50, 50]:
        errors.append("null_proposal_mix_gate")
    if len(null) == 2 and [x["harmful_admissions"] for x in null] != [50, 5]:
        errors.append("null_harm_gate")
    if len(prot) == 2 and not prot[1]["harmful_admissions"] < 5:
        errors.append("protective_harm_gate")

    return {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "world_count": len(EXPECTED), "arm_rows": sum(map(len, rows.values())),
            "errors": errors, "gate": {
                "compensation_harm_per_1000": [x["harmful_admissions"] for x in comp],
                "null_harm_per_1000": [x["harmful_admissions"] for x in null],
                "protective_guard_harm_per_1000": prot[1]["harmful_admissions"] if len(prot) == 2 else None,
                "unsafe_rejection_sensitivity": comp[1]["unsafe_rejection_sensitivity"] if len(comp) == 2 else None,
                "safe_false_rejection_rate": comp[1]["safe_false_rejection_rate"] if len(comp) == 2 else None}}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        candidate = json.load(f)
    print(json.dumps(audit(fixture, candidate), sort_keys=True, separators=(",", ":")))
