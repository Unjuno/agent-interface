from __future__ import annotations
import argparse,json
from pathlib import Path

EXPECTED_N=100_000
EXPECTED_CONTROLS=20_000

def main():
    ap=argparse.ArgumentParser();ap.add_argument("result");ap.add_argument("--out",required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());e=[]
    if r.get("formal_invocations")!=1 or r.get("reruns")!=0:e.append("invocation")
    if r.get("universe")!=[-2,-1,1,2] or r.get("k")!=2:e.append("budget_universe")
    if r.get("grants_prepared_authority") is not False:e.append("prepared_authority")
    A=r["arms"];C=r["controls"]
    for arm in ("wait","current","temporal"):
        x=A[arm]
        if x["n"]!=EXPECTED_N:e.append(arm+"_n")
        if x["effect_correct"]!=EXPECTED_N:e.append(arm+"_effect")
        if x["wrong_admissions"]!=0 or x["authority_laundering"]!=0:e.append(arm+"_safety")
        for c in ("forced_reversal","expiry","no_authority"):
            if C[arm][c]["n"]!=EXPECTED_CONTROLS:e.append(arm+"_"+c+"_n")
        if C[arm]["forced_reversal"]["pre_fallback_admissions"]!=0:e.append(arm+"_reversal_admit")
        if C[arm]["expiry"]["expired_admissions"]!=0:e.append(arm+"_expiry_admit")
        if C[arm]["no_authority"]["admissions"]!=0 or C[arm]["no_authority"]["effects"]!=0:e.append(arm+"_noauth")
    hit_gain=A["temporal"]["branch_hit_rate"]-A["current"]["branch_hit_rate"]
    latency_gain=A["current"]["latency_ns"]["mean"]-A["temporal"]["latency_ns"]["mean"]
    resume_gain=A["current"]["planner_resumption_rate"]-A["temporal"]["planner_resumption_rate"]
    if A["wait"]["branch_hits"]!=0 or A["wait"]["planner_resumptions"]!=EXPECTED_N:e.append("wait_semantics")
    if not (101_000_000 <= A["wait"]["latency_ns"]["mean"] <= 102_500_000):e.append("wait_latency")
    if hit_gain<.05:e.append("hit_gain")
    if latency_gain<5_000_000:e.append("latency_gain")
    if resume_gain<.05:e.append("resume_gain")
    decision="PASS_RUNG1_TEMPORAL_SPECULATION_GAP_SCOPED" if not e else ("FAIL_AUTHORITY_OR_STALE_EXECUTION" if any("safety" in x or "admit" in x or "noauth" in x or "authority" in x for x in e) else "HOLD_RUNG1_NO_USEFUL_LATENCY_GAIN")
    out={"decision":decision,"errors":e,"hit_rate_current":A["current"]["branch_hit_rate"],"hit_rate_temporal":A["temporal"]["branch_hit_rate"],
      "hit_gain_pp":100*hit_gain,"mean_latency_current_ns":A["current"]["latency_ns"]["mean"],"mean_latency_temporal_ns":A["temporal"]["latency_ns"]["mean"],
      "mean_latency_gain_ns":latency_gain,"planner_resume_gain_pp":100*resume_gain,
      "wait_mean_latency_ns":A["wait"]["latency_ns"]["mean"]}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
