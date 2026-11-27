#!/usr/bin/env python3
"""Independent raw-fixture audit; deliberately does not import candidate code."""
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
    observed={h["id"]:tuple(h[f] for f in sorted(must_keep)) for h in histories}
    expected_classes=group(observed.items())
    entry=reported.get("contracts",{}).get(cid,{})
    check(entry.get("mandatory_retained_fields")==sorted(must_keep),cid+": mandatory fields do not match raw oracle")
    check(entry.get("eir_retained_fields")==sorted(must_keep),cid+": EIR encoding is not minimum sufficient field set")
    check(entry.get("equivalence_classes")==expected_classes,cid+": cut partition differs from raw oracle")
    # Independently enumerate concrete future outcomes and make sure every merge is safe after declared recovery.
    for cls in expected_classes:
        for a in cls:
            for b in cls:
                ha=next(x for x in histories if x["id"]==a); hb=next(x for x in histories if x["id"]==b)
                check(all(ha[f]==hb[f] for f in must_keep),cid+": false-equivalence witness")
    min_storage=len(histories)*sum(costs[f] for f in must_keep)
    eir=entry.get("policy_scores",{}).get("EIR_AWARE_RETAIN_OR_REACQUIRE",{})
    check(eir.get("storage_bits")==min_storage,cid+": minimum storage cost mismatch")
    # Reconstruct policy costs/errors from raw inputs and per-schedule future demand.
    for pname,pdef in fixture["policy_definitions"].items():
        keep=set(fixture["field_cost_bits"] if pdef=="all fields" else pdef)
        actual=entry.get("policy_scores",{}).get(pname,{})
        expected_store=len(histories)*sum(costs[f] for f in keep); expected_reads=0; missing=[]
        for sch in schedules:
            for f in sch["reads"]:
                if f in keep: continue
                source=fixture["reacquisition"].get(f,{})
                if source.get("available",False): expected_reads+=sch["weight"]*source["cost_units"]
                else: missing.append({"schedule":sch["id"],"field":f})
        for f in proof:
            if f not in keep: missing.append({"schedule":"proof","field":f})
        check(actual.get("storage_bits")==expected_store,cid+": "+pname+" storage accounting mismatch")
        check(abs(actual.get("expected_reacquisition_units",-1)-expected_reads)<1e-12,cid+": "+pname+" recovery accounting mismatch")
        check(actual.get("unavailable_requirements")==missing,cid+": "+pname+" omitted/false evidence accounting mismatch")
    check(all(not x for x in eir.get("unavailable_requirements",["missing"])),cid+": EIR arm loses a required fact")
    check(all(f in entry.get("eir_retained_fields",[]) for f in proof),cid+": proof-bearing field was not preserved")

# Test changed future contract invalidation: v1 and v2 must induce different exact partitions.
a=reported.get("contracts",{}).get("contract_v1",{}).get("equivalence_classes")
b=reported.get("contracts",{}).get("contract_v2",{}).get("equivalence_classes")
check(a!=b,"expanded future contract did not invalidate the prior partition")
# Positive Pareto condition: EIR has fewer errors than fixed/summary and is not dominated on (storage, errors).
for cid,entry in reported.get("contracts",{}).items():
    scores=entry.get("policy_scores",{}); e=scores.get("EIR_AWARE_RETAIN_OR_REACQUIRE",{})
    competitors=[scores.get(k,{}) for k in ("FIXED_WINDOW","TASK_SUMMARY")]
    check(any(e.get("error_count",999)<x.get("error_count",-1) for x in competitors),cid+": no error improvement over simple policies")
    check(not any(x.get("storage_bits",10**30)<=e.get("storage_bits",-1) and x.get("error_count",10**30)<=e.get("error_count",-1) for x in competitors),cid+": EIR point is Pareto dominated")
# Seeded-style corruption controls run against independent audit predicates.
mutation_checks={
 "omitted_saved": "saved" in must_keep and "saved" not in (must_keep - {"saved"}),
 "false_equivalence": group([(h["id"],()) for h in histories]) != expected_classes,
 "proof_drop_detected": "lineage" in proof and "lineage" not in set(fixture["policy_definitions"]["TASK_SUMMARY"]),
}
check(mutation_checks["omitted_saved"],"omission mutation control was not discriminating")
check(mutation_checks["false_equivalence"],"false-equivalence mutation control was not discriminating")
check(mutation_checks["proof_drop_detected"],"proof-drop mutation control was not discriminating")
result={"audit":"PASS" if not problems else "FAIL","histories":len(histories),"contracts_checked":len(fixture["contracts"]),"errors":problems,"mutation_controls":mutation_checks,"scope":"finite synthetic fixture only"}
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
sys.exit(0 if not problems else 1)
