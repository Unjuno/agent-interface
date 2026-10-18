#!/usr/bin/env python3
import hashlib, json, math
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/"results"

def canonical(x): return (json.dumps(x,sort_keys=True,separators=(",",":"))+"\n").encode()

def run(s):
    base=s["latency_period"]; d0=s["disturbance_period"]; out=[]
    dm=sum(d0)/len(d0); vd=sum((v-dm)**2 for v in d0)
    for shift in range(len(base)):
        l0=base[shift:]+base[:shift]; d=d0*s["periods"]; lat=l0*s["periods"]
        lm=sum(l0)/len(l0); vl=sum((v-lm)**2 for v in l0)
        cov=sum((a-lm)*(b-dm) for a,b in zip(l0,d0))/len(l0)
        corr=cov/math.sqrt(vl*vd)
        arms={}
        for name,g in (("null",s["null_gain"]),("interaction",s["interaction_gain"])):
            x=0.; trace=[]; events=[]
            for i,(l,sev) in enumerate(zip(lat,d)):
                before=x; ov=l*sev; dx=sev-s["action_cap"]+g*ov; x=max(0.,x+dx)
                trace.append(round(x,12)); events.append({"event":i,"period":i//len(d0),"period_index":i%len(d0),"is_seam":i%len(d0)==0 and i>0,"latency":l,"severity":sev,"overlap":ov,"state_before":round(before,12),"state_delta":round(dx,12),"state_after":round(x,12)})
            arms[name]={"latencies":lat,"disturbances":d,"events":events,"state_trace":trace,"peak_state":max(trace),"outside_envelope_event_ticks":sum(v>s["envelope_max"] for v in trace),"stale_cover_occupancy_ticks":sum(lat),"stale_severity_exposure":sum(e["overlap"] for e in events),"termination_release_tick":sum(lat)}
        out.append({"shift":shift,"latency_period":l0,"disturbance_period":d0,"centered_pearson_r":round(corr,12),**arms})
    return {"schema":"inference-disturbance-coupling-circular-seam-v1","spec":s,"shift_count":len(out),"trajectory_count":2*len(out),"shifts":out}

def main():
    OUT.mkdir(parents=True,exist_ok=False); s=json.loads((HERE/"spec.json").read_text()); raw=canonical(run(s)); (OUT/"candidate.json").write_bytes(raw); print(f"CANDIDATE_COMPLETE shifts=4 trajectories=8 events_per_trajectory=8 sha256={hashlib.sha256(raw).hexdigest()}"); return 0
if __name__=="__main__": raise SystemExit(main())
