"""Independent oracle replay; deliberately imports no candidate code."""
ALLOCATION = "AMENDMENT-EFFECT-LEDGER-6219-T0-CPU-20261002-01"

def reference(case):
    a=case["amendment"]
    if a.get("authenticated") is None:
        return {"disposition":"HOLD_AMBIGUOUS_AMENDMENT","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    if a.get("authenticated") is not True:
        return {"disposition":"REJECT_UNAUTHENTICATED","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    newgen=a["generation"]
    stale=[x["id"] for x in case["proposals"] if x["generation"] < newgen]
    prior=case["effects"]
    goals=a["clauses"]
    if any(x["state"]=="UNKNOWN" for x in prior):
        return {"disposition":"HOLD_UNKNOWN_DELIVERY","generation":newgen,"retained_effects":prior,"open_clauses":goals,"rejected_proposals":stale}
    impossible=any(x["state"]=="COMMITTED_VERIFIED" and x["clause"] not in goals and x["reversible"] is False for x in prior)
    if impossible:
        return {"disposition":"IMPOSSIBLE_TO_FULLY_SATISFY","generation":newgen,"retained_effects":prior,"open_clauses":goals,"rejected_proposals":stale}
    undo=[x["clause"] for x in prior if x["state"]=="COMMITTED_VERIFIED" and x["clause"] not in goals and x["reversible"] is True]
    if undo:
        if a.get("compensation_allowed") is not True:
            return {"disposition":"HOLD_COMPENSATION_NOT_AUTHORIZED","generation":newgen,"retained_effects":prior,"open_clauses":goals,"rejected_proposals":stale}
        return {"disposition":"COMPENSATION_REQUIRED","generation":newgen,"retained_effects":prior,"open_clauses":goals,"rejected_proposals":stale,"compensation_clauses":undo}
    if len(goals)==0:
        return {"disposition":"SATISFIED_NO_EFFECT" if len(prior)==0 else "SATISFIED_EFFECTS_RETAINED","generation":newgen,"retained_effects":prior,"open_clauses":[],"rejected_proposals":stale}
    done={x["clause"] for x in prior if x["state"]=="COMMITTED_VERIFIED"}
    return {"disposition":"CONTINUE_NEW_GENERATION","generation":newgen,"retained_effects":prior,"open_clauses":[x for x in goals if x not in done],"rejected_proposals":stale}

def baseline_reference(case,policy):
    a=case["amendment"]
    if policy=="old_plan":
        return {"disposition":"CONTINUE_OLD_PLAN","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    if policy=="prompt_reset":
        return {"disposition":"PROMPT_RESET_ONLY","generation":a["generation"],"retained_effects":[],"open_clauses":a["clauses"],"rejected_proposals":[]}
    if policy=="blanket_undo":
        return {"disposition":"BLANKET_UNDO_ALL" if len(case["effects"]) else "BLANKET_RESTART","generation":a["generation"],"retained_effects":[],"open_clauses":a["clauses"],"rejected_proposals":[]}
    raise ValueError("unknown baseline")

def audit(fixture,oracle,raw):
    errors=[]
    if raw.get("schema")!="amendment-effect-candidate-raw-v1": errors.append("SCHEMA")
    if raw.get("allocation")!=fixture.get("allocation") or raw.get("allocation")!=ALLOCATION: errors.append("ALLOCATION")
    if raw.get("main_sha")!=fixture.get("main_sha"): errors.append("MAIN_SHA")
    expect={(c["id"],p) for c in fixture["cases"] for p in fixture["policies"]}
    rows={(r.get("case_id"),r.get("policy")):r for r in raw.get("rows",[])}
    if len(rows)!=len(raw.get("rows",[])) or set(rows)!=expect: errors.append("COVERAGE_OR_DUPLICATE")
    reconstructed=[]
    for c in fixture["cases"]:
        ref=reference(c)
        if oracle.get("expected_disposition",{}).get(c["id"])!=ref["disposition"]: errors.append("ORACLE_CONTRACT:"+c["id"])
        for p in fixture["policies"]:
            row=rows.get((c["id"],p))
            if row is None: continue
            if p=="obligation_ledger":
                if row.get("result")!=ref: errors.append("LEDGER_MISMATCH:"+c["id"])
            elif row.get("result")!=baseline_reference(c,p): errors.append("BASELINE_MISMATCH:"+c["id"]+":"+p)
            reconstructed.append({"case_id":c["id"],"policy":p,"disposition":row.get("result",{}).get("disposition")})
    matches={p:sum(1 for c in fixture["cases"] if rows.get((c["id"],p),{}).get("result")==reference(c)) for p in fixture["policies"]}
    return {"status":"METHOD_PASS_SCOPED" if not errors else "METHOD_FAIL","errors":errors,"rows":len(raw.get("rows",[])),"reconstructed":reconstructed,"exact_oracle_matches_by_policy":matches}
