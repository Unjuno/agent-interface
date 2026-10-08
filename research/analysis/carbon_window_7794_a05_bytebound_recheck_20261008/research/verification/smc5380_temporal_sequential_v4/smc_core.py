"""Deterministic temporal trace generator and Wald SPRT primitives for Issue #5380."""
import math
import random

P0=0.01
P1=0.08
ALPHA=0.05
BETA=0.10
MAX_SAMPLES=500
CALIBRATION_REPLICATES=2000
DEADLINE_TICK=2
FAULT_EVENT={
 "timeout":"VERIFIER_TIMEOUT",
 "stale_receipt":"STALE_RECEIPT",
 "duplicate_result":"DUPLICATE_RESULT",
 "correlated_verifier":"COMMON_CAUSE_FAILURE",
 "dropped_ack":"ACK_DROPPED",
}
FAULT_WEIGHTS={
 "timeout":0.70,
 "stale_receipt":0.10,
 "duplicate_result":0.10,
 "correlated_verifier":0.05,
 "dropped_ack":0.05,
}
LOG_UPPER=math.log((1-BETA)/ALPHA)
LOG_LOWER=math.log(BETA/(1-ALPHA))
LOG_HIT=math.log(P1/P0)
LOG_MISS=math.log((1-P1)/(1-P0))

def make_trace(seed,stratum,violation_probability):
    rng=random.Random(seed)
    events=[{"tick":0,"kind":FAULT_EVENT[stratum]}]
    if rng.random()<violation_probability:
        events.append({"tick":1,"kind":"ACTION_ADMITTED_UNVERIFIED"})
    else:
        events.append({"tick":1,"kind":"UNKNOWN"})
    return events

def temporal_violation(events,deadline=DEADLINE_TICK):
    current_verified=False
    terminal=False
    for event in sorted(events,key=lambda x:x["tick"]):
        if event["tick"]>deadline:
            continue
        if event["kind"]=="VERIFIED_CURRENT":
            current_verified=True
        elif event["kind"]=="ACTION_ADMITTED_UNVERIFIED" and not current_verified:
            return True
        elif event["kind"] in {"UNKNOWN","CONTAINMENT_COMPLETED"}:
            terminal=True
    return not terminal

def one_trace(seed,stratum,probability):
    events=make_trace(seed,stratum,probability)
    return temporal_violation(events),events

def sprt_from_samples(sample_iter,max_samples=MAX_SAMPLES):
    llr=0.0
    bits=[]
    for sample in sample_iter:
        hit=bool(sample)
        bits.append("1" if hit else "0")
        llr += LOG_HIT if hit else LOG_MISS
        if llr>=LOG_UPPER:
            return {"decision":"FAIL_RATE_AT_OR_ABOVE_P1","n":len(bits),"llr":llr,"bits":"".join(bits)}
        if llr<=LOG_LOWER:
            return {"decision":"ACCEPT_H0_AT_P0","n":len(bits),"llr":llr,"bits":"".join(bits)}
        if len(bits)>=max_samples:
            break
    return {"decision":"INCONCLUSIVE","n":len(bits),"llr":llr,"bits":"".join(bits)}

def trace_sprt(stratum,probability,seed_base,max_samples=MAX_SAMPLES):
    seeds=[]
    def samples():
        for i in range(max_samples):
            seed=seed_base+i
            violated,_=one_trace(seed,stratum,probability)
            if violated:
                seeds.append(seed)
            yield violated
    result=sprt_from_samples(samples(),max_samples)
    result["stratum"]=stratum
    result["seed_base"]=seed_base
    result["counterexample_seeds"]=seeds
    return result

def coin_sprt(true_probability,seed,max_samples=MAX_SAMPLES):
    rng=random.Random(seed)
    return sprt_from_samples((rng.random()<true_probability for _ in range(max_samples)),max_samples)

def wilson_interval(successes,total,z=1.959963984540054):
    if total<=0:
        raise ValueError("total must be positive")
    phat=successes/total
    z2=z*z
    den=1+z2/total
    center=(phat+z2/(2*total))/den
    half=z*math.sqrt(phat*(1-phat)/total+z2/(4*total*total))/den
    return [max(0.0,center-half),min(1.0,center+half)]
