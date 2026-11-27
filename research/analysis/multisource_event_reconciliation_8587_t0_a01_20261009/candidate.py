#!/usr/bin/env python3
"""Reconcile finite client/toolkit/OS trace projections without forced total order."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path

STAGES=("client","toolkit","os")
EXPECTED={"client":"dispatch","toolkit":"callback","os":"delivery"}
IGNORED={"redraw","independent"}

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def records(case,stage): return [e for e in case["logs"][stage] if e.get("kind") not in IGNORED]
def groups(case,stage):
    result=defaultdict(list)
    for e in records(case,stage): result[e.get("correlation_token")].append(e)
    return result

def partial_order(case):
    edges=[]
    by_token={s:groups(case,s) for s in STAGES}
    for left,right in zip(STAGES,STAGES[1:]):
        for token in sorted(set(by_token[left]) & set(by_token[right])):
            if token is None: continue
            a=by_token[left][token]; b=by_token[right][token]
            if len(a)==len(b)==1:
                edges.append(f"{a[0]['source_id']}->{b[0]['source_id']}")
    actions={a["token"]:set(a.get("depends_on",[])) for a in case["declared_actions"]}
    closure={k:set(v) for k,v in actions.items()}
    changed=True
    while changed:
        changed=False
        for node,parents in closure.items():
            expanded=set(parents)
            for p in tuple(parents): expanded.update(closure.get(p,set()))
            if expanded!=parents: closure[node]=expanded; changed=True
    ordered=[]
    for node,ancestors in closure.items():
        for ancestor in ancestors: ordered.append(f"{ancestor}->{node}")
    unordered=[]
    names=sorted(actions)
    for i,left in enumerate(names):
        for right in names[i+1:]:
            if left not in closure[right] and right not in closure[left]:
                unordered.append(f"{left}|{right}")
    return sorted(edges),sorted(ordered),sorted(unordered)

def classify(case):
    for stage in STAGES:
        coverage=case["coverage"].get(stage)
        if not coverage or not coverage.get("complete"):
            return "UNKNOWN_SOURCE_COVERAGE",None,"coverage_not_complete"
        if coverage.get("frontier_sequence",-1)<0:
            return "UNKNOWN_SOURCE_COVERAGE",None,"invalid_coverage_frontier"
    for stage in STAGES:
        for event in records(case,stage):
            if event.get("correlation_token") is None:
                return "UNKNOWN_CORRELATION",None,"relevant_event_lacks_propagated_token"
            if event.get("kind")!=EXPECTED[stage]:
                return "UNKNOWN_SOURCE_COVERAGE",None,"unmodeled_semantic_event"
    by_stage={s:groups(case,s) for s in STAGES}
    client_counts=Counter(e.get("correlation_token") for e in records(case,"client"))
    duplicate=next((token for token,count in sorted(client_counts.items()) if count>1),None)
    if duplicate is not None:
        return "FAULT","CLIENT",f"duplicate_client_token:{duplicate}"
    for index,stage in enumerate(STAGES[1:],start=1):
        previous=STAGES[index-1]
        current=by_stage[stage]; prior=by_stage[previous]
        duplicate=next((token for token,count in sorted(((k,len(v)) for k,v in current.items())) if count>1),None)
        if duplicate is not None:
            return "FAULT",stage.upper(),f"duplicate_token:{duplicate}"
        for token,events in current.items():
            if token not in prior:
                return "FAULT",stage.upper(),f"unexpected_token:{token}"
        later_tokens=set().union(*(set(by_stage[x]) for x in STAGES[index+1:])) if index+1<len(STAGES) else set()
        for token,prior_events in prior.items():
            current_events=current.get(token,[])
            if not current_events:
                if token in later_tokens:
                    boundary="CLIENT_TO_TOOLKIT" if stage=="toolkit" else "TOOLKIT_TO_OS"
                    return "FAULT",boundary,f"missing_stage:{stage}:{token}"
                if case["coverage"][stage]["complete"]:
                    boundary="CLIENT_TO_TOOLKIT" if stage=="toolkit" else "TOOLKIT_TO_OS"
                    return "FAULT",boundary,f"missing_stage:{stage}:{token}"
                return "UNKNOWN_SOURCE_COVERAGE",None,f"cannot_exclude_missing_stage:{stage}"
            left,right=prior_events[0],current_events[0]
            if left.get("window")!=right.get("window"):
                return "FAULT",stage.upper(),f"window_mismatch:{token}"
            if left.get("generation")!=right.get("generation"):
                return "FAULT",stage.upper(),f"generation_mismatch:{token}"
            if left.get("clock_domain")==right.get("clock_domain"):
                left_interval=left.get("interval_ms",[]); right_interval=right.get("interval_ms",[])
                if len(left_interval)==len(right_interval)==2:
                    if right_interval[0]-left_interval[1]>case["max_delivery_delay_ms"]:
                        return "FAULT",stage.upper(),f"delay_exceeds_bound:{token}"
    return "CONSISTENT",None,"no_identifiable_projection_conflict"

def baselines(case):
    states=list(case["final_state_by_source"].values())
    final_only="NO_SIGNAL" if all(x==states[0] for x in states[1:]) else "STATE_DIVERGENCE"
    client_tokens=[e.get("correlation_token") for e in records(case,"client")]
    client_only="CLIENT_DUPLICATE" if len(client_tokens)!=len(set(client_tokens)) else "NO_SIGNAL"
    return {"FINAL_STATE_ONLY":final_only,"CLIENT_LEDGER_ONLY":client_only}

def reconcile(case):
    classification,boundary,reason=classify(case)
    event_edges,action_edges,unordered=partial_order(case)
    return {"case_id":case["case_id"],"case_input_sha256":digest(case),
            "classification":classification,"boundary":boundary,"reason":reason,
            "event_edges":event_edges,"declared_action_order":action_edges,
            "incomparable_action_pairs":unordered,"baselines":baselines(case)}

def main(argv):
    if len(argv)!=3: raise SystemExit("usage: candidate.py MODEL.json FREEZE.json")
    model=json.loads(Path(argv[1]).read_text()); freeze=json.loads(Path(argv[2]).read_text())
    rows=[reconcile(case) for case in model["cases"]]
    result={"schema":"multisource-event-candidate-v1","allocation_id":freeze["allocation_id"],
            "cases":rows,"summary":{"localized_faults":sum(r["classification"]=="FAULT" for r in rows),
             "unknowns":sum(r["classification"].startswith("UNKNOWN") for r in rows),
             "final_state_only_signals":sum(r["baselines"]["FINAL_STATE_ONLY"]!="NO_SIGNAL" for r in rows),
             "client_only_signals":sum(r["baselines"]["CLIENT_LEDGER_ONLY"]!="NO_SIGNAL" for r in rows)}}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0
if __name__=="__main__": raise SystemExit(main(sys.argv))
