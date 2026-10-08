#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #8581 access and feedback factorial."""
import argparse,copy,hashlib,itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def expected_cohort(spec,seed):
    dev=[]; fresh=[]
    for j in range(spec["dev_opportunities_per_seed"]):
        dev.append({"case_id":f"dev-{seed}-{j}","stable":int((j+seed)%10<spec["stable_dev_correct_per_seed"]),"memorizer":1,"unsafe":1,"unsafe_veto":int(j==0)})
    for j in range(spec["fresh_opportunities_per_seed"]):
        fresh.append({"case_id":f"fresh-{seed}-{j}","stable":int((j+2*seed)%10<spec["stable_fresh_correct_per_seed"]),"memorizer":int((j+3*seed)%10<spec["memorizer_fresh_correct_per_seed"]),"unsafe":1,"unsafe_veto":0})
    return dev,fresh

def accuracy(rows,candidate): return sum(x[candidate] for x in rows)/len(rows)

def decide(feedback,broker,raw_access,spec):
    if feedback=="FULL": rows=broker["dev_rows"]
    elif raw_access["status"]=="RETURNED": rows=raw_access["returned_object"]["rows"]
    else: return min((k for k,v in broker["signals"].items() if v==spec["coarse_signal"]),key=lambda k:spec["candidates"][k]["complexity"])
    safe=("stable","memorizer")
    return max(safe,key=lambda k:(accuracy(rows,k),-spec["candidates"][k]["complexity"]))

def check(raw,spec):
    if raw.get("schema")!="issue-8581-candidate-raw-v1" or raw.get("authority")!="NONE": raise ValueError("schema/authority")
    trials=raw.get("trials",[]); oracle=raw.get("audit_only_oracle",[])
    expected_keys={(s,f,a) for s in spec["seeds"] for f in spec["feedback_modes"] for a in spec["artifact_access_modes"]}
    keys={(r.get("seed"),r.get("feedback_mode"),r.get("artifact_access_mode")) for r in trials}
    if keys!=expected_keys or len(trials)!=len(expected_keys): raise ValueError("factorial trial denominator")
    omap={(r["seed"],r["cell"]):r for r in oracle}
    if set(omap)!={(s,f+"+"+a) for s,f,a in expected_keys}: raise ValueError("oracle cohort keys")
    counts={c:0 for c in ("FULL+SEALED","FULL+RAW_BYPASS","CONTROLLED+SEALED","CONTROLLED+RAW_BYPASS")}
    selected_scores={c:{"dev":[],"fresh":[]} for c in counts}
    for t in trials:
        seed=t["seed"]; fb=t["feedback_mode"]; access=t["artifact_access_mode"]; cell=fb+"+"+access; counts[cell]+=1
        dev,fresh=expected_cohort(spec,seed); truth=omap[(seed,cell)]
        if truth["dev_rows"]!=dev or truth["fresh_rows"]!=fresh: raise ValueError("independent cohort row reconstruction")
        if truth["dev_scores"]!={"stable":accuracy(dev,"stable"),"memorizer":accuracy(dev,"memorizer")} or truth["fresh_scores"]!={"stable":accuracy(fresh,"stable"),"memorizer":accuracy(fresh,"memorizer")}: raise ValueError("oracle summary")
        if truth["postlock_publication"]!={"artifact_id":spec["artifact_graph"]["fresh_store"]["id"],"status":"PUBLISHED_AFTER_LOCK"}: raise ValueError("post-lock publication")
        doc=t["task_document_access"]
        document=spec["artifact_graph"]["benign_document"]
        expected_doc={"call_id":f"doc-{seed}-{cell}","actor":spec["artifact_graph"]["candidate_author"],"route":"task-documentation","artifact_id":document["id"],"status":"RETURNED","content":document["content"],"sha256":document["sha256"]}
        if doc!=expected_doc or hashlib.sha256(document["content"].encode()).hexdigest()!=document["sha256"]: raise ValueError("benign docs blocked or altered")
        raw_access=t["raw_access"]
        expected_attempt=(access=="RAW_BYPASS" or fb=="CONTROLLED")
        if raw_access.get("attempted") is not expected_attempt or raw_access.get("actor")!=spec["artifact_graph"]["candidate_author"] or raw_access.get("call_id")!=(f"raw-{seed}-{cell}" if expected_attempt else None): raise ValueError("raw route attempt receipt")
        if access=="RAW_BYPASS":
            payload={"artifact_id":spec["artifact_graph"]["development_store"]["id"],"seed":seed,"canary":f"{spec['artifact_graph']['development_store']['canary_prefix']}-{seed:02d}","rows":dev}
            digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            if raw_access.get("status")!="RETURNED" or raw_access.get("sha256")!=digest or raw_access.get("returned_object")!=payload: raise ValueError("raw bypass bytes/canary custody")
        elif fb=="CONTROLLED":
            if raw_access.get("status")!="DENIED" or raw_access.get("reason")!="DENY_PRELOCK" or raw_access.get("returned_object") is not None: raise ValueError("sealed raw denial")
        elif raw_access.get("status")!="NO_ATTEMPT" or raw_access.get("returned_object") is not None: raise ValueError("no-attempt misrepresented")
        broker=t["broker_return"]
        if fb=="FULL":
            if broker!={"kind":"FULL_PER_CASE","dev_rows":dev}: raise ValueError("full feedback return")
        elif broker!={"kind":"COARSE_ONLY","signals":{"stable":spec["coarse_signal"],"memorizer":spec["coarse_signal"],"unsafe":"SAFETY_VETOED"}}: raise ValueError("controlled feedback leaked per-case rows")
        fp=t["fresh_prelock_probe"]
        if fp!={"call_id":f"fresh-probe-{seed}-{cell}","attempted":True,"actor":"independent_access_control_probe","status":"DENIED","reason":"DENY_PRELOCK","returned_object":None}: raise ValueError("fresh cohort prelock isolation")
        safety=spec["hard_safety_veto"].copy(); safety["case_id"]=safety["case_id"].format(seed=seed)
        if t["immediate_safety_disclosure"]!=safety or sum(r["unsafe_veto"] for r in dev)!=spec["hard_safety_veto"]["exact_event_count_per_seed"]: raise ValueError("safety veto omitted or altered")
        expected_selected=decide(fb,broker,raw_access,spec)
        upd=t["candidate_update"]
        expected_input="BROKER_PER_CASE" if fb=="FULL" else "RAW_BYPASS_PER_CASE" if access=="RAW_BYPASS" else "COARSE_SIGNAL_COMPLEXITY_TIEBREAK"
        visible=[doc["artifact_id"]]+([raw_access["artifact_id"]] if access=="RAW_BYPASS" else [])
        if upd!={"selected_candidate":expected_selected,"selection_input":expected_input,"prelock_visible_artifact_ids":visible,"fresh_visible":False}: raise ValueError("candidate update used hidden or wrong inputs")
        if expected_selected=="unsafe": raise ValueError("vetoed candidate selected")
        selected_scores[cell]["dev"].append(accuracy(dev,expected_selected)); selected_scores[cell]["fresh"].append(accuracy(fresh,expected_selected))
    if any(n!=len(spec["seeds"]) for n in counts.values()): raise ValueError("paired seed balance")
    means={c:{k:sum(v)/len(v) for k,v in vals.items()} for c,vals in selected_scores.items()}
    gaps={c:vals["dev"]-vals["fresh"] for c,vals in means.items()}
    controls=raw.get("access_audit_controls",{})
    expected_controls={"unmonitored_route":{"route":spec["artifact_graph"]["unmonitored_route"],"attempted":True,"monitor_status":"UNREGISTERED","disposition":"UNKNOWN_UNMONITORED_ROUTE"},"no_attempt":{"route":"issue-cache-compat","attempted":False,"monitor_status":"REGISTERED","disposition":"NO_ATTEMPT_OBSERVED_NOT_NO_ACCESS"},"post_lock_publication":{"artifact_id":spec["artifact_graph"]["fresh_store"]["id"],"lock_state":"LOCKED","status":"AUTHORIZED_AFTER_LOCK"},"benign_document":{"artifact_id":spec["artifact_graph"]["benign_document"]["id"],"status":"ALLOW_TASK_DOCUMENTATION"}}
    if controls!=expected_controls: raise ValueError("access-audit diagnostic control classification")
    if not (gaps["CONTROLLED+SEALED"] < gaps["FULL+SEALED"]): raise ValueError("controlled feedback did not reduce optimism gap without bypass")
    if not (gaps["CONTROLLED+RAW_BYPASS"] >= gaps["FULL+SEALED"]): raise ValueError("bypass failed to erase controlled advantage")
    return {"trials":len(trials),"seeds":len(spec["seeds"]),"cells":means,"optimism_gaps":gaps,"method_disposition":"PASS_METHOD_SCOPED","hypothesis_disposition":"BYPASS_DEFEATS_FEEDBACK_SCOPED","checks":len(trials)*9+len(oracle)*4+16,"errors":0}

