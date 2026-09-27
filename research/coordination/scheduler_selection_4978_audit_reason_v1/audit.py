#!/usr/bin/env python3
"""Independent reference audit for the scheduler-selection raw rows."""
import copy, hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
POLICIES=("FIFO_HEAD","STABLE_LIST","ELIGIBLE_HEAP")

def sha(b): return hashlib.sha256(b).hexdigest()
def key(op): return (-op["priority"],op["deadline"],op["seq"],op["id"])
def blocked(op,tick,done,locks):
    if op["release"]>tick:return "not_released"
    if op["ready_at"]>tick:return "not_before"
    if any(d not in done for d in op["deps"]):return "dependency"
    if op["resource"] is not None and locks.get(op["resource"],-1)>tick:return "resource"
    return None

def reference_trace(spec,fixture,policy):
    ops={o["id"]:dict(o,state="pending") for o in spec["operations"]}
    done=set(); events={}
    for e in spec.get("events",[]):events.setdefault(e["tick"],[]).append(e)
    trace=[]; horizon=spec.get("horizon",fixture["horizon"])
    for tick in range(horizon):
        for o in ops.values():
            if o["state"]=="pending" and o["release"]<=tick:o["state"]="waiting"
            if o["state"]=="waiting" and o["deadline"]<tick:o["state"]="expired"
        for e in events.get(tick,[]):
            o=ops[e["id"]]
            if o["state"]!="waiting":continue
            if e["kind"]=="cancel":o["state"]="cancelled"
            elif e["kind"]=="reprioritize":o["priority"]=e["priority"]
        eligible=[o for o in ops.values() if o["state"]=="waiting" and o["deadline"]>=tick and blocked(o,tick,done,fixture["locks_until"]) is None]
        selected=None;reason="no_eligible_candidate"
        if policy=="FIFO_HEAD":
            waiting=sorted((o for o in ops.values() if o["state"]=="waiting"),key=lambda o:(o["seq"],o["id"]))
            if waiting:
                head=waiting[0]
                reason=blocked(head,tick,done,fixture["locks_until"]) or "fifo_head"
                if head in eligible:selected=head
        elif eligible:
            selected=min(eligible,key=key);reason="priority_deadline_stable_seq"
        avoidable=selected is None and bool(eligible)
        trace.append({"tick":tick,"selected":selected["id"] if selected else None,"reason":reason,"eligible_while_idle":avoidable})
        if selected:
            if any(d not in done for d in selected["deps"]):return None
            if selected["resource"] is not None and fixture["locks_until"].get(selected["resource"],-1)>tick:return None
            selected["state"]="completed";selected["completed_tick"]=tick;done.add(selected["id"])
    states={k:{"state":v["state"],"completed_tick":v.get("completed_tick"),"priority":v["priority"],"seq":v["seq"]} for k,v in ops.items()}
    return trace,states

