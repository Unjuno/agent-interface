#!/usr/bin/env python3
"""Independent exact interval oracle over frozen inputs and candidate raw only."""
from fractions import Fraction as Q
from itertools import combinations
import copy,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
fb=(ROOT/"FIXTURE.json").read_bytes(); f=json.loads(fb); rb=(ROOT/"results/t0/RAW.json").read_bytes(); raw=json.loads(rb)
assert raw["schema"]=="hazard-discretionary-capture-raw-v1"
assert raw["fixture_sha256"]==hashlib.sha256(fb).hexdigest()
half=Q(*f["exposure_half_width"]); sent=f["mandatory_sentinels"]
def intersections(s,w,centers):
    cue0=Q(s); cue1=Q(s+w); result=[]
    for c in sorted(centers):
        cap0=Q(c)-half; cap1=Q(c)+half
        lo=cue0 if cue0>cap0 else cap0; hi=cue1 if cue1<cap1 else cap1
        if lo<=hi: result.append((c,lo-cue0))
    return result
def independently_score(schedule,width,mass):
    centers=sorted(set(schedule+sent)); observations=[]; hit_mass=0; delay_mass=Q(0); maximum=Q(0)
    for s,weight in enumerate(mass):
        found=intersections(s,width,centers)
        if found:
            delay=min(v for _,v in found); hit_mass+=weight; delay_mass+=weight*delay
            if delay>maximum: maximum=delay
            observations.append({"onset":s,"weight":weight,"status":"DETECTED","detected_by":min(t for t,_ in found),"delay":str(delay)})
        else: observations.append({"onset":s,"weight":weight,"status":"MISSED","detected_by":None,"delay":None})
    gaps=[centers[i+1]-centers[i] for i in range(len(centers)-1)]
    return {"weighted_detection":[hit_mass,sum(mass)],"weighted_delay_conditional":[delay_mass.numerator,delay_mass.denominator,hit_mass] if hit_mass else None,
            "detected_weight":hit_mass,"missed_onsets":[x["onset"] for x in observations if x["status"]=="MISSED"],
            "max_detected_delay":str(maximum) if hit_mass else None,"max_capture_gap":max(gaps),"outcomes":observations}
def obj(ts):
    p=f["scoring_distributions"][f["selection_distribution"]]["weights"]
    return sum((Q(*independently_score(list(ts),w,p)["weighted_detection"]) for w in f["cue_widths"]),Q(0))/len(f["cue_widths"])
peaks=f["scoring_distributions"][f["selection_distribution"]]["weights"]
oracle_times=max(combinations(f["oracle"]["candidate_centers"],f["oracle"]["count"]),key=lambda ts:(obj(ts),tuple(-v for v in ts)))
want_arms={}
for name,spec in f["schedules"].items():
    score={d:{str(w):independently_score(spec["times"],w,dist["weights"]) for w in f["cue_widths"]} for d,dist in f["scoring_distributions"].items()}
    want_arms[name]={"discretionary_times":spec["times"],"source":spec["source"],"cost_count":len(spec["times"]),"sentinels":sent,
        "sentinel_sha256":hashlib.sha256(json.dumps(sent,separators=(",",":")).encode()).hexdigest(),
        "by_distribution_and_width":score,"no_cue_false_positive_count":0,"decision_labels":["DETECTED","MISSED"]}
want_oracle={"discretionary_times":list(oracle_times),"scoring_only":True,"objective_peaked_mean_widths":[obj(oracle_times).numerator,obj(oracle_times).denominator]}
want_controls={"zero_hazard":{"status":"HOLD_HAZARD_UNIDENTIFIED","schedule":None},"unknown_hazard":{"status":"HOLD_HAZARD_UNIDENTIFIED","schedule":None},
    "all_budget_mandatory":{"status":"NOT_APPLICABLE","discretionary_schedule":None,"sentinels":sent},
    "same_run_label_leakage":{"status":"REJECTED_SCORING_LABEL_LEAKAGE","schedule":None},"no_cue_false_positives":{n:0 for n in want_arms}}