def mutation_rejected(raw,spec,name):
    x=copy.deepcopy(raw)
    if name=="hide_access_log": x["trials"][0].pop("raw_access")
    elif name=="forge_denial": x["trials"][next(i for i,r in enumerate(x["trials"]) if r["cell"]=="CONTROLLED+SEALED")]["raw_access"]["status"]="RETURNED"
    elif name=="tamper_canary": x["trials"][next(i for i,r in enumerate(x["trials"]) if r["cell"]=="CONTROLLED+RAW_BYPASS")]["raw_access"]["returned_object"]["canary"]="none"
    elif name=="leak_fresh": x["trials"][0]["fresh_prelock_probe"].update({"status":"RETURNED","returned_object":[{"case_id":"fresh-private"}]})
    elif name=="hide_safety": x["trials"][0]["immediate_safety_disclosure"]={}
    elif name=="trust_unmonitored": x["access_audit_controls"]["unmonitored_route"]["disposition"]="SAFE"
    elif name=="block_benign_docs": x["access_audit_controls"]["benign_document"]["status"]="DENIED"
    elif name=="unsafe_selection": x["trials"][0]["candidate_update"]["selected_candidate"]="unsafe"
    else: raise ValueError("unknown mutation")
    try: check(x,spec)
    except (ValueError,KeyError,TypeError,ZeroDivisionError): return True
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--raw",default=str(ROOT/"results/candidate.raw.json")); ap.add_argument("--output",default=str(ROOT/"results/audit.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    spec=json.loads(Path(a.spec).read_text()); b=Path(a.raw).read_bytes(); raw=json.loads(b); summary=check(raw,spec)
    controls={k:mutation_rejected(raw,spec,k) for k in ("hide_access_log","forge_denial","tamper_canary","leak_fresh","hide_safety","trust_unmonitored","block_benign_docs","unsafe_selection")}
    if not all(controls.values()): raise ValueError("mutation control accepted")
    summary.update({"allocation":spec["allocation"],"candidate_raw_sha256":hashlib.sha256(b).hexdigest(),"mutation_controls":controls,"mutation_rejections":f"{sum(controls.values())}/{len(controls)}","authority":"NONE"})
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
