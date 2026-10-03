"""Raw-only independent audit; deliberately does not import candidate.py."""
import hashlib
import json
import sys

POLICIES = ("raw", "fixed_hysteresis", "minimum_dwell")


def reconstruct(symbols, policy):
    out, state, wait = [], 0, 0
    for x in symbols:
        risk, stale, critical = x % 5, x // 5 % 2 == 1, x >= 10
        if policy == "raw":
            state = int(stale or critical or risk >= 3)
        elif stale:
            state, wait = 0, 0
            out.append(1)
            continue
        elif critical:
            state = 1
            if policy == "minimum_dwell": wait = 2
        elif policy == "fixed_hysteresis":
            if state == 0 and risk >= 3: state = 1
            elif state == 1 and risk <= 1: state = 0
        elif policy == "minimum_dwell":
            if state == 0 and risk >= 3: state, wait = 1, 2
            elif state == 1:
                if wait: wait -= 1
                elif risk < 3: state = 0
        else:
            raise ValueError("unknown policy")
        out.append(state)
    return out


def oracle(case, modes):
    violations = []
    for i, need in enumerate(case.get("required_modes", [])):
        if modes[i] != need: violations.append({"index":i,"kind":"required_mode"})
    for i, allowed in enumerate(case.get("allowed_modes", [])):
        if modes[i] not in allowed: violations.append({"index":i,"kind":"mode_not_allowed"})
    for i in case.get("prefix_forbidden", []):
        if modes[i] == 1: violations.append({"index":i,"kind":"forbidden_prefix_escalation"})
    valid = not violations
    effect = case["effect_if_valid"] if valid else case["effect_if_invalid"]
    switches = sum(a != b for a,b in zip(modes,modes[1:]))
    cost = switches * case["boundary_cost"]
    return {"valid":valid,"effect":effect,"violations":violations,"boundary_cost":cost}


def verify(fixture, raw):
    errors=[]
    try: payload=json.loads(raw)
    except Exception as exc: return {"audit_pass":False,"errors":["json:"+type(exc).__name__]}
    expected_ids=[c["id"] for c in fixture["cases"]]
    rows=payload.get("rows",[])
    if payload.get("schema")!="planner-hysteresis-effect-candidate-v1": errors.append("schema")
    if [r.get("id") for r in rows] != expected_ids: errors.append("row_identity_or_order")
    if len(rows)!=len(fixture["cases"]): errors.append("row_count")
    result=[]
    for case,row in zip(fixture["cases"],rows):
        if row.get("symbols")!=case["symbols"]: errors.append("symbols:"+case["id"])
        schedule=row.get("schedules",{})
        for p in POLICIES:
            expected=reconstruct(case["symbols"],p)
            if schedule.get(p)!=expected: errors.append("schedule:"+case["id"]+":"+p)
            result.append({"id":case["id"],"policy":p,**oracle(case,expected)})
    by={(x["id"],x["policy"]):x for x in result}
    benign=by.get(("B1","fixed_hysteresis"),{}).get("valid") and by.get(("B1","fixed_hysteresis"),{}).get("effect")==by.get(("B1","raw"),{}).get("effect")
    harmful=not by.get(("H1","fixed_hysteresis"),{}).get("valid",True)
    unsafe_prefix=not by.get(("P1","fixed_hysteresis"),{}).get("valid",True)
    raw_cost=by.get(("B1","raw"),{}).get("boundary_cost")
    hyst_cost=by.get(("B1","fixed_hysteresis"),{}).get("boundary_cost")
    cost_reduced=raw_cost is not None and hyst_cost is not None and hyst_cost < raw_cost
    summary={"benign_divergence_witness":bool(benign),"harmful_divergence_witness":bool(harmful),"unsafe_prefix_witness":bool(unsafe_prefix),"benign_boundary_cost_reduced":cost_reduced,"method_disposition":"METHOD_PASS_SCOPED" if benign and harmful and unsafe_prefix and cost_reduced and not errors else "HOLD_OR_FAIL"}
    return {"audit_pass":not errors,"errors":errors,"candidate_sha256":hashlib.sha256(raw).hexdigest(),"rows":result,"summary":summary}


if __name__=="__main__":
    fixture=json.load(open(sys.argv[1],encoding="utf-8"))
    raw=sys.stdin.buffer.read()
    result=verify(fixture,raw)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    raise SystemExit(0 if result["audit_pass"] else 1)
