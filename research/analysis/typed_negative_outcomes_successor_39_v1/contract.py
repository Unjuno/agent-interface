"""Finite typed negative-outcome contract; no authority or side effects."""
import hashlib
import itertools
import json

OUTCOMES = (
    "SUCCEEDED", "BLOCKED", "AUTHORITY_REQUIRED", "TARGET_NOT_FOUND",
    "CAPABILITY_UNSUPPORTED", "CONFLICT", "IMPOSSIBLE_UNDER_CONSTRAINTS",
    "FAILED_UNKNOWN",
)

def classify(e, budget):
    if not e["fresh"]:
        return {"outcome":"FAILED_UNKNOWN","retryable":False,
                "required_change":"NEW_OBSERVATION","authority":False}
    if not e["authority"]:
        return {"outcome":"AUTHORITY_REQUIRED","retryable":False,
                "required_change":"FOCUS_OR_LEASE","authority":False}
    if e["conflict"]:
        return {"outcome":"CONFLICT","retryable":False,
                "required_change":"FRESH_RECONCILIATION","authority":False}
    if not e["capability"]:
        return {"outcome":"CAPABILITY_UNSUPPORTED","retryable":False,
                "required_change":"ALTERNATIVE_CAPABILITY","authority":False}
    if e["impossible"]:
        return {"outcome":"IMPOSSIBLE_UNDER_CONSTRAINTS","retryable":False,
                "required_change":"PLANNER_RECONSIDERATION","authority":False}
    if not e["target"]:
        return {"outcome":"TARGET_NOT_FOUND","retryable":False,
                "required_change":"DIFFERENT_TARGET_OR_OBSERVATION","authority":False}
    if e["blocked"]:
        return {"outcome":"BLOCKED","retryable":budget > 0,
                "required_change":"UNBLOCK_OR_WAIT","authority":False}
    return {"outcome":"SUCCEEDED","retryable":False,
            "required_change":"NONE","authority":False}

def oracle(e, budget):
    # Independent field-order and control-flow arrangement.
    if e["fresh"] is not True:
        result=("FAILED_UNKNOWN",False,"NEW_OBSERVATION")
    elif e["authority"] is not True:
        result=("AUTHORITY_REQUIRED",False,"FOCUS_OR_LEASE")
    elif e["conflict"] is True:
        result=("CONFLICT",False,"FRESH_RECONCILIATION")
    elif e["capability"] is not True:
        result=("CAPABILITY_UNSUPPORTED",False,"ALTERNATIVE_CAPABILITY")
    elif e["impossible"] is True:
        result=("IMPOSSIBLE_UNDER_CONSTRAINTS",False,"PLANNER_RECONSIDERATION")
    elif e["target"] is not True:
        result=("TARGET_NOT_FOUND",False,"DIFFERENT_TARGET_OR_OBSERVATION")
    elif e["blocked"] is True:
        result=("BLOCKED",budget > 0,"UNBLOCK_OR_WAIT")
    else:
        result=("SUCCEEDED",False,"NONE")
    return {"outcome":result[0],"retryable":result[1],
            "required_change":result[2],"authority":False}

def main():
    fields=("fresh","authority","conflict","capability","impossible","target","blocked")
    rows=[]
    for bits in itertools.product((False,True), repeat=len(fields)):
        evidence=dict(zip(fields,bits))
        for budget in range(3):
            candidate=classify(evidence,budget)
            expected=oracle(evidence,budget)
            assert candidate==expected, (evidence,budget,candidate,expected)
            assert candidate["authority"] is False
            if not evidence["fresh"] or not evidence["authority"]:
                assert candidate["outcome"] != "SUCCEEDED"
                assert candidate["retryable"] is False
            rows.append({"evidence":evidence,"budget":budget,"result":candidate})
    for row in rows:
        if row["result"]["outcome"] != "BLOCKED":
            assert row["result"]["retryable"] is False
        if row["result"]["outcome"] == "SUCCEEDED":
            assert row["evidence"]["fresh"] and row["evidence"]["authority"]
    for bits in itertools.product((False,True), repeat=len(fields)):
        evidence=dict(zip(fields,bits))
        low=classify(evidence,0)
        high=classify(evidence,2)
        if low["outcome"] != "BLOCKED":
            assert high["outcome"] == low["outcome"]
            assert high["retryable"] == low["retryable"] == False
    encoded=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    digest=hashlib.sha256(encoded).hexdigest()
    counts={name:sum(row["result"]["outcome"]==name for row in rows) for name in OUTCOMES}
    print("PASS_TYPED_NEGATIVE_OUTCOMES_SCOPED rows=%d oracle_agreement=%d controls=7 authority_grants=0 digest=%s" %
          (len(rows),len(rows),digest))
    print("OUTCOME_COUNTS",json.dumps(counts,sort_keys=True))
    assert len(rows)==384
    assert counts["SUCCEEDED"]==3
    assert counts["BLOCKED"]==3

if __name__=="__main__":
    main()
