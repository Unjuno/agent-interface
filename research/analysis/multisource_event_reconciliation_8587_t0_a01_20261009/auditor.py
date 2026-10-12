#!/usr/bin/env python3
"""Independent audit of raw source projections and candidate reconciliation."""
from __future__ import annotations
import copy,hashlib,json,sys
from collections import defaultdict
from pathlib import Path

STAGES=("client","toolkit","os")
KINDS={"client":"dispatch","toolkit":"callback","os":"delivery"}

def encoded(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def sha(v): return hashlib.sha256(encoded(v)).hexdigest()
def semantic(case,stage):
    return [r for r in case["logs"][stage] if r.get("kind") not in {"redraw","independent"}]
def by_token(case,stage):
    result={}
    for record in semantic(case,stage):
        result.setdefault(record.get("correlation_token"),[]).append(record)
    return result

def oracle_classification(case):
    for source in STAGES:
        evidence=case.get("coverage",{}).get(source)
        if evidence is None or evidence.get("complete") is not True or evidence.get("frontier_sequence",-1)<0:
            return "UNKNOWN_SOURCE_COVERAGE",None,"coverage_not_complete"
    for source in STAGES:
        for record in semantic(case,source):
            if not record.get("correlation_token"):
                return "UNKNOWN_CORRELATION",None,"relevant_event_lacks_propagated_token"
            if record.get("kind")!=KINDS[source]:
                return "UNKNOWN_SOURCE_COVERAGE",None,"unmodeled_semantic_event"
    index=by_token(case,"client")
    repeated=next((tag for tag,items in sorted(index.items()) if len(items)>1),None)
    if repeated is not None:
        return "FAULT","CLIENT",f"duplicate_client_token:{repeated}"
    for earlier,later in (("client","toolkit"),("toolkit","os")):
        before=by_token(case,earlier); after=by_token(case,later)
        repeated=next((tag for tag,items in sorted(after.items()) if len(items)>1),None)
        if repeated is not None:
            return "FAULT",later.upper(),f"duplicate_token:{repeated}"
        for tag in after:
            if tag not in before:
                return "FAULT",later.upper(),f"unexpected_token:{tag}"
        for tag,prior in before.items():
            following=after.get(tag,[])
            if not following:
                first_missing="CLIENT_TO_TOOLKIT" if later=="toolkit" else "TOOLKIT_TO_OS"
                return "FAULT",first_missing,f"missing_stage:{later}:{tag}"
            a,b=prior[0],following[0]
            if a.get("window")!=b.get("window"):
                return "FAULT",later.upper(),f"window_mismatch:{tag}"
            if a.get("generation")!=b.get("generation"):
                return "FAULT",later.upper(),f"generation_mismatch:{tag}"
            if a.get("clock_domain")==b.get("clock_domain"):
                ta,tb=a.get("interval_ms",[]),b.get("interval_ms",[])
                if len(ta)==len(tb)==2 and tb[0]-ta[1]>case["max_delivery_delay_ms"]:
                    return "FAULT",later.upper(),f"delay_exceeds_bound:{tag}"
    return "CONSISTENT",None,"no_identifiable_projection_conflict"

def independently_ordered_actions(case):
    tokens={a["token"]:set(a.get("depends_on",[])) for a in case["declared_actions"]}
    def ancestors(node,seen=None):
        seen=set() if seen is None else seen
        for parent in tokens.get(node,set()):
            if parent not in seen:
                seen.add(parent); ancestors(parent,seen)
        return seen
    reach={n:ancestors(n) for n in tokens}
    ordered=sorted(f"{parent}->{node}" for node,parents in reach.items() for parent in parents)
    labels=sorted(tokens); incomparable=[]
    for i,x in enumerate(labels):
        for y in labels[i+1:]:
            if y not in reach[x] and x not in reach[y]: incomparable.append(f"{x}|{y}")
    return ordered,incomparable

def event_links(case):
    result=[]
    for left,right in (("client","toolkit"),("toolkit","os")):
        a=by_token(case,left); b=by_token(case,right)
        for tag in set(a)&set(b):
            if tag is not None and len(a[tag])==len(b[tag])==1:
                result.append(f"{a[tag][0]['source_id']}->{b[tag][0]['source_id']}")
    return sorted(result)

def baseline_signals(case):
    states=list(case["final_state_by_source"].values())
    final="NO_SIGNAL" if all(value==states[0] for value in states[1:]) else "STATE_DIVERGENCE"
    client=[r.get("correlation_token") for r in semantic(case,"client")]
    ledger="CLIENT_DUPLICATE" if len(client)!=len(set(client)) else "NO_SIGNAL"
    return {"FINAL_STATE_ONLY":final,"CLIENT_LEDGER_ONLY":ledger}

def expected_row(case):
    cls,boundary,reason=oracle_classification(case)
    ordered,incomparable=independently_ordered_actions(case)
    return {"case_id":case["case_id"],"case_input_sha256":sha(case),"classification":cls,
            "boundary":boundary,"reason":reason,"event_edges":event_links(case),
            "declared_action_order":ordered,"incomparable_action_pairs":incomparable,
            "baselines":baseline_signals(case)}

def audit_rows(model,oracle,raw,allocation_id):
    errors=[]
    expected_oracle={r["case_id"]:r for r in oracle["cases"]}
    if raw.get("schema")!="multisource-event-candidate-v1": errors.append("candidate-schema")
    if raw.get("allocation_id")!=allocation_id: errors.append("allocation-id")
    if set(raw)!={"schema","allocation_id","cases","summary"}: errors.append("candidate-shape")
    rows=raw.get("cases",[])
    if [r.get("case_id") for r in rows]!=[c["case_id"] for c in model["cases"]]: errors.append("case-order-membership")
    localized=0; client_signals=0; final_signals=0; unknown=0; false_benign=[]
    for case,row in zip(model["cases"],rows):
        expected=expected_row(case)
        for key,value in expected.items():
            if row.get(key)!=value: errors.append(f"{case['case_id']}:{key}")
        hidden=expected_oracle.get(case["case_id"])
        if hidden is None: errors.append(f"{case['case_id']}:oracle-row-missing"); continue
        if (expected["classification"],expected["boundary"])!=(hidden["expected_classification"],hidden["expected_boundary"]):
            errors.append(f"{case['case_id']}:fixture-oracle-disagreement")
        if expected["classification"]=="FAULT" and expected["boundary"]==hidden["expected_boundary"]:
            localized+=1
        if expected["classification"].startswith("UNKNOWN"): unknown+=1
        if hidden["benign"] and expected["classification"]=="FAULT": false_benign.append(case["case_id"])
        if expected["baselines"]["CLIENT_LEDGER_ONLY"]!="NO_SIGNAL": client_signals+=1
        if expected["baselines"]["FINAL_STATE_ONLY"]!="NO_SIGNAL": final_signals+=1
    summary=raw.get("summary",{})
    expected_summary={"localized_faults":sum(x["expected_classification"]=="FAULT" for x in oracle["cases"]),
                      "unknowns":sum(x["expected_classification"].startswith("UNKNOWN") for x in oracle["cases"]),
                      "final_state_only_signals":final_signals,"client_only_signals":client_signals}
    if summary!=expected_summary: errors.append("summary-mismatch")
    faults=sum(x["expected_classification"]=="FAULT" for x in oracle["cases"])
    if localized!=faults: errors.append("not-all-identifiable-seeded-faults-localized")
    if false_benign: errors.append("false-benign-localizations")
    if not (localized>final_signals and localized>client_signals): errors.append("no-improvement-over-weak-comparators")
    return errors

def verify_files(model_path,oracle_path,freeze):
    errors=[]
    for key,path in (("model.json",model_path),("oracle.json",oracle_path)):
        expected=freeze.get("input_sha256",{}).get(key)
        actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if actual!=expected: errors.append("frozen-input-hash:"+key)
    for name,expected in freeze.get("source_sha256",{}).items():
        path=Path(name)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            errors.append("frozen-source-hash:"+name)
    return errors

def main(argv):
    if len(argv)!=5: raise SystemExit("usage: auditor.py MODEL.json ORACLE.json FREEZE.json CANDIDATE.json")
    model_path,oracle_path,freeze_path,candidate_path=argv[1:]
    model=json.loads(Path(model_path).read_text()); oracle=json.loads(Path(oracle_path).read_text())
    freeze=json.loads(Path(freeze_path).read_text()); raw=json.loads(Path(candidate_path).read_text())
    errors=verify_files(model_path,oracle_path,freeze)+audit_rows(model,oracle,raw,freeze["allocation_id"])
    mutations=[]
    if not errors:
        probes=[]
        altered=copy.deepcopy(model)
        clean=next(c for c in altered["cases"] if c["case_id"]=="clean")
        clean["logs"]["toolkit"].clear(); probes.append((altered,raw))
        altered=copy.deepcopy(model)
        concurrent=next(c for c in altered["cases"] if c["case_id"]=="concurrent_reorder")
        concurrent["logs"]["toolkit"][0]["correlation_token"]="a1"; probes.append((altered,raw))
        altered=copy.deepcopy(model)
        clean=next(c for c in altered["cases"] if c["case_id"]=="clean")
        clean["coverage"]["os"]["complete"]=False; probes.append((altered,raw))
        altered_raw=copy.deepcopy(raw)
        altered_raw["cases"][0]["event_edges"].append("C1->O1"); probes.append((model,altered_raw))
        altered_raw=copy.deepcopy(raw)
        benign=next(r for r in altered_raw["cases"] if r["case_id"]=="benign_coalescing")
        benign["classification"]="FAULT"; benign["boundary"]="TOOLKIT"; probes.append((model,altered_raw))
        for changed_model,changed_raw in probes:
            rejected=bool(audit_rows(changed_model,oracle,changed_raw,freeze["allocation_id"]))
            mutations.append(rejected)
    result={"status":"PASS_METHOD_SCOPED" if not errors and len(mutations)==5 and all(mutations) else "FAIL_AUDIT",
            "cases_audited":len(model["cases"]),"faults_localized":sum(c["expected_classification"]=="FAULT" for c in oracle["cases"]),
            "unknown_cases":sum(c["expected_classification"].startswith("UNKNOWN") for c in oracle["cases"]),
            "client_only_signals":sum(x["baselines"]["CLIENT_LEDGER_ONLY"]!="NO_SIGNAL" for x in raw["cases"]),
            "final_state_only_signals":sum(x["baselines"]["FINAL_STATE_ONLY"]!="NO_SIGNAL" for x in raw["cases"]),
            "false_localizations_on_benign":sum(o["benign"] and r["classification"]=="FAULT" for o,r in zip(oracle["cases"],raw["cases"])),
            "errors":errors,"mutation_controls_rejected":sum(mutations),"mutation_controls_total":len(mutations),
            "mutation_results":mutations}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0 if result["status"]=="PASS_METHOD_SCOPED" else 1

if __name__=="__main__": raise SystemExit(main(sys.argv))
