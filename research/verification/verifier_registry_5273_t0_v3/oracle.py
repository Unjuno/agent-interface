"""Test oracle, independent of candidate; audit.py carries its own literal map."""
EXPECTED_ROWS={
    "c1":("COMPATIBLE",(),12),
    "c2":("REJECTED",("unsupported_primitive","wrong_evidence_role"),12),
    "c3":("REJECTED",("wrong_evidence_role",),12),
    "c4":("REJECTED",("wrong_output_role",),12),
    "c5":("REJECTED",("stale_version",),12),
    "c6":("UNAVAILABLE",("verifier_unknown",),None),
    "c7":("UNAVAILABLE",("resource_unavailable","latency_unqualified"),120),
    "c8":("REJECTED",("budget_exceeded",),80),
    "c9":("REJECTED",("stale_version","side_effect_prohibited","resource_unavailable","latency_unqualified"),900),
    "c10":("REJECTED",("deadline_infeasible",),12),
    "c11":("UNAVAILABLE",("resource_unavailable","latency_unqualified"),120),
    "c12":("COMPATIBLE",(),12),
}


def expected_plan(check_ids):
    rows=[EXPECTED_ROWS[check_id] for check_id in check_ids]
    status="REJECTED" if any(row[0]=="REJECTED" for row in rows) else "UNAVAILABLE" if any(row[0]=="UNAVAILABLE" for row in rows) else "COMPATIBLE"
    reasons=[{"check_id":check_id,"reason":reason}
             for check_id in check_ids for reason in EXPECTED_ROWS[check_id][1]]
    return status,reasons
