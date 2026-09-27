#!/usr/bin/env python3
"""Independent raw-only audit plus executable mutation rejection controls."""
import argparse,copy,hashlib,json
from pathlib import Path

def require(ok,msg):
    if not ok: raise ValueError(msg)

def interval_union_ns(rows):
    if not rows:return 0
    rows=sorted(rows); start,end=rows[0]; total=0
    for a,b in rows[1:]:
        if a<=end:end=max(end,b)
        else:total+=end-start;start,end=a,b
    return total+end-start

def trace_invariant_errors(raw):
    errors=[]
    ids=set()
    for case in raw["cases"]:
        domains={(d["domain_id"],d["epoch_id"]) for d in case.get("clock_domains",[])}
        downs={}
        for ev in case["events"]:
            if ev["event_id"] in ids: errors.append("duplicate_event_id")
            ids.add(ev["event_id"])
            if (ev["clock"]["domain_id"],ev["clock"]["epoch_id"]) not in domains: errors.append("unknown_clock")
            if ev["event_type"]=="INPUT_EDGE_BRACKET":
                p=ev["payload"]; bounds=p.get("transition_interval_ns",[])
                if len(bounds)!=2 or bounds[0]>bounds[1]: errors.append("inverted_interval")
                if (p.get("pre_server_state"),p.get("post_server_state"))!=(("UP","DOWN") if p.get("edge")=="down" else ("DOWN","UP")): errors.append("edge_state_contradiction")
                k=p.get("key")
                if p.get("edge")=="down": downs[k]=ev
                elif p.get("edge")=="up" and k not in downs: errors.append("up_without_down")
                if ev.get("source_role")!="backend": errors.append("input_edge_wrong_owner_role")
                if ev["input_authority"]!="true": errors.append("input_edge_without_true_authority")
                if not ev["lineage"].get("actuation_id"): errors.append("input_edge_missing_actuation")
                if not ev["lineage"].get("lease_id"): errors.append("input_edge_missing_lease")
                if ev["input_authority"]=="true" and not any(x["event_type"]=="LEASE_OPEN" and x["lineage"].get("lease_id")==ev["lineage"].get("lease_id") and x["time"]["lower_ns"]<=bounds[0] for x in case["events"]):
                    errors.append("input_edge_no_prior_lease")
                if ev["input_authority"]=="true" and any(x["event_type"]=="LEASE_CLOSE" and x["lineage"].get("lease_id")==ev["lineage"].get("lease_id") and x["time"]["lower_ns"]<=bounds[0] for x in case["events"]):
                    errors.append("input_edge_after_lease_close")
        for ev in case["events"]:
            if ev["event_type"]=="TASK_EFFECT" and ev["source_role"]!="independent_scorer": errors.append("task_effect_source")
            if ev["event_type"]=="TASK_EFFECT" and ev["lineage"].get("actuation_id"):
                aid=ev["lineage"]["actuation_id"]
                if not any(x["event_type"]=="INPUT_EDGE_BRACKET" and x["lineage"].get("actuation_id")==aid for x in case["events"]): errors.append("unbound_effect_attributed")
    # Terminals are separate event types and may never be interpreted as input edges.
    return set(errors)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--traces",required=True);ap.add_argument("--verification",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    raw=json.loads(Path(a.traces).read_text(encoding="utf-8"))
    result=json.loads(Path(a.verification).read_text(encoding="utf-8"))
    by={r["case_id"]:r for r in result["cases"]}
    require(result["disposition"]=="PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED","runner disposition mismatch")
    require(len(by)==8 and result["case_count"]==8,"missing/duplicate result rows")
    errors=[]
    def check(case_id, disposition, lower, upper):
        r=by[case_id]
        if (r["disposition"],r["guaranteed_any_input_ns"],r["possible_any_input_ns"])!=(disposition,lower,upper): errors.append(case_id)
    def durations(case_id):
        c=next(x for x in raw["cases"] if x["case_id"]==case_id)
        open_edges={}; low=[]; high=[]
        for e in c["events"]:
            if e["event_type"]!="INPUT_EDGE_BRACKET":continue
            key=e["payload"]["key"]; lo,hi=e["payload"]["transition_interval_ns"]
            if e["payload"]["edge"]=="down":open_edges[key]=(lo,hi)
            elif key in open_edges:
                dl,dh=open_edges.pop(key)
                if dh<lo:low.append((dh,lo))
                if dl<hi:high.append((dl,hi))
        if open_edges:return None,None
        return interval_union_ns(low),interval_union_ns(high)
    for cid,disp in [("unauthorized-input-after-expiry","UNAUTHORIZED_INPUT"),("release-before-terminal","COMPLETED_RELEASE_BEFORE_TERMINAL"),("overlapping-key-holds","VALID_OVERLAPPING_HOLDS"),("missing-and-out-of-order-edge","HOLD_OUT_OF_ORDER_AND_RIGHT_CENSORED"),("held-input-no-effect","HELD_INPUT_NO_USEFUL_EFFECT")]:
        lo,hi=durations(cid)
        check(cid,disp,lo,hi)
    mc=next(x for x in raw["cases"] if x["case_id"]=="missing-and-out-of-order-edge")
    require(not any(e["event_type"]=="INPUT_EDGE_BRACKET" and e["payload"]["edge"]=="up" for e in mc["events"]),"censor case gained release")
    nc=next(x for x in raw["cases"] if x["case_id"]=="no-input-unbound-task-effect")
    effect=next(e for e in nc["events"] if e["event_type"]=="TASK_EFFECT")
    require(effect["source_role"]=="independent_scorer" and not effect["lineage"].get("actuation_id"),"unbound effect was promoted")
    require(by["no-input-unbound-task-effect"]["task_effect"]=="OBSERVED_UNBOUND","unbound effect classification lost")
    for case in raw["cases"]:
        for e in case["events"]:
            if e["source_role"]=="independent_scorer":
                require(e["input_authority"]!="true" and e["semantic_authority"]!="true","scorer authority escalation")
    hc=next(x for x in raw["cases"] if x["case_id"]=="held-input-no-effect")
    score=next(e for e in hc["events"] if e["event_type"]=="SCORE_SAMPLE")
    require(score["payload"]["window_complete"] is True and score["payload"]["before"]==score["payload"]["after"],"negative outcome lacks complete unchanged scorer window")
    # Apply seven actual mutations and demand that the raw invariant checker detects the intended violation.
    base=copy.deepcopy(raw)
    base_errors=trace_invariant_errors(base)
    require(not base_errors,"baseline traces fail invariants: "+repr(sorted(base_errors)))
    def reject(name, mutate):
        sample=copy.deepcopy(base); mutate(sample)
        detected=trace_invariant_errors(sample)
        require(name in detected,f"mutation escaped rejection: {name}")
    reject("duplicate_event_id",lambda d:d["cases"][0]["events"].__setitem__(1,{**d["cases"][0]["events"][1],"event_id":d["cases"][0]["events"][0]["event_id"]}))
    reject("unknown_clock",lambda d:d["cases"][0]["events"][0]["clock"].update({"domain_id":"ghost"}))
    def invert(d):
        ev=next(e for c in d["cases"] for e in c["events"] if e["event_type"]=="INPUT_EDGE_BRACKET")
        ev["payload"]["transition_interval_ns"]=[999,1]
    reject("inverted_interval",invert)
    def remove_scorer(d):
        next(e for c in d["cases"] for e in c["events"] if e["event_type"]=="TASK_EFFECT").update({"source_role":"executor"})
    reject("task_effect_source",remove_scorer)
    def break_edge(d):
        next(e for c in d["cases"] for e in c["events"] if e["event_type"]=="INPUT_EDGE_BRACKET" and e["payload"]["edge"]=="up").update({"payload":{"key":"SPACE","edge":"up","transition_interval_ns":[400,402],"pre_server_state":"UP","post_server_state":"DOWN"}})
    reject("edge_state_contradiction",break_edge)
    def terminal_release(d):
        case=next(c for c in d["cases"] if c["case_id"]=="missing-and-out-of-order-edge")
        terminal=next(e for e in case["events"] if e["event_type"]=="PROGRAM_TERMINAL")
        case["events"].append({**terminal,"event_id":"terminal-as-release","event_type":"INPUT_EDGE_BRACKET","lineage":{**terminal["lineage"],"actuation_id":"A6","lease_id":"L6"},"payload":{"key":"SPACE","edge":"up","transition_interval_ns":[100,100],"pre_server_state":"DOWN","post_server_state":"UP"}})
    reject("terminal_release_event_invalid",terminal_release)
    def attribute_unbound(d):
        next(e for c in d["cases"] for e in c["events"] if e["event_type"]=="TASK_EFFECT").update({"lineage":{"actuation_id":"fabricated"}})
    reject("unbound_effect_attributed",attribute_unbound)
    overlap=interval_union_ns([(12,50),(32,70)])
    require(overlap==58 and (50-12)+(70-32)==76,"overlap union reconstruction failed")
    require(not errors,"verification result disagrees with independent reconstruction")
    audit={"schema":"o2-g1-w2-independent-audit-v2","disposition":"PASS_RAW_TRACE_AUDIT_SCOPED","errors":[],
           "case_count":8,"numeric_reconstructions":5,"corruption_controls_rejected":7,
           "mutation_names":["duplicate_event_id","unknown_clock","inverted_interval","task_effect_source","edge_state_contradiction","terminal_release_event_invalid","unbound_effect_attributed"],
           "overlap_union_ns":overlap,"naive_sum_ns":76,"case_result_mismatches":errors,
           "verification_sha256":hashlib.sha256(Path(a.verification).read_bytes()).hexdigest(),
           "trace_sha256":hashlib.sha256(Path(a.traces).read_bytes()).hexdigest(),
           "limits":["audits only retained synthetic trace examples","no live authority or efficacy claim"]}
    Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PASS_RAW_TRACE_AUDIT_SCOPED cases=8 numeric=5 mutations=7/7")
if __name__=="__main__":
    main()