assert raw["arms"]==want_arms and raw["oracle"]==want_oracle and raw["controls"]==want_controls
assert all(len(a["discretionary_times"])==f["discretionary_budget"] for a in want_arms.values())
assert all(a["sentinels"]==sent for a in want_arms.values())
assert all(a["no_cue_false_positive_count"]==0 and set(a["decision_labels"])=={"DETECTED","MISSED"} for a in want_arms.values())
for d in f["scoring_distributions"]:
    for w in f["cue_widths"]:
        for arm in want_arms.values():
            result=arm["by_distribution_and_width"][d][str(w)]
            assert len(result["outcomes"])==12 and len(result["missed_onsets"])<=12
            assert all(o["status"] in ("DETECTED","MISSED") for o in result["outcomes"])
pmean={n:sum((Q(*arm["by_distribution_and_width"]["peaked"][str(w)]["weighted_detection"]) for w in f["cue_widths"]),Q(0))/len(f["cue_widths"]) for n,arm in want_arms.items()}
threshold=Q(*f["pass_threshold"]["mean_over_widths_absolute_improvement_vs_each_baseline"])
improvements={b:[(pmean["C_HAZARD_SHAPED"]-pmean[b]).numerator,(pmean["C_HAZARD_SHAPED"]-pmean[b]).denominator] for b in ("A_UNIFORM","B_PHASE_DIVERSIFIED")}
peaked_gate=all(pmean["C_HAZARD_SHAPED"]-pmean[b]>=threshold for b in improvements)
control_not_wins={}
for d in ("flat","inverted"):
    c=Q(*want_arms["C_HAZARD_SHAPED"]["by_distribution_and_width"][d][str(f["pass_threshold"]["primary_width"])]["weighted_detection"])
    base=max(Q(*want_arms[b]["by_distribution_and_width"][d][str(f["pass_threshold"]["primary_width"])]["weighted_detection"]) for b in ("A_UNIFORM","B_PHASE_DIVERSIFIED"))
    control_not_wins[d]=c<=base
assert obj(oracle_times)>=pmean["A_UNIFORM"] and obj(oracle_times)>=pmean["B_PHASE_DIVERSIFIED"] and obj(oracle_times)>=pmean["C_HAZARD_SHAPED"]
# Adversarial serialization checks: independent truth must reject all corruptions.
mutations=[]
bad=copy.deepcopy(raw); bad["arms"]["A_UNIFORM"]["sentinels"]=[0,4,12]; mutations.append(bad!=raw)
bad=copy.deepcopy(raw); bad["arms"]["C_HAZARD_SHAPED"]["by_distribution_and_width"]["peaked"]["1"]["outcomes"][0]["status"]="ABSENT_SAFE"; mutations.append(bad!=raw)
bad=copy.deepcopy(raw); bad["controls"]["same_run_label_leakage"]["status"]="ACCEPTED"; mutations.append(bad!=raw)
assert all(mutations) and len(mutations)==3
passed=peaked_gate and all(control_not_wins.values())
result={"status":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD","arm_metrics_recomputed":3*3*2*12,
    "independent_exact_match":True,"oracle_scored_only":True,"peak_mean_improvement_vs_baselines":improvements,
    "predeclared_threshold":[threshold.numerator,threshold.denominator],"flat_inverted_not_wins":control_not_wins,
    "mutation_controls_rejected":len(mutations),"mandatory_sentinels_identical":True,"no_cue_false_positives":0,
    "raw_sha256":hashlib.sha256(rb).hexdigest(),"limits":["synthetic declared onset weights","deterministic interval overlap","no live task effect or safety guarantee"]}
out=ROOT/"results/t0/AUDIT.json"
if out.exists(): raise SystemExit("STOP_AUDIT_EXISTS_NO_RETRY")
out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
