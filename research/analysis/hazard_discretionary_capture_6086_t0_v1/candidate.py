#!/usr/bin/env python3
"""One-shot exact-rational finite capture-schedule candidate."""
from fractions import Fraction as F
from itertools import combinations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
fb=(ROOT/"FIXTURE.json").read_bytes(); f=json.loads(fb)
half=F(*f["exposure_half_width"])
sent=f["mandatory_sentinels"]
def frac(x): return F(x[0],x[1]) if isinstance(x,list) else F(x)
def detect(onset,width,centers):
    start=F(onset); end=F(onset+width); hits=[]
    for c in sorted(centers):
        lo=F(c)-half; hi=F(c)+half
        left=max(start,lo); right=min(end,hi)
        if left<=right: hits.append((c,left-start))
    return hits
def metrics(times,width,weights):
    centers=sorted(set(sent+list(times))); outcomes=[]; den=sum(weights)
    got=delay_weight=0; max_delay=F(0)
    for onset,w in enumerate(weights):
        hits=detect(onset,width,centers)
        if hits:
            delay=min(d for _,d in hits); got+=w; delay_weight+=w*delay; max_delay=max(max_delay,delay)
            outcomes.append({"onset":onset,"weight":w,"status":"DETECTED","detected_by":min(c for c,_ in hits),"delay":str(delay)})
        else: outcomes.append({"onset":onset,"weight":w,"status":"MISSED","detected_by":None,"delay":None})
    gaps=[b-a for a,b in zip(centers,centers[1:])]
    return {"weighted_detection":[got,den],"weighted_delay_conditional":[delay_weight.numerator,delay_weight.denominator,got] if got else None,
            "detected_weight":got,"missed_onsets":[o["onset"] for o in outcomes if o["status"]=="MISSED"],
            "max_detected_delay":str(max_delay) if got else None,"max_capture_gap":max(gaps),"outcomes":outcomes}
def objective(times):
    values=[]
    for width in f["cue_widths"]:
        m=metrics(times,width,f["scoring_distributions"][f["selection_distribution"]]["weights"])
        a,b=m["weighted_detection"]; values.append(F(a,b))
    return sum(values,F(0))/len(values)
allowed=f["oracle"]["candidate_centers"]; k=f["oracle"]["count"]
oracle_times=max(combinations(allowed,k),key=lambda ts:(objective(ts),tuple(-z for z in ts)))
arms={name:{"discretionary_times":spec["times"],"source":spec["source"],"cost_count":len(spec["times"]),
            "sentinels":sent,"sentinel_sha256":hashlib.sha256(json.dumps(sent,separators=(",",":")).encode()).hexdigest(),
            "by_distribution_and_width":{d:{str(width):metrics(spec["times"],width,dist["weights"]) for width in f["cue_widths"]} for d,dist in f["scoring_distributions"].items()},
            "no_cue_false_positive_count":0,"decision_labels":["DETECTED","MISSED"]}
      for name,spec in f["schedules"].items()}
oracle={"discretionary_times":list(oracle_times),"scoring_only":True,"objective_peaked_mean_widths":[objective(oracle_times).numerator,objective(oracle_times).denominator]}
controls={"zero_hazard":{"status":"HOLD_HAZARD_UNIDENTIFIED","schedule":None},"unknown_hazard":{"status":"HOLD_HAZARD_UNIDENTIFIED","schedule":None},
          "all_budget_mandatory":{"status":"NOT_APPLICABLE","discretionary_schedule":None,"sentinels":sent},
          "same_run_label_leakage":{"status":"REJECTED_SCORING_LABEL_LEAKAGE","schedule":None},"no_cue_false_positives":{n:0 for n in arms}}
raw={"schema":"hazard-discretionary-capture-raw-v1","fixture_sha256":hashlib.sha256(fb).hexdigest(),"arms":arms,"oracle":oracle,"controls":controls}
out=ROOT/"results/t0/RAW.json"
if out.exists(): raise SystemExit("STOP_OUTPUT_EXISTS_NO_RETRY")
out.parent.mkdir(parents=True,exist_ok=False); data=(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n").encode();out.write_bytes(data)
print(json.dumps({"status":"CANDIDATE_RAW_WRITTEN","arms":len(arms),"distributions":3,"widths":2,"onsets_per_metric":12,"raw_sha256":hashlib.sha256(data).hexdigest()},sort_keys=True))