def audit_doc(raw,fixture,freeze):
    errors=[]
    if raw.get("schema")!="scheduler-selection-raw-v1":errors.append("schema")
    if raw.get("issue")!=2868 or raw.get("allocation") not in (freeze["predecessor_allocation"],freeze["allocation"]):errors.append("identity")
    allocation=raw.get("allocation")
    if allocation==freeze["predecessor_allocation"]:expected_sources=freeze["predecessor_source_sha256"]
    elif allocation==freeze["allocation"]:expected_sources=freeze["source_sha256"]
    else:expected_sources=None
    if expected_sources is None or raw.get("source_sha256")!=expected_sources:errors.append("source_hash_manifest")
    if raw.get("fixture_sha256")!=sha((ROOT/"scenarios.json").read_bytes()):errors.append("fixture_hash")
    rows=raw.get("rows")
    if not isinstance(rows,list) or len(rows)!=48 or raw.get("worker_processes")!=48:errors.append("row_inventory")
    if not isinstance(rows,list):return errors or ["rows_type"]
    index={(r.get("scenario"),r.get("policy"),r.get("repeat")):r for r in rows if isinstance(r,dict)}
    expected={(s["id"],p,n) for s in fixture["scenarios"] for p in POLICIES for n in (0,1)}
    if set(index)!=expected:errors.append("row_keys")
    for scenario in fixture["scenarios"]:
        sid=scenario["id"]
        for policy in POLICIES:
            pair=[index.get((sid,policy,n)) for n in (0,1)]
            if None in pair:continue
            def stable_projection(row):return {k:row[k] for k in ("trace","states","idle_ticks","avoidable_idle_ticks")}
            if stable_projection(pair[0])!=stable_projection(pair[1]):errors.append("repeat_determinism:"+sid+":"+policy)
            expected_trace=reference_trace(scenario,fixture,policy)
            if expected_trace is None or pair[0].get("trace")!=expected_trace[0]:errors.append("reference_trace:"+sid+":"+policy)
            else:
                projection={k:{kk:v[kk] for kk in ("state","completed_tick","priority","seq")} for k,v in pair[0].get("states",{}).items()}
                if projection!=expected_trace[1]:errors.append("reference_states:"+sid+":"+policy)
            if pair[0].get("worker_exit_code")!=0 or len(pair[0].get("trace",[]))!=scenario.get("horizon",fixture["horizon"]):errors.append("worker_receipt:"+sid+":"+policy)
        l=index.get((sid,"STABLE_LIST",0));h=index.get((sid,"ELIGIBLE_HEAP",0))
        if l and h and any(l[k]!=h[k] for k in ("trace","states","idle_ticks","avoidable_idle_ticks")):
            errors.append("list_heap_semantics:"+sid)
    for r in rows:
        if not isinstance(r,dict):continue
        for step in r.get("trace",[]):
            if step.get("selected") is not None and step.get("eligible_while_idle") is not False:errors.append("selection_receipt")
        if r.get("scenario")=="reprioritize_versioned_entry" and r.get("policy")=="ELIGIBLE_HEAP" and r.get("stale_heap_entries_discarded",0)<1:errors.append("stale_reprioritize")
        if r.get("scenario")=="cancel_versioned_entry" and r.get("policy")=="ELIGIBLE_HEAP" and r.get("stale_heap_entries_discarded",0)<1:errors.append("stale_cancel")
    for sid in ("independent_blocked_head","external_resource_lock"):
        f=index.get((sid,"FIFO_HEAD",0));l=index.get((sid,"STABLE_LIST",0));h=index.get((sid,"ELIGIBLE_HEAP",0))
        if not f or not l or not h:continue
        if f.get("avoidable_idle_ticks",0)<1 or l.get("avoidable_idle_ticks",0)!=0 or h.get("avoidable_idle_ticks",0)!=0:errors.append("head_of_line_control:"+sid)
    eq=index.get(("equal_priority_stability","STABLE_LIST",0))
    if eq and [x["selected"] for x in eq["trace"] if x["selected"]] != ["A","B","C"]:errors.append("stable_tie_order")
    for policy in ("STABLE_LIST","ELIGIBLE_HEAP"):
        starve=index.get(("high_priority_starvation",policy,0))
        if starve and starve.get("states",{}).get("LOW",{}).get("state")!="waiting":errors.append("starvation_witness_hidden:"+policy)
    fifo_starve=index.get(("high_priority_starvation","FIFO_HEAD",0))
    if fifo_starve and fifo_starve.get("states",{}).get("LOW",{}).get("state")!="completed":errors.append("fifo_service_control")
    return errors

def corruption_controls(raw,fixture,freeze):
    controls={}
    mutants={}
    m=copy.deepcopy(raw);m["rows"].pop();mutants["row_drop"]=m
    m=copy.deepcopy(raw);m["rows"].append(copy.deepcopy(m["rows"][0]));mutants["duplicate_row"]=m
    m=copy.deepcopy(raw);m["source_sha256"]["runner.py"]="0"*64;mutants["source_hash"]=m
    m=copy.deepcopy(raw);m["worker_processes"]=47;mutants["denominator"]=m
    m=copy.deepcopy(raw);m["rows"][0]["trace"][0]["selected"]="unknown";mutants["unknown_selection"]=m
    m=copy.deepcopy(raw);m["rows"][0]["worker_exit_code"]=1;mutants["worker_exit"]=m
    m=copy.deepcopy(raw);m["rows"][0]["scenario"]="forged";mutants["scenario_identity"]=m
    m=copy.deepcopy(raw);m["rows"][0]["repeat"]=99;mutants["repeat_identity"]=m
    m=copy.deepcopy(raw);m["rows"][0]["trace"][0]["eligible_while_idle"]=not bool(m["rows"][0]["trace"][0]["eligible_while_idle"]);mutants["idle_receipt"]=m
    m=copy.deepcopy(raw);m["rows"][0]["states"].pop(next(iter(m["rows"][0]["states"])));mutants["state_omission"]=m
    for name,doc in mutants.items():controls[name]=bool(audit_doc(doc,fixture,freeze))
    return controls

def main():
    raw_path=Path(sys.argv[1]);out=Path(sys.argv[2]);freeze=json.loads((ROOT/"FREEZE.json").read_text());fixture=json.loads((ROOT/"scenarios.json").read_text())
    raw_bytes=raw_path.read_bytes();raw=json.loads(raw_bytes);errors=audit_doc(raw,fixture,freeze);controls=corruption_controls(raw,fixture,freeze)
    rejected=sum(controls.values());decision="PASS_SCHEDULER_SELECTION_SEMANTICS_SCOPED" if not errors and rejected==10 else "HOLD_OR_FAIL_SCHEDULER_SELECTION"
    report={"schema":"scheduler-selection-audit-v1","decision":decision,"errors":errors,"rows":len(raw.get("rows",[])),"worker_processes":raw.get("worker_processes"),"corruption_controls":controls,"corruption_controls_rejected":rejected,"raw_sha256":sha(raw_bytes)}
    data=(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n").encode();out.mkdir(parents=True,exist_ok=True);(out/"audit.json").write_bytes(data);(out/"audit.sha256").write_text(sha(data)+"  audit.json\n",encoding="ascii");print(data.decode(),end="")
    raise SystemExit(0 if decision.startswith("PASS_") else 1)
if __name__=="__main__":main()
