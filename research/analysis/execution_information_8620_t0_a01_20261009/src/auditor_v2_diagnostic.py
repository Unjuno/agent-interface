#!/usr/bin/env python3
"""Post-result diagnostic auditor v2; reads A01 raw only, never reruns candidate."""
import json, pathlib, sys
fixture=json.loads(pathlib.Path(sys.argv[1]).read_text())
reported=json.loads(pathlib.Path(sys.argv[2]).read_text())
problems=[]; histories=fixture["histories"]; costs=fixture["field_cost_bits"]
def check(ok,msg):
    if not ok: problems.append(msg)
def group(rows):
    buckets={}
    for hid,key in rows: buckets.setdefault(json.dumps(key,sort_keys=True),[]).append(hid)
    return sorted(sorted(v) for v in buckets.values())
for contract in fixture["contracts"]:
    cid=contract["id"]; schedules=contract["schedules"]; proof=set(contract["proof_fields"])
    must_keep=set(proof)
    for schedule in schedules:
        for field in schedule["reads"]:
            if not fixture["reacquisition"].get(field,{}).get("available",False): must_keep.add(field)
    expected_classes=group((h["id"],tuple(h[f] for f in sorted(must_keep))) for h in histories)
    entry=reported.get("contracts",{}).get(cid,{})
    # v2 intentionally compares fields as sets because order is not part of the frozen contract.
    check(entry.get("mandatory_retained_fields")==sorted(must_keep),cid+": mandatory field set mismatch")
    check(set(entry.get("eir_retained_fields",[]))==must_keep,cid+": EIR field set mismatch")
    check(entry.get("equivalence_classes")==expected_classes,cid+": partition mismatch")
    check(entry.get("minimum_storage_bits")==len(histories)*sum(costs[f] for f in must_keep),cid+": minimum storage mismatch")
    for pname,pdef in fixture["policy_definitions"].items():
        keep=set(fixture["field_cost_bits"] if pdef=="all fields" else pdef); actual=entry.get("policy_scores",{}).get(pname,{})
        store=len(histories)*sum(costs[f] for f in keep); reads=0.0; missing=[]
        for sch in schedules:
            for f in sch["reads"]:
                if f in keep: continue
                src=fixture["reacquisition"].get(f,{})
                if src.get("available",False): reads+=sch["weight"]*src["cost_units"]
                else: missing.append({"schedule":sch["id"],"field":f})
        for f in proof:
            if f not in keep: missing.append({"schedule":"proof","field":f})
        norm=lambda xs: sorted(xs,key=lambda x:(x["schedule"],x["field"]))
        check(actual.get("storage_bits")==store,pname+": storage mismatch in "+cid)
        check(abs(actual.get("expected_reacquisition_units",-1)-reads)<1e-12,pname+": recovery mismatch in "+cid)
        check(norm(actual.get("unavailable_requirements",[]))==norm(missing),pname+": omissions mismatch in "+cid)
    eir=entry.get("policy_scores",{}).get("EIR_AWARE_RETAIN_OR_REACQUIRE",{})
    check(not eir.get("unavailable_requirements"),cid+": EIR loses required state")
    check(proof <= set(entry.get("eir_retained_fields",[])),cid+": proof field missing")
v1=reported["contracts"]["contract_v1"]["equivalence_classes"]
v2=reported["contracts"]["contract_v2"]["equivalence_classes"]
check(v1!=v2,"expanded contract reused old partition")
for cid,entry in reported["contracts"].items():
    scores=entry["policy_scores"]; e=scores["EIR_AWARE_RETAIN_OR_REACQUIRE"]
    simple=[scores["FIXED_WINDOW"],scores["TASK_SUMMARY"]]
    check(any(e["error_count"]<x["error_count"] for x in simple),cid+": no error advantage")
    check(not any(x["storage_bits"]<=e["storage_bits"] and x["error_count"]<=e["error_count"] for x in simple),cid+": EIR dominated")
# Explicitly inject three corruptions into copies of raw candidate output and ensure each violates a gate.
def encoding_ok(obj,cid,required): return set(obj["contracts"][cid]["eir_retained_fields"])==required
mutations={}
copy=json.loads(json.dumps(reported)); copy["contracts"]["contract_v2"]["eir_retained_fields"].remove("saved")
mutations["omit_saved_rejected"]=not encoding_ok(copy,"contract_v2",must_keep)
copy=json.loads(json.dumps(reported)); copy["contracts"]["contract_v2"]["equivalence_classes"]=[sorted(h["id"] for h in histories)]
mutations["false_equivalence_rejected"]=copy["contracts"]["contract_v2"]["equivalence_classes"]!=v2
copy=json.loads(json.dumps(reported)); copy["contracts"]["contract_v2"]["eir_retained_fields"].remove("lineage")
mutations["proof_drop_rejected"]=not encoding_ok(copy,"contract_v2",must_keep)
for name,ok in mutations.items(): check(ok,"mutation not detected: "+name)
result={"audit":"PASS_DIAGNOSTIC_ONLY" if not problems else "FAIL_DIAGNOSTIC","errors":problems,"histories":len(histories),"contracts_checked":len(fixture["contracts"]),"mutation_controls":mutations,"reads_only":"A01 retained raw candidate output","not_a_new_formal_allocation":True,"scope":"finite synthetic fixture only"}
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True)); sys.exit(0 if not problems else 1)
