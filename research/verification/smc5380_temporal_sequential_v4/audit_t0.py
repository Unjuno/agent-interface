"""Pre-run frozen independent auditor for Issue #5380 temporal/SPRT raw."""
import base64,hashlib,json,math,random,sys
EXPECTED_CORE_SHA="f0d07ea839bc4e8b80bb9d10b9640e6c03e4aa55"
STRATA=["timeout","stale_receipt","duplicate_result","correlated_verifier","dropped_ack"]
WEIGHTS={"timeout":0.70,"stale_receipt":0.10,"duplicate_result":0.10,"correlated_verifier":0.05,"dropped_ack":0.05}
P0=0.01; P1=0.08; ALPHA=0.05; BETA=0.10; MAX_N=500; REPS=2000; DEADLINE=2
UP=math.log((1-BETA)/ALPHA); LOW=math.log(BETA/(1-ALPHA))
HIT=math.log(P1/P0); MISS=math.log((1-P1)/(1-P0))
FAULT={"timeout":"VERIFIER_TIMEOUT","stale_receipt":"STALE_RECEIPT","duplicate_result":"DUPLICATE_RESULT","correlated_verifier":"COMMON_CAUSE_FAILURE","dropped_ack":"ACK_DROPPED"}
PROFILE={s:(P1 if s=="correlated_verifier" else P0) for s in STRATA}

def wilson(k,n):
    z=1.959963984540054; ph=k/n; z2=z*z; den=1+z2/n
    center=(ph+z2/(2*n))/den
    half=z*math.sqrt(ph*(1-ph)/n+z2/(4*n*n))/den
    return [max(0.0,center-half),min(1.0,center+half)]

def trace_oracle(seed,stratum,p):
    rng=random.Random(seed); fault=FAULT[stratum]
    if rng.random()<p:
        events=[(0,fault),(1,"ACTION_ADMITTED_UNVERIFIED")]
    else:
        events=[(0,fault),(1,"UNKNOWN")]
    has_fresh=False; terminal=False
    for tick,kind in events:
        if tick>DEADLINE: continue
        if kind=="VERIFIED_CURRENT": has_fresh=True
        if kind=="ACTION_ADMITTED_UNVERIFIED" and not has_fresh: return True
        if kind in {"UNKNOWN","CONTAINMENT_COMPLETED"}: terminal=True
    return not terminal

def trace_bits(base,stratum,p,n):
    return "".join("1" if trace_oracle(base+i,stratum,p) else "0" for i in range(n))

def sprt(bits):
    llr=0.0
    for i,ch in enumerate(bits,1):
        llr += HIT if ch=="1" else MISS
        if llr>=UP: return ("FAIL_RATE_AT_OR_ABOVE_P1",i,llr)
        if llr<=LOW: return ("ACCEPT_H0_AT_P0",i,llr)
        if i>=MAX_N: break
    return ("INCONCLUSIVE",min(len(bits),MAX_N),llr)

def coin_decision(p,seed):
    rng=random.Random(seed); bits=[]
    for _ in range(MAX_N):
        bits.append("1" if rng.random()<p else "0")
        outcome,n,_=sprt("".join(bits))
        if outcome!="INCONCLUSIVE": return {"FAIL_RATE_AT_OR_ABOVE_P1":"F","ACCEPT_H0_AT_P0":"S"}[outcome]
    return "I"

