"""Independent exhaustive finite-branch and safe-action auditor."""
import itertools
import json
import sys
from pathlib import Path

LIFETIMES=("FULL","ZERO","EVENT")
PHASES=("PRE_EVENT","POST_EVENT")
EVIDENCE=("VALID_0","VALID_1","MISSING","STALE")
ORDERS=("NATURE_FIRST_PUBLIC","AGENT_FIRST_REACTIVE")


def support(life,phase,evidence):
    if life=="FULL" and evidence=="VALID_0": return [0]
    if life=="FULL" and evidence=="VALID_1": return [1]
    if life=="EVENT" and phase=="POST_EVENT" and evidence=="VALID_0": return [0]
    if life=="EVENT" and phase=="POST_EVENT" and evidence=="VALID_1": return [1]
    return [0,1]


def action(theta): return "A" if theta==0 else "B"


def audit(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8")); errors=[]
    if obj.get("schema")!="issue-6580-t0c-candidate-v1": errors.append("schema")
    rows=obj.get("rows",[])
    seen={}
    for index,row in enumerate(rows):
        key=(row.get("lifetime"),row.get("phase"),row.get("evidence"),row.get("order"))
        if key in seen and (key[3]!="NATURE_FIRST_PUBLIC" or row.get("observed_theta") in seen[key]):
            errors.append(f"duplicate_branch:{index}")
        seen.setdefault(key,set())
        theta=row.get("observed_theta")
        if theta is not None: seen[key].add(theta)
    scenario_keys=list(itertools.product(LIFETIMES,PHASES,EVIDENCE,ORDERS))
    if len(seen)!=48: errors.append("scenario_denominator")
    expected_count=0
    safe_branches=0
    for life,phase,evidence,order in scenario_keys:
        key=(life,phase,evidence,order); possible=support(life,phase,evidence)
        expected_values=possible if order=="NATURE_FIRST_PUBLIC" else [None]
        expected_count+=len(expected_values)
        actual=[r for r in rows if (r.get("lifetime"),r.get("phase"),r.get("evidence"),r.get("order"))==key]
        if len(actual)!=len(expected_values): errors.append(f"branch_count:{key}")
        if {r.get("observed_theta") for r in actual}!=set(expected_values): errors.append(f"branch_coverage:{key}")
        for row in actual:
            if row.get("support")!=possible: errors.append(f"support:{key}")
            theta=row.get("observed_theta")
            if order=="NATURE_FIRST_PUBLIC":
                expected_decision,expected_action,reachable="CONTINUE",action(theta),[theta]
                if theta not in possible: errors.append(f"observation_outside_support:{key}")
                safe_branches+=1
            elif len(possible)==1:
                expected_decision,expected_action,reachable="CONTINUE",action(possible[0]),[possible[0]]
                safe_branches+=1
            else:
                expected_decision,expected_action,reachable="YIELD",None,[]
            if row.get("decision")!=expected_decision: errors.append(f"decision:{key}:{theta}")
            if row.get("action")!=expected_action: errors.append(f"action:{key}:{theta}")
            if row.get("reachable_theta")!=reachable: errors.append(f"reachable:{key}:{theta}")
            if row.get("unsafe_dispatch") is not False: errors.append(f"dispatch:{key}:{theta}")
            if expected_decision=="CONTINUE" and (not reachable or any(expected_action!=action(v) for v in reachable)):
                errors.append(f"unsafe_continue:{key}:{theta}")
    controls=obj.get("negative_controls",[])
    if len(controls)!=6: errors.append("negative_control_denominator")
    expected_controls={(life,order) for life,order in itertools.product(LIFETIMES,ORDERS)}
    observed_controls=[(c.get("lifetime"),c.get("order")) for c in controls]
    if set(observed_controls)!=expected_controls or len(set(observed_controls))!=len(observed_controls): errors.append("negative_control_coverage")
    for c in controls:
        if c.get("decision")!="CONTINUE" or c.get("action")!="SAFE_INDEPENDENT_OF_THETA" or c.get("unsafe_dispatch") is not False: errors.append("negative_control")
    return {"schema":"issue-6580-t0c-audit-v1","status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "scenario_rows_expected":48,"scenario_rows_seen":len(seen),"branch_rows_expected":expected_count,
        "branch_rows_seen":len(rows),"negative_controls_expected":6,"negative_controls_seen":len(controls),
        "nature_first_public_branches_exhaustive":not any("branch_count" in e or "branch_coverage" in e for e in errors),
        "safe_continue_branches_reconstructed":safe_branches,"errors":errors,"model_calls":0,"external_effects":0}


if __name__=="__main__":
    result=audit(sys.argv[1]); Path(sys.argv[2]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result["status"]=="PASS_METHOD_SCOPED" else 1)
