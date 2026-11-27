#!/usr/bin/env python3
"""Finite controlled-feedback × raw-artifact-access simulator for Issue #8581."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def outcomes(spec,seed):
    dev=[]; fresh=[]
    for j in range(spec["dev_opportunities_per_seed"]):
        dev.append({"case_id":f"dev-{seed}-{j}","stable":int((j+seed)%10<spec["stable_dev_correct_per_seed"]),"memorizer":int(True),"unsafe":int(True),"unsafe_veto":int(j==0)})
    for j in range(spec["fresh_opportunities_per_seed"]):
        fresh.append({"case_id":f"fresh-{seed}-{j}","stable":int((j+2*seed)%10<spec["stable_fresh_correct_per_seed"]),"memorizer":int((j+3*seed)%10<spec["memorizer_fresh_correct_per_seed"]),"unsafe":int(True),"unsafe_veto":0})
    return dev,fresh

def score(rows,candidate): return sum(r[candidate] for r in rows)/len(rows)

def build(spec):
    trials=[]; oracle=[]
    for seed in spec["seeds"]:
        dev,fresh=outcomes(spec,seed)
        canary=f"{spec['artifact_graph']['development_store']['canary_prefix']}-{seed:02d}"
        raw_payload={"artifact_id":spec["artifact_graph"]["development_store"]["id"],"seed":seed,"canary":canary,"rows":dev}
        raw_bytes=json.dumps(raw_payload,sort_keys=True,separators=(",",":")).encode()
        for feedback in spec["feedback_modes"]:
            for access in spec["artifact_access_modes"]:
                cell=f"{feedback}+{access}"
                doc={"call_id":f"doc-{seed}-{cell}","actor":spec["artifact_graph"]["candidate_author"],"route":"task-documentation","artifact_id":spec["artifact_graph"]["benign_document"]["id"],"status":"RETURNED","content":spec["artifact_graph"]["benign_document"]["content"],"sha256":spec["artifact_graph"]["benign_document"]["sha256"]}
                raw_access={"call_id":f"raw-{seed}-{cell}" if access=="RAW_BYPASS" or feedback=="CONTROLLED" else None,"actor":spec["artifact_graph"]["candidate_author"],"route":"issue-cache-compat","artifact_id":spec["artifact_graph"]["development_store"]["id"],"attempted":access=="RAW_BYPASS" or feedback=="CONTROLLED"}
                if access=="RAW_BYPASS":
                    raw_access.update({"status":"RETURNED","sha256":hashlib.sha256(raw_bytes).hexdigest(),"returned_object":raw_payload})
                elif feedback=="CONTROLLED":
                    raw_access.update({"status":"DENIED","reason":"DENY_PRELOCK","returned_object":None})
                else:
                    raw_access.update({"status":"NO_ATTEMPT","returned_object":None})
                if feedback=="FULL":
                    broker={"kind":"FULL_PER_CASE","dev_rows":dev}
                else:
                    broker={"kind":"COARSE_ONLY","signals":{"stable":spec["coarse_signal"],"memorizer":spec["coarse_signal"],"unsafe":"SAFETY_VETOED"}}
                safety=spec["hard_safety_veto"].copy(); safety["case_id"]=safety["case_id"].format(seed=seed)
                # Exact noncompensable event is a separate, immediate channel in every factorial cell.
                if broker["kind"]=="FULL_PER_CASE":
                    source=broker["dev_rows"]
                    eligible=[c for c in ("stable","memorizer") if c in spec["candidates"]]
                    selected=max(eligible,key=lambda c:(score(source,c),-spec["candidates"][c]["complexity"]))
                    selection_input="BROKER_PER_CASE"
                elif raw_access["status"]=="RETURNED":
                    source=raw_access["returned_object"]["rows"]
                    eligible=[c for c in ("stable","memorizer") if c in spec["candidates"]]
                    selected=max(eligible,key=lambda c:(score(source,c),-spec["candidates"][c]["complexity"]))
                    selection_input="RAW_BYPASS_PER_CASE"
                else:
                    eligible=[c for c,sig in broker["signals"].items() if sig==spec["coarse_signal"]]
                    selected=min(eligible,key=lambda c:spec["candidates"][c]["complexity"])
                    selection_input="COARSE_SIGNAL_COMPLEXITY_TIEBREAK"
                fresh_probe={"call_id":f"fresh-probe-{seed}-{cell}","attempted":True,"actor":"independent_access_control_probe","status":"DENIED","reason":"DENY_PRELOCK","returned_object":None}
                trials.append({"seed":seed,"cell":cell,"feedback_mode":feedback,"artifact_access_mode":access,"task_document_access":doc,"raw_access":raw_access,"broker_return":broker,"fresh_prelock_probe":fresh_probe,"immediate_safety_disclosure":safety,"candidate_update":{"selected_candidate":selected,"selection_input":selection_input,"prelock_visible_artifact_ids":[doc["artifact_id"]]+([raw_access["artifact_id"]] if raw_access["status"]=="RETURNED" else []),"fresh_visible":False}})
                oracle.append({"seed":seed,"cell":cell,"dev_rows":dev,"fresh_rows":fresh,"postlock_publication":{"artifact_id":spec["artifact_graph"]["fresh_store"]["id"],"status":"PUBLISHED_AFTER_LOCK"},"dev_scores":{"stable":score(dev,"stable"),"memorizer":score(dev,"memorizer")},"fresh_scores":{"stable":score(fresh,"stable"),"memorizer":score(fresh,"memorizer")}})
    controls={"unmonitored_route":{"route":spec["artifact_graph"]["unmonitored_route"],"attempted":True,"monitor_status":"UNREGISTERED","disposition":spec["diagnostic_controls"]["unmonitored_route_disposition"]},"no_attempt":{"route":"issue-cache-compat","attempted":False,"monitor_status":"REGISTERED","disposition":spec["diagnostic_controls"]["no_attempt_disposition"]},"post_lock_publication":{"artifact_id":spec["artifact_graph"]["fresh_store"]["id"],"lock_state":"LOCKED","status":spec["diagnostic_controls"]["post_lock_publication_disposition"]},"benign_document":{"artifact_id":spec["artifact_graph"]["benign_document"]["id"],"status":spec["diagnostic_controls"]["benign_document_disposition"]}}
    return {"schema":"issue-8581-candidate-raw-v1","allocation":spec["allocation"],"trials":trials,"audit_only_oracle":oracle,"access_audit_controls":controls,"authority":"NONE"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--output",default=str(ROOT/"results/candidate.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    raw=build(json.loads(Path(a.spec).read_text())); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps({"allocation":raw["allocation"],"trials":len(raw["trials"]),"oracle_rows":len(raw["audit_only_oracle"]),"output":str(out)},sort_keys=True))
if __name__=="__main__": main()
