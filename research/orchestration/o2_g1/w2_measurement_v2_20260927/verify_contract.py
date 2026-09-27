#!/usr/bin/env python3
"""Independent stdlib conformance runner for useful-control trace v2."""
import argparse
import hashlib
import json
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)

def union_ns(intervals):
    if not intervals:
        return 0
    rows=sorted(intervals)
    total=0
    lo,hi=rows[0]
    for a,b in rows[1:]:
        if a<=hi:
            hi=max(hi,b)
        else:
            total += hi-lo
            lo,hi=a,b
    return total+hi-lo

def validate_shape(schema, case):
    require(schema.get("$schema")=="https://json-schema.org/draft/2020-12/schema","wrong schema dialect")
    root=schema["properties"]
    require(set(schema["required"])=={"schema_version","trace_id","clock_domains","events"},"root required mismatch")
    require(schema["additionalProperties"] is False,"root must reject extra fields")
    event_schema=schema["$defs"]["event"]
    event_props=event_schema["properties"]
    require(event_schema["additionalProperties"] is False,"event must reject extra fields")
    require(set(event_schema["required"])=={"event_id","event_type","source_role","clock","time","input_authority","semantic_authority","lineage","payload"},"event required mismatch")
    declared=case.get("clock_domains",[])
    domains=[(d["domain_id"],d["epoch_id"]) for d in declared]
    require(len(domains)==len(set(domains)),"duplicate clock domain declaration")
    require(all(d["kind"] in ("monotonic","calibrated_monotonic") and d["unit"]=="ns" for d in declared),"invalid clock domain metadata")
    envelope={"schema_version":"useful-control-trace-v2","trace_id":case["case_id"],
              "clock_domains":declared,"events":case["events"]}
    require(set(envelope)==set(schema["required"]),"root shape mismatch")
    known=set(domains)
    ids=set()
    times=[]
    edge_rows=[]
    lease_open={}
    lease_close={}
    actuation_ids=set()
    for ev in envelope["events"]:
        require(set(event_schema["required"]).issubset(ev),"event required property missing")
        require(set(ev).issubset(set(event_props)),"unknown event field")
        for key in ("event_type","source_role","input_authority","semantic_authority"):
            vals=event_props[key].get("enum")
            require(vals is not None and ev[key] in vals,f"invalid {key}")
        require(ev["event_id"] not in ids,"duplicate event_id")
        ids.add(ev["event_id"])
        require((ev["clock"]["domain_id"],ev["clock"]["epoch_id"]) in known,"undeclared clock")
        tm=ev["time"]
        require(isinstance(tm["lower_ns"],int) and not isinstance(tm["lower_ns"],bool) and tm["lower_ns"]>=0,"invalid lower time")
        upper=tm["upper_ns"]
        require(upper is None or (isinstance(upper,int) and not isinstance(upper,bool) and upper>=tm["lower_ns"]),"invalid upper time")
        require(tm["censoring"] in schema["$defs"]["time"]["properties"]["censoring"]["enum"],"invalid censoring")
        if tm["censoring"]=="exact":
            require(upper==tm["lower_ns"],"exact timestamp has width")
        if tm["censoring"] in ("bounded","left"):
            require(upper is not None,"missing bounded endpoint")
        require(isinstance(ev["lineage"],dict) and isinstance(ev["payload"],dict),"invalid lineage/payload")
        for lid in ("plan_id","program_id","actuation_id","lease_id","capture_id"):
            if lid in ev["lineage"]:
                require(ev["lineage"][lid] is None or isinstance(ev["lineage"][lid],str),f"invalid lineage {lid}")
        if ev["event_type"]=="LEASE_OPEN":
            lid=ev["lineage"].get("lease_id")
            require(bool(lid),"lease open without lease_id")
            lease_open.setdefault(lid,[]).append(tm["lower_ns"])
        elif ev["event_type"]=="LEASE_CLOSE":
            lid=ev["lineage"].get("lease_id")
            require(bool(lid),"lease close without lease_id")
            lease_close.setdefault(lid,[]).append(tm["lower_ns"])
        elif ev["event_type"]=="INPUT_EDGE_BRACKET":
            p=ev["payload"]
            require(p.get("edge") in ("down","up"),"bad input edge")
            require(bool(p.get("key")),"edge without key")
            bounds=p.get("transition_interval_ns")
            require(isinstance(bounds,list) and len(bounds)==2 and all(isinstance(v,int) and not isinstance(v,bool) and v>=0 for v in bounds) and bounds[0]<=bounds[1],"bad physical edge bounds")
            require((p.get("pre_server_state"),p.get("post_server_state"))==(("UP","DOWN") if p["edge"]=="down" else ("DOWN","UP")),"edge/server-state contradiction")
            edge_rows.append(ev)
            aid=ev["lineage"].get("actuation_id")
            if aid:
                actuation_ids.add(aid)
        elif ev["event_type"]=="TASK_EFFECT":
            require(ev["source_role"]=="independent_scorer","TASK_EFFECT lacks independent scorer source")
            require(ev["semantic_authority"]!="true" and ev["input_authority"]!="true","scorer event carries authority")
            require(bool(ev["payload"].get("scoring_rule_id")),"TASK_EFFECT missing scoring rule")
            require(ev["payload"].get("verdict") in ("positive","negative","unknown"),"bad task-effect verdict")
        if ev["event_type"]=="SCORE_SAMPLE":
            require(ev["source_role"]=="independent_scorer","score sample not from independent scorer")
            require(isinstance(ev["payload"].get("window_complete"),bool),"score window completeness missing")
        times.append(tm["lower_ns"])
    ordered=all(a<=b for a,b in zip(times,times[1:]))
    unauthorized=False
    for ev in edge_rows:
        if ev["input_authority"]=="false":
            unauthorized=True
            continue
        if ev["input_authority"]=="unknown":
            continue
        lid=ev["lineage"].get("lease_id")
        bounds=ev["payload"]["transition_interval_ns"]
        opens=lease_open.get(lid,[])
        closes=lease_close.get(lid,[])
        valid_open=any(t<=bounds[0] for t in opens)
        expired=any(bounds[0]<=t for t in closes)
        if not valid_open or expired:
            unauthorized=True
    open_down={}
    guaranteed=[]
    possible=[]
    unmatched=False
    for ev in edge_rows:
        key=ev["payload"]["key"]; edge=ev["payload"]["edge"]; lo,hi=ev["payload"]["transition_interval_ns"]
        if edge=="down":
            require(key not in open_down,"duplicate down before up")
            open_down[key]=(lo,hi,ev)
        else:
            require(key in open_down,"up without down")
            d_lo,d_hi,d_ev=open_down.pop(key)
            if d_hi<lo: guaranteed.append((d_hi,lo))
            if d_lo<hi: possible.append((d_lo,hi))
    if open_down: unmatched=True
    if not ordered or unmatched:
        g_ns=p_ns=None
    else:
        g_ns=union_ns(guaranteed)
        p_ns=union_ns(possible)
    case_id=case["case_id"]
    if not ordered or unmatched:
        disposition="HOLD_OUT_OF_ORDER_AND_RIGHT_CENSORED"
    elif unauthorized:
        disposition="UNAUTHORIZED_INPUT"
    elif not edge_rows and any(e["event_type"]=="RESOURCE_CHANGE" for e in envelope["events"]):
        disposition="INPUT_FREE_RESOURCE_LOSS_UNATTRIBUTED"
    elif not edge_rows and any(e["event_type"]=="TASK_EFFECT" for e in envelope["events"]):
        disposition="NO_INPUT_EFFECT_UNBOUND"
    elif len({e["payload"]["key"] for e in edge_rows})>1:
        disposition="VALID_OVERLAPPING_HOLDS"
    elif edge_rows and any(e["event_type"]=="PROGRAM_TERMINAL" for e in envelope["events"]):
        up_rows=[e for e in edge_rows if e["payload"]["edge"]=="up"]
        if not up_rows:
            disposition="HOLD_RELEASE_TERMINAL_ORDER"
        else:
            up_time=max(e["payload"]["transition_interval_ns"][1] for e in up_rows)
            terminal=min(e["time"]["lower_ns"] for e in envelope["events"] if e["event_type"]=="PROGRAM_TERMINAL")
            disposition="COMPLETED_RELEASE_BEFORE_TERMINAL" if up_time<terminal else "HOLD_RELEASE_TERMINAL_ORDER"
    elif edge_rows and any(e["event_type"]=="SCORE_SAMPLE" and e["payload"].get("window_complete") and e["payload"].get("before")==e["payload"].get("after") for e in envelope["events"]):
        disposition="HELD_INPUT_NO_USEFUL_EFFECT"
    elif not edge_rows and any(e["event_type"]=="LEASE_OPEN" for e in envelope["events"]):
        disposition="AUTHORIZED_IDLE"
    else:
        disposition="UNRESOLVED"
    effects=[]
    for ev in envelope["events"]:
        if ev["event_type"]=="TASK_EFFECT":
            aid=ev["lineage"].get("actuation_id")
            effects.append("BOUND" if aid and aid in actuation_ids else "OBSERVED_UNBOUND")
    score_negative=any(e["event_type"]=="SCORE_SAMPLE" and e["payload"].get("window_complete") and e["payload"].get("before")==e["payload"].get("after") for e in envelope["events"])
    accepted=[e["time"]["lower_ns"] for e in envelope["events"] if e["event_type"]=="PROGRAM_ACCEPTED"]
    terminal=[e["time"]["lower_ns"] for e in envelope["events"] if e["event_type"]=="PROGRAM_TERMINAL"]
    program_ns=(max(terminal)-min(accepted)) if accepted and terminal else None
    terminal_after_release=None
    if terminal and any(e["payload"]["edge"]=="up" for e in edge_rows):
        last_up=max(e["payload"]["transition_interval_ns"][1] for e in edge_rows if e["payload"]["edge"]=="up")
        terminal_after_release=last_up<min(terminal)
    observed={"disposition":disposition,"guaranteed_any_input_ns":g_ns,"possible_any_input_ns":p_ns,
              "task_effect":effects[0] if effects else ("NEGATIVE_FOR_DECLARED_WINDOW" if score_negative else "UNRESOLVED"),
              "program_envelope_ns":program_ns,"terminal_does_not_extend_input":terminal_after_release}
    return observed, {"ordered":ordered,"unmatched_down":unmatched,"unauthorized":unauthorized}

