"""Issue #4990; frozen 2026-09-28 19:10 JST (UTC+09:00)."""
import hashlib
import itertools
import json
import sys

OUTCOMES = (
    "SUCCEEDED", "BLOCKED", "AUTHORITY_REQUIRED", "TARGET_NOT_FOUND",
    "CAPABILITY_UNSUPPORTED", "CONFLICT", "IMPOSSIBLE_UNDER_CONSTRAINTS",
    "FAILED_UNKNOWN",
)
FIELDS = ("fresh", "authority", "conflict", "capability", "impossible", "target", "blocked")
EXPECTED_DIGEST = "c9e0871ce3272c99f91db2596fd02ffd3ba941ca10bf8a21662a45a5c302d68a"
EXPECTED_COUNTS = {"SUCCEEDED":3,"BLOCKED":3,"AUTHORITY_REQUIRED":96,"TARGET_NOT_FOUND":6,"CAPABILITY_UNSUPPORTED":24,"CONFLICT":48,"IMPOSSIBLE_UNDER_CONSTRAINTS":12,"FAILED_UNKNOWN":192}

# Decision table is deliberately ordered independently of the input contract.py.
def classify(e, budget):
    if e["fresh"] is not True:
        value = ("FAILED_UNKNOWN", False, "NEW_OBSERVATION")
    elif e["authority"] is not True:
        value = ("AUTHORITY_REQUIRED", False, "FOCUS_OR_LEASE")
    elif e["conflict"] is True:
        value = ("CONFLICT", False, "FRESH_RECONCILIATION")
    elif e["capability"] is not True:
        value = ("CAPABILITY_UNSUPPORTED", False, "ALTERNATIVE_CAPABILITY")
    elif e["impossible"] is True:
        value = ("IMPOSSIBLE_UNDER_CONSTRAINTS", False, "PLANNER_RECONSIDERATION")
    elif e["target"] is not True:
        value = ("TARGET_NOT_FOUND", False, "DIFFERENT_TARGET_OR_OBSERVATION")
    elif e["blocked"] is True:
        value = ("BLOCKED", budget > 0, "UNBLOCK_OR_WAIT")
    else:
        value = ("SUCCEEDED", False, "NONE")
    return {"outcome":value[0],"retryable":value[1],"required_change":value[2],"authority":False}

def oracle(e, budget):
    # This oracle translates the frozen contract's documented precedence into a separately shaped tuple.
    if e["fresh"] is not True: r=("FAILED_UNKNOWN",False,"NEW_OBSERVATION")
    elif e["authority"] is not True: r=("AUTHORITY_REQUIRED",False,"FOCUS_OR_LEASE")
    elif e["conflict"] is True: r=("CONFLICT",False,"FRESH_RECONCILIATION")
    elif e["capability"] is not True: r=("CAPABILITY_UNSUPPORTED",False,"ALTERNATIVE_CAPABILITY")
    elif e["impossible"] is True: r=("IMPOSSIBLE_UNDER_CONSTRAINTS",False,"PLANNER_RECONSIDERATION")
    elif e["target"] is not True: r=("TARGET_NOT_FOUND",False,"DIFFERENT_TARGET_OR_OBSERVATION")
    elif e["blocked"] is True: r=("BLOCKED",budget>0,"UNBLOCK_OR_WAIT")
    else: r=("SUCCEEDED",False,"NONE")
    return {"outcome":r[0],"retryable":r[1],"required_change":r[2],"authority":False}

def fail(label, details=None):
    raise RuntimeError(label + (":" + repr(details) if details is not None else ""))

def validate_budget_monotonicity(low, high, evidence):
    if low["outcome"] != "BLOCKED" and (high["outcome"] != low["outcome"] or high["retryable"] or low["retryable"]):
        fail("budget_changed_hard_outcome", evidence)

def run():
    rows=[]
    for bits in itertools.product((False,True), repeat=len(FIELDS)):
        evidence=dict(zip(FIELDS,bits))
        for budget in range(3):
            actual=classify(evidence,budget); expected=oracle(evidence,budget)
            if actual != expected: fail("oracle_mismatch",(evidence,budget,actual,expected))
            if actual["authority"] is not False: fail("authority_grant",(evidence,budget))
            if (not evidence["fresh"] or not evidence["authority"]) and (actual["outcome"]=="SUCCEEDED" or actual["retryable"]): fail("unsafe_unknown_or_authority",(evidence,budget,actual))
            rows.append({"evidence":evidence,"budget":budget,"result":actual})
    for row in rows:
        result=row["result"]
        if result["outcome"] != "BLOCKED" and result["retryable"]: fail("nonblocked_retry",row)
        if result["outcome"] == "SUCCEEDED" and not (row["evidence"]["fresh"] and row["evidence"]["authority"]): fail("untrusted_success",row)
    for bits in itertools.product((False,True),repeat=len(FIELDS)):
        evidence=dict(zip(FIELDS,bits)); low=classify(evidence,0); high=classify(evidence,2)
        validate_budget_monotonicity(low, high, evidence)
    encoded=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    digest=hashlib.sha256(encoded).hexdigest()
    counts={name:sum(row["result"]["outcome"]==name for row in rows) for name in OUTCOMES}
    if len(rows)!=384: fail("row_count",len(rows))
    if counts!=EXPECTED_COUNTS: fail("outcome_counts",counts)
    if digest!=EXPECTED_DIGEST: fail("result_digest",digest)
    return {"decision":"PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED","rows":len(rows),"counts":counts,"digest":digest,"authority_grants":0,"python":sys.version.split()[0],"optimize":sys.flags.optimize}

if __name__=="__main__": print(json.dumps(run(),sort_keys=True))