def audit(raw):
    errors=[]
    if raw.get("schema")!="smc5380-temporal-sequential-v4-raw": errors.append("schema")
    if raw.get("allocation")!="smc5380-temporal-sequential-v4-20260930-01": errors.append("allocation")
    if raw.get("source_identity",{}).get("core_git_blob_sha")!=EXPECTED_CORE_SHA: errors.append("core_source")
    params=raw.get("parameters",{})
    if params!={"p0":P0,"p1":P1,"alpha":ALPHA,"beta":BETA,"max_samples":MAX_N,
                "calibration_replicates":REPS,"deadline_tick":DEADLINE,"fault_weights":WEIGHTS,"injected_rates":PROFILE}:
        errors.append("parameters")
    expected_fixed=[]
    for j,s in enumerate(STRATA):
        base=10000+j*1000; bits=trace_bits(base,s,PROFILE[s],20)
        expected_fixed.append({"stratum":s,"n":20,"bits":bits,"counterexample_seeds":[base+i for i,b in enumerate(bits) if b=="1"]})
    if raw.get("fixed_replay")!=expected_fixed: errors.append("fixed_replay")
    rng=random.Random(987654321); names=rng.choices(STRATA,weights=[WEIGHTS[x] for x in STRATA],k=1000)
    by={s:{"n":0,"violations":0,"counterexample_seeds":[]} for s in STRATA}
    for i,s in enumerate(names):
        seed=1000000+i; hit=trace_oracle(seed,s,PROFILE[s]); row=by[s]; row["n"]+=1
        if hit: row["violations"]+=1; row["counterexample_seeds"].append(seed)
    k=sum(v["violations"] for v in by.values()); pooled={"n":1000,"violations":k,"rate":k/1000,"wilson_95":wilson(k,1000),
        "fault_weights":WEIGHTS,"by_stratum":by,
        "stratum_schedule_sha256":hashlib.sha256("|".join(names).encode()).hexdigest()}
    if raw.get("uniform_sample")!=pooled: errors.append("uniform_sample")
    expected_seq=[]
    for j,s in enumerate(STRATA):
        base=2000000+j*10000; bits=""; ce=[]
        for i in range(MAX_N):
            bit="1" if trace_oracle(base+i,s,PROFILE[s]) else "0"; bits+=bit
            if bit=="1": ce.append(base+i)
            decision,n,llr=sprt(bits)
            if decision!="INCONCLUSIVE": break
        expected_seq.append({"decision":decision,"n":n,"llr":llr,"bits":bits,"stratum":s,"seed_base":base,"counterexample_seeds":ce})
    if raw.get("stratified_sequential")!=expected_seq: errors.append("stratified_sequential")
    def cal(p,seed_base):
        outcomes="".join(coin_decision(p,seed_base+i) for i in range(REPS))
        fails=outcomes.count("F"); safe=outcomes.count("S"); inc=outcomes.count("I")
        return {"true_p":p,"replicates":REPS,"seed_base":seed_base,"outcomes":outcomes,
                "false_fail_or_detect":fails,"accept_h0":safe,"inconclusive":inc,"rate":fails/REPS,"wilson_95":wilson(fails,REPS)}
    null=cal(P0,3000000); alt=cal(P1,4000000)
    corr=next(r for r in expected_seq if r["stratum"]=="correlated_verifier")
    calpass=(null["wilson_95"][1]<=0.08 and alt["wilson_95"][0]>=0.85
        and null["inconclusive"]/REPS<=0.02 and alt["inconclusive"]/REPS<=0.15)
    expected_cal={"null":null,"alternative":alt,"pass":calpass}
    if raw.get("calibration")!=expected_cal: errors.append("calibration")
    ce_count=sum(len(x["counterexample_seeds"]) for x in expected_fixed)+sum(len(x["counterexample_seeds"]) for x in by.values())+sum(len(x["counterexample_seeds"]) for x in expected_seq)
    expected_counts={"fixed_traces":100,"uniform_traces":1000,"sequential_samples":sum(x["n"] for x in expected_seq),"retained_main_counterexample_seeds":ce_count}
    if raw.get("counts")!=expected_counts: errors.append("counts")
    if raw.get("side_effects")!={"authority_grants":0,"action_dispatches":0,"model_calls":0,"gpu_calls":0,"network_calls":0}: errors.append("side_effects")
    disposition="PASS_SMC_METHOD_CALIBRATION_SCOPED" if calpass and corr["decision"]=="FAIL_RATE_AT_OR_ABOVE_P1" else "FAIL_OR_UNCERTAIN_SMC_METHOD_CALIBRATION"
    if raw.get("disposition")!=disposition: errors.append("disposition")
    result={"schema":"smc5380-temporal-sequential-v4-audit","errors":errors,"integrity_pass":not errors,
            "fixed_traces_recomputed":100,"uniform_traces_recomputed":1000,"sequential_strata_recomputed":5,
            "calibration_replicates_recomputed":2*REPS,"candidate_imported":False}
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0 if not errors else 1
if __name__=="__main__":
    raw=json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
    raise SystemExit(audit(raw))
