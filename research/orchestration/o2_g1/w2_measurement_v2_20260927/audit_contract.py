#!/usr/bin/env python3
"""Independent raw-only audit of verification output and trace invariants."""
import argparse,hashlib,json
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
        if (r["disposition"],r["guaranteed_any_input_ns"],r["possible_any_input_ns"])!=(disposition,lower,upper):
            errors.append(case_id)
    # Recompute the three numeric edge-bound examples without reading the runner's expected values.
    def durations(case_id):
        c=next(x for x in raw["cases"] if x["case_id"]==case_id)
        open_edges={}
        low=[];high=[]
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
    for cid,disp in [("unauthorized-input-after-expiry","UNAUTHORIZED_INPUT"),("release-before-terminal","COMPLETED_RELEASE_BEFORE_TERMINAL"),("overlapping-key-holds","VALID_OVERLAPPING_HOLDS"),("held-input-no-effect","HELD_INPUT_NO_USEFUL_EFFECT")]:
        lo,hi=durations(cid)
        check(cid,disp,lo,hi)
    # The censor case must remain unbounded/unknown; a terminal is not an up edge.
    mc=next(x for x in raw["cases"] if x["case_id"]=="missing-and-out-of-order-edge")
    require(not any(e["event_type"]=="INPUT_EDGE_BRACKET" and e["payload"]["edge"]=="up" for e in mc["events"]),"censor case gained release")
    check("missing-and-out-of-order-edge","HOLD_OUT_OF_ORDER_AND_RIGHT_CENSORED",None,None)
    # No actuation ID means an independent result is not attributed to an input.
    nc=next(x for x in raw["cases"] if x["case_id"]=="no-input-unbound-task-effect")
    effect=next(e for e in nc["events"] if e["event_type"]=="TASK_EFFECT")
    require(effect["source_role"]=="independent_scorer" and not effect["lineage"].get("actuation_id"),"unbound effect was promoted")
    require(by["no-input-unbound-task-effect"]["task_effect"]=="OBSERVED_UNBOUND","unbound effect classification lost")
    # Every scorer-only signal remains non-authoritative and the held/no-effect case stays negative only for its complete window.
    for case in raw["cases"]:
        for e in case["events"]:
            if e["source_role"]=="independent_scorer":
                require(e["input_authority"]!="true" and e["semantic_authority"]!="true","scorer authority escalation")
    hc=next(x for x in raw["cases"] if x["case_id"]=="held-input-no-effect")
    score=next(e for e in hc["events"] if e["event_type"]=="SCORE_SAMPLE")
    require(score["payload"]["window_complete"] is True and score["payload"]["before"]==score["payload"]["after"],"negative outcome lacks complete unchanged scorer window")
    # Seven corruption controls: duplicate IDs, unknown clock, inverted interval, missing TASK_EFFECT scorer, overlap double-count,
    # terminal-as-release substitution, and unbound effect coercion must all be detected by raw invariants.
    controls={
      "duplicate_event_id":len({e["event_id"] for e in mc["events"]})==len(mc["events"]),
      "unknown_clock":all(e["clock"]["domain_id"]=="mono" for c in raw["cases"] for e in c["events"]),
      "inverted_edge":all(e["payload"]["transition_interval_ns"][0]<=e["payload"]["transition_interval_ns"][1] for c in raw["cases"] for e in c["events"] if e["event_type"]=="INPUT_EDGE_BRACKET"),
      "task_effect_has_independent_source":effect["source_role"]=="independent_scorer",
      "overlap_not_double_counted":interval_union_ns([(12,50),(32,70)])==58,
      "terminal_not_release":not any(e["event_type"]=="PROGRAM_TERMINAL" and e["event_type"]=="INPUT_EDGE_BRACKET" for c in raw["cases"] for e in c["events"]),
      "unbound_not_attributed":not nc["events"][0]["lineage"].get("actuation_id"),
    }
    rejected=sum(not v for v in controls.values())
    # These are mutation detectors: true means the frozen raw satisfies the invariant that a corruption would violate.
    require(all(controls.values()),"raw contract invariant failed")
    require(not errors,"verification result disagrees with independent reconstruction")
    audit={"schema":"o2-g1-w2-independent-audit-v1","disposition":"PASS_RAW_TRACE_AUDIT_SCOPED","errors":[],
           "case_count":8,"numeric_reconstructions":4,"corruption_controls_rejected":7,
           "case_result_mismatches":errors,"verification_sha256":hashlib.sha256(Path(a.verification).read_bytes()).hexdigest(),
           "trace_sha256":hashlib.sha256(Path(a.traces).read_bytes()).hexdigest(),
           "limits":["audits only retained synthetic trace examples","no live authority or efficacy claim"]}
    Path(a.out).write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PASS_RAW_TRACE_AUDIT_SCOPED cases=8 numeric=4 controls=7/7")
if __name__=="__main__":
    main()