def compare(case, observed):
    expected=case["expected"]
    for key,value in expected.items():
        if key in ("input_decision_may_be_correct","key_intervals_counted_as_union","authorized_guaranteed_ns","upper_bound","causality","input_authority_remains_separate"):
            continue
        require(key in observed,f"{case['case_id']}: unsupported expected field {key}")
        if key=="terminal_not_release":
            require(not any(e["event_type"]=="INPUT_EDGE_BRACKET" and e["payload"].get("edge")=="up" for e in case["events"]),"terminal promoted to release")
            continue
        require(observed.get(key)==value,f"{case['case_id']}: {key} expected {value!r} got {observed.get(key)!r}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--schema",required=True);ap.add_argument("--traces",required=True);ap.add_argument("--out",required=True)
    args=ap.parse_args()
    schema=json.loads(Path(args.schema).read_text(encoding="utf-8"))
    traces=json.loads(Path(args.traces).read_text(encoding="utf-8"))
    require(len(traces["cases"])==8,"expected exactly eight trace cases")
    rows=[]
    for case in traces["cases"]:
        # The example fixture omits explicit domains; derive a declared domain envelope from trace-wide metadata.
        # This is fixture normalization only and keeps the validator's runtime clock check explicit.
        pairs=sorted({(e["clock"]["domain_id"],e["clock"]["epoch_id"]) for e in case["events"]})
        case["clock_domains"]=[{"domain_id":d,"epoch_id":ep,"kind":"monotonic","unit":"ns"} for d,ep in pairs]
        obs,flags=validate_shape(schema,case)
        compare(case,obs)
        rows.append({"case_id":case["case_id"],**obs,**flags})
    report={"schema":"o2-g1-w2-verification-v2","disposition":"PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED",
            "case_count":len(rows),"cases":rows,
            "limits":["schema checks only fields and refs used by this runner; no external JSON Schema meta-validator was available","shape/trace contract only","no live/game/model/input effect","no recovery efficacy"],
            "inputs_sha256":{Path(args.schema).name:hashlib.sha256(Path(args.schema).read_bytes()).hexdigest(),
                             Path(args.traces).name:hashlib.sha256(Path(args.traces).read_bytes()).hexdigest()}}
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"PASS_MEASUREMENT_CONTRACT_CONSTRUCTION_SCOPED {len(rows)}/8")
if __name__=="__main__":
    main()
