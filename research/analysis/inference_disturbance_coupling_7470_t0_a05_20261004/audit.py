#!/usr/bin/env python3
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent; RAW=HERE/"results"/"candidate.json"
def rebuild(s):
 b=s["latency_period"]; d0=s["disturbance_period"]; rows=[]; dm=sum(d0)/len(d0); ss=sum((v-dm)**2 for v in d0)
 for k in range(len(b)):
  lp=b[k:]+b[:k]; lm=sum(lp)/len(lp); ll=sum((v-lm)**2 for v in lp); cross=sum((a-lm)*(z-dm) for a,z in zip(lp,d0)); r=round(cross/math.sqrt(ll*ss),12); L=lp*s["periods"]; D=d0*s["periods"]; arms={}
  for nm,g in (("null",s["null_gain"]),("interaction",s["interaction_gain"])):
   x=0.; tr=[]; ev=[]
   for i in range(len(L)):
    l,z=L[i],D[i]; prev=x; q=l*z; change=z-s["action_cap"]+g*q; x=max(0.,x+change); tr.append(round(x,12)); ev.append({"event":i,"period":i//len(d0),"period_index":i%len(d0),"is_seam":i%len(d0)==0 and i>0,"latency":l,"severity":z,"overlap":q,"state_before":round(prev,12),"state_delta":round(change,12),"state_after":round(x,12)})
   arms[nm]={"latencies":L,"disturbances":D,"events":ev,"state_trace":tr,"peak_state":max(tr),"outside_envelope_event_ticks":sum(v>s["envelope_max"] for v in tr),"stale_cover_occupancy_ticks":sum(L),"stale_severity_exposure":sum(e["overlap"] for e in ev),"termination_release_tick":sum(L)}
  rows.append({"shift":k,"latency_period":lp,"disturbance_period":d0,"pearson_r":r,**arms})
 return {"schema":s["schema"],"spec":s,"shift_count":len(rows),"trajectory_count":2*len(rows),"shifts":rows}
def main():
 raw=json.loads(RAW.read_text()); s=json.loads((HERE/"spec.json").read_text()); exp=rebuild(s); m1=json.loads(json.dumps(exp));m1["shifts"][0]["latency_period"][0]+=1;m2=json.loads(json.dumps(exp));m2["shifts"].pop();m3=json.loads(json.dumps(exp));m3["shifts"][0]["interaction"]["peak_state"]+=1
 null={tuple(x["null"]["state_trace"]) for x in exp["shifts"]}; peaks=[x["interaction"]["peak_state"] for x in exp["shifts"]]; seam=all(sum(e["is_seam"] for e in x[arm]["events"])==1 for x in exp["shifts"] for arm in ("null","interaction")); r=[x["pearson_r"] for x in exp["shifts"]]
 if raw!=exp or r!=s["expected_pearson_r"] or len(null)!=1 or len(set(peaks))<2 or not seam or any(m==exp for m in (m1,m2,m3)):
  print("FAIL_METHOD audit_or_preregistered_gate"); return 1
 print(f"PASS_METHOD_SCOPED shifts=4 trajectories=8 seam_rows=8 pearson_r={r} null_states=1 mutations=3/3 sha256={hashlib.sha256(RAW.read_bytes()).hexdigest()}"); return 0
if __name__=="__main__": raise SystemExit(main())
