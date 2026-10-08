"""Independent raw-only auditor for Issue #5531 delay/correlation allocation."""
import hashlib, json, random, sys

ALLOCATION="fd5531-delay-correlation-20261001-01"

BASE=55310000; COUNT=10000; LAST=16
KINDS=("healthy_fast","healthy_heavy_tail","partition_recover","crashed","restarted")
CUTS=(2,4,8)

def sample(kind, number):
    q=random.Random(BASE+KINDS.index(kind)*COUNT+number)
    if kind=="healthy_fast": ready=q.randrange(1,4); reboot=None
    elif kind=="healthy_heavy_tail":
        x=q.random()
        ready=q.randrange(1,4) if x<.75 else q.randrange(4,9) if x<.95 else q.randrange(9,17)
        reboot=None
    elif kind=="partition_recover": ready=q.randrange(3,13)+q.randrange(1,4); reboot=None
    elif kind=="crashed": ready=None; reboot=None
    else: reboot=10; ready=10+q.randrange(1,4)
    if kind=="crashed": wa=q.random()<.96; wb=q.random()<.94
    else:
        shared=q.random()<.04
        separate=q.random()<.005
        wa=shared or q.random()<.005
        wb=separate
    return ready,reboot,wa,wb

def replay(kind, cut, mode, i):
    ready,reboot,wa,wb=sample(kind,i)
    state="AUTHORIZED"; first_failure=None; failure_events=0
    blocked=0; clear=None; refused=0; decoys=0
    for now in range(LAST+1):
        if reboot==now:
            if state=="FAILED": state="AUTHORIZED"
        if mode=="typed" and now==6 and wa and wb:
            state="FAILED"; first_failure=now; failure_events+=1
        if state=="AUTHORIZED" and now>=cut and (ready is None or ready>now):
            state="FAILED" if mode=="baseline" else "SUSPECTED_UNAVAILABLE"
            if mode=="baseline": first_failure=now; failure_events+=1
        if now in (3,5) and mode=="typed": decoys+=1
        if ready==now and (reboot is None or now>=reboot) and mode=="typed":
            if state=="FAILED": refused+=1
            elif state=="SUSPECTED_UNAVAILABLE":
                state="AUTHORIZED"; clear=now
        if state=="SUSPECTED_UNAVAILABLE": blocked+=1
    return state,blocked,first_failure,clear,refused,failure_events,decoys

def expected(cut,mode):
    answer=[]
    for kind in KINDS:
        finals={}; false_final=0; detected=0; blocked=0; suspect_any=0; refused=0; fail_events=0; decoys=0
        chain=bytes(32)
        for i in range(COUNT):
            state,bt,ft,ct,rf,fe,dc=replay(kind,cut,mode,i)
            finals[state]=finals.get(state,0)+1
            false_final += int(state=="FAILED" and kind!="crashed")
            detected += int(kind=="crashed" and ft is not None and ft<=8)
            blocked+=bt; suspect_any+=int(bt>0); refused+=rf; fail_events+=fe if kind!="crashed" else 0; decoys+=dc
            row=f"{i}|{state}|{bt}|{ft}|{ct}|{rf}|{fe}|{dc}".encode()
            chain=hashlib.sha256(chain+row).digest()
        answer.append({"scenario":kind,"n":COUNT,"final":finals,"false_failed":false_final,
          "crash_failed_by_8":detected,"suspect_tick_sum":blocked,"suspect_any":suspect_any,
          "late_response_rejected_after_failed":refused,"false_terminal_failures":fail_events,
          "decoys_ignored":decoys,"hash_chain":chain.hex()})
    return answer

def audit(raw, expected_freeze_sha):
    errors=[]
    if raw.get("schema")!="fd5531-delay-correlation-raw-v1": errors.append("schema")
    if raw.get("allocation")!=ALLOCATION: errors.append("allocation")
    if raw.get("freeze_blob_sha")!=expected_freeze_sha: errors.append("freeze_identity")
    if raw.get("runtime",{}).get("container") is not False: errors.append("container_flag")
    if raw.get("parameters",{}).get("episodes_per_scenario")!=COUNT: errors.append("count")
    expected_thresholds={}
    for cut in CUTS:
        expected_thresholds[str(cut)]={"typed":expected(cut,"typed"),"timeout_as_failure":expected(cut,"baseline")}
    if raw.get("threshold_results")!=expected_thresholds: errors.append("replay_mismatch")
    primary=raw.get("threshold_results",{}).get("4",{})
    typed=primary.get("typed",[])
    baseline=primary.get("timeout_as_failure",[])
    if len(typed)!=len(KINDS) or len(baseline)!=len(KINDS): errors.append("coverage")
    if sum(x.get("late_response_rejected_after_failed",0) for x in typed)==0: errors.append("no_late_rejection_exercised")
    if any(x.get("decoys_ignored")!=2*COUNT for x in typed): errors.append("decoy_accounting")
    crash=next((x for x in typed if x.get("scenario")=="crashed"),{})
    if crash.get("crash_failed_by_8",0)<8900: errors.append("crash_completeness_gate")
    htail=next((x for x in typed if x.get("scenario")=="healthy_heavy_tail"),{})
    btail=next((x for x in baseline if x.get("scenario")=="healthy_heavy_tail"),{})
    if htail.get("false_failed",1)>=btail.get("false_failed",0): errors.append("no_accuracy_improvement")
    result={"schema":"fd5531-delay-correlation-audit-v1","errors":errors,"integrity_pass":not errors,
      "candidate_imported":False,"episodes_recomputed":COUNT*len(KINDS)*len(CUTS)*2,
      "policy_rows_recomputed":COUNT*len(KINDS)*len(CUTS)*2,"gates_rechecked":True}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0 if not errors else 1

if __name__=="__main__":
    import base64
    raise SystemExit(audit(json.loads(base64.b64decode(sys.argv[1]).decode("utf-8")),sys.argv[2]))
