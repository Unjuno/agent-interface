#!/usr/bin/env python3
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent; OUT=HERE/"results"
def canon(x): return (json.dumps(x,sort_keys=True,separators=(",",":"))+"\n").encode()
def run(s):
 b=s["latency_period"]; d0=s["disturbance_period"]; rows=[]; dm=sum(d0)/len(d0); sd=sum((x-dm)**2 for x in d0)
 for k in range(len(b)):
  lp=b[k:]+b[:k]; lm=sum(lp)/len(lp); sl=sum((x-lm)**2 for x in lp); cov=sum((x-lm)*(y-dm) for x,y in zip(lp,d0)); corr=round(cov/math.sqrt(sl*sd),12); ls=lp*s["periods"]; ds=d0*s["periods"]; arms={}
  for name,g in (("null",s["null_gain"]),("interaction",s["interaction_gain"])):
   x=0.; trace=[]; ev=[]
   for i,(l,z) in enumerate(zip(ls,ds)):
    old=x; ov=l*z; dx=z-s["action_cap"]+g*ov; x=max(0.,x+dx); trace.append(round(x,12)); ev.append({"event":i,"period":i//len(d0),"period_index":i%len(d0),"is_seam":i%len(d0)==0 and i>0,"latency":l,"severity":z,"overlap":ov,"state_before":round(old,12),"state_delta":round(dx,12),"state_after":round(x,12)})
   arms[name]={"latencies":ls,"disturbances":ds,"events":ev,"state_trace":trace,"peak_state":max(trace),"outside_envelope_event_ticks":sum(v>s["envelope_max"] for v in trace),"stale_cover_occupancy_ticks":sum(ls),"stale_severity_exposure":sum(e["overlap"] for e in ev),"termination_release_tick":sum(ls)}
  rows.append({"shift":k,"latency_period":lp,"disturbance_period":d0,"pearson_r":corr,**arms})
 return {"schema":s["schema"],"spec":s,"shift_count":len(rows),"trajectory_count":2*len(rows),"shifts":rows}
def main():
 OUT.mkdir(parents=True,exist_ok=False); s=json.loads((HERE/"spec.json").read_text()); raw=canon(run(s)); (OUT/"candidate.json").write_bytes(raw); print(f"CANDIDATE_COMPLETE shifts=4 trajectories=8 events_per_trajectory=8 sha256={hashlib.sha256(raw).hexdigest()}"); return 0
if __name__=="__main__": raise SystemExit(main())
