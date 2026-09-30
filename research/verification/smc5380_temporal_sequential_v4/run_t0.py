"""One-shot comparison: fixed replay, uniform sample, stratified sequential SMC."""
import json,platform,sys,random
from smc_core import *
CORE_GIT_BLOB_SHA="f0d07ea839bc4e8b80bb9d10b9640e6c03e4aa55"
STRATA=list(FAULT_WEIGHTS)
PROFILE={name:(P1 if name=="correlated_verifier" else P0) for name in STRATA}

def fixed_replay():
    rows=[]
    for j,stratum in enumerate(STRATA):
        base=10000+j*1000
        bits=[]; seeds=[]
        for i in range(20):
            seed=base+i
            violated,_=one_trace(seed,stratum,PROFILE[stratum])
            bits.append("1" if violated else "0")
            if violated: seeds.append(seed)
        rows.append({"stratum":stratum,"n":len(bits),"bits":"".join(bits),"counterexample_seeds":seeds})
    return rows

def uniform_sample():
    rng=random.Random(987654321)
    names=rng.choices(STRATA,weights=[FAULT_WEIGHTS[x] for x in STRATA],k=1000)
    by={x:{"n":0,"violations":0,"counterexample_seeds":[]} for x in STRATA}
    for i,stratum in enumerate(names):
        seed=1000000+i
        violated,_=one_trace(seed,stratum,PROFILE[stratum])
        row=by[stratum]; row["n"]+=1
        if violated:
            row["violations"]+=1; row["counterexample_seeds"].append(seed)
    n=sum(v["n"] for v in by.values()); k=sum(v["violations"] for v in by.values())
    return {"n":n,"violations":k,"rate":k/n,"wilson_95":wilson_interval(k,n),
            "fault_weights":FAULT_WEIGHTS,"by_stratum":by,
            "stratum_schedule_sha256":__import__("hashlib").sha256("|".join(names).encode()).hexdigest()}

def calibration(true_p,seed_base):
    outcomes=[]
    for i in range(CALIBRATION_REPLICATES):
        res=coin_sprt(true_p,seed_base+i)
        outcomes.append({"FAIL_RATE_AT_OR_ABOVE_P1":"F","ACCEPT_H0_AT_P0":"S","INCONCLUSIVE":"I"}[res["decision"]])
    fail=outcomes.count("F"); safe=outcomes.count("S"); inconclusive=outcomes.count("I")
    return {"true_p":true_p,"replicates":len(outcomes),"seed_base":seed_base,
            "outcomes":"".join(outcomes),"false_fail_or_detect":fail,"accept_h0":safe,"inconclusive":inconclusive,
            "rate":fail/len(outcomes),"wilson_95":wilson_interval(fail,len(outcomes))}

def main():
    fixed=fixed_replay()
    uniform=uniform_sample()
    strata=[]
    for j,name in enumerate(STRATA):
        strata.append(trace_sprt(name,PROFILE[name],2000000+j*10000))
    null_cal=calibration(P0,3000000)
    alt_cal=calibration(P1,4000000)
    null_upper=null_cal["wilson_95"][1]
    alt_lower=alt_cal["wilson_95"][0]
    calibration_pass=(null_upper<=0.08 and alt_lower>=0.85
                      and null_cal["inconclusive"]/CALIBRATION_REPLICATES<=0.02
                      and alt_cal["inconclusive"]/CALIBRATION_REPLICATES<=0.15)
    correlated=[r for r in strata if r["stratum"]=="correlated_verifier"][0]
    detected=correlated["decision"]=="FAIL_RATE_AT_OR_ABOVE_P1"
    raw={"schema":"smc5380-temporal-sequential-v4-raw",
         "allocation":"smc5380-temporal-sequential-v4-20260930-01",
         "runtime":{"python":platform.python_version(),"platform":sys.platform,"container":False},
         "source_identity":{"core_git_blob_sha":CORE_GIT_BLOB_SHA},
         "parameters":{"p0":P0,"p1":P1,"alpha":ALPHA,"beta":BETA,"max_samples":MAX_SAMPLES,
                       "calibration_replicates":CALIBRATION_REPLICATES,"deadline_tick":DEADLINE_TICK,
                       "fault_weights":FAULT_WEIGHTS,"injected_rates":PROFILE},
         "fixed_replay":fixed,"uniform_sample":uniform,"stratified_sequential":strata,
         "calibration":{"null":null_cal,"alternative":alt_cal,"pass":calibration_pass},
         "counts":{"fixed_traces":sum(r["n"] for r in fixed),"uniform_traces":uniform["n"],
                   "sequential_samples":sum(r["n"] for r in strata),
                   "retained_main_counterexample_seeds":sum(len(r["counterexample_seeds"]) for r in fixed)
                      +sum(len(r["counterexample_seeds"]) for r in uniform["by_stratum"].values())
                      +sum(len(r["counterexample_seeds"]) for r in strata)},
         "side_effects":{"authority_grants":0,"action_dispatches":0,"model_calls":0,"gpu_calls":0,"network_calls":0},
         "disposition":"PASS_SMC_METHOD_CALIBRATION_SCOPED" if calibration_pass and detected
                       else "FAIL_OR_UNCERTAIN_SMC_METHOD_CALIBRATION"}
    print(json.dumps(raw,sort_keys=True,separators=(",",":")))
    return 0
if __name__=="__main__": raise SystemExit(main())
