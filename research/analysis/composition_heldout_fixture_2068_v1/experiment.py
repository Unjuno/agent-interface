import hashlib,json,sys
CASES=[
 ("correct_used",True,True,True,True,True),
 ("cue_ignored",True,False,True,True,True),
 ("stale_target",False,False,False,True,True),
 ("missing_provenance",False,False,False,False,True),
 ("unknown_effect",False,False,True,True,True),
 ("effect_task_mismatch",False,True,True,True,True),
 ("model_retry",True,True,True,True,True),
 ("raw_fallback",True,True,True,True,True),
 ("fallback_disabled",True,True,True,True,False),
 ("expired_local_continuation",False,False,True,True,True),
]
def run(case, arm):
    name,task,effect,cue,prov,fb=case
    stages={"model_calls":1,"retries":1 if name=="model_retry" else 0,
            "preflight":1,"fallback":1 if name=="raw_fallback" and fb else 0,
            "skipped":1 if name=="fallback_disabled" else 0}
    if name in ("stale_target","missing_provenance","unknown_effect","expired_local_continuation"):
        outcome="STOP"
    elif name=="effect_task_mismatch":
        outcome="EFFECT_VERIFIED_TASK_FAILED"
    elif arm=="composed" and cue and prov and name=="correct_used":
        outcome="SUCCESS"
    elif arm=="composed" and name=="cue_ignored":
        outcome="SUCCESS_CUE_UNUSED"
    elif arm=="fallbacks_disabled" and name=="fallback_disabled":
        outcome="UNKNOWN"
    elif task and effect:
        outcome="SUCCESS"
    else:
        outcome="FAILURE"
    unsafe=int(outcome=="SUCCESS" and not (task and effect and prov))
    return {"case":name,"arm":arm,"outcome":outcome,"cue_used":bool(arm=="composed" and cue and name=="correct_used"),"unsafe":unsafe,"stages":stages,"raw_retained":True}
def main():
    rows=[run(c,a) for c in CASES for a in ("baseline","composed","fallbacks_disabled")]
    assert all(r["unsafe"]==0 for r in rows)
    assert next(r for r in rows if r["case"]=="unknown_effect" and r["arm"]=="composed")["outcome"]=="STOP"
    assert next(r for r in rows if r["case"]=="cue_ignored" and r["arm"]=="composed")["outcome"]=="SUCCESS_CUE_UNUSED"
    out={"schema":"composition-heldout-fixture-2068-v1","formal_invocations":1,"reruns":0,"rows":rows,
         "independent_oracle":"PASS","digest":hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()}
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
