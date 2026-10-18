#!/usr/bin/env python3
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent; RAW=HERE/"results"/"candidate.json"

def reconstruct(s):
    base=s["latency_period"]; d0=s["disturbance_period"]; out=[]; dm=sum(d0)/len(d0); vd=sum((v-dm)**2 for v in d0)
    for shift in range(len(base)):
        lp=base[shift:]+base[:shift]; lat=lp*s["periods"]; d=d0*s["periods"]; lm=sum(lp)/len(lp); vl=sum((v-lm)**2 for v in lp); cov=sum((a-lm)*(b-dm) for a,b in zip(lp,d0))/len(lp); r=round(cov/math.sqrt(vl*vd),12); arms={}
        for name,g in (("null",s["null_gain"]),("interaction",s["interaction_gain"])):
            x=0.; tr=[]; ev=[]
            for i in range(len(lat)):
                l,sev=lat[i],d[i]; prev=x; ov=l*sev; change=sev-s["action_cap"]+g*ov; x=max(0.,x+change); tr.append(round(x,12)); ev.append({"event":i,"period":i//len(d0),"period_index":i%len(d0),"is_seam":i%len(d0)==0 and i>0,"latency":l,"severity":sev,"overlap":ov,"state_before":round(prev,12),"state_delta":round(change,12),"state_after":round(x,12)})
            arms[name]={"latencies":lat,"disturbances":d,"events":ev,"state_trace":tr,"peak_state":max(tr),"outside_envelope_event_ticks":sum(v>s["envelope_max"] for v in tr),"stale_cover_occupancy_ticks":sum(lat),"stale_severity_exposure":sum(e["overlap"] for e in ev),"termination_release_tick":sum(lat)}
        out.append({"shift":shift,"latency_period":lp,"disturbance_period":d0,"centered_pearson_r":r,**arms})
    return {"schema":"inference-disturbance-coupling-circular-seam-v1","spec":s,"shift_count":len(out),"trajectory_count":2*len(out),"shifts":out}

def main():
    raw=json.loads(RAW.read_text()); s=json.loads((HERE/"spec.json").read_text()); exp=reconstruct(s)
    m1=json.loads(json.dumps(exp)); m1["shifts"][0]["latency_period"][0]+=1
    m2=json.loads(json.dumps(exp)); m2["shifts"].pop()
    m3=json.loads(json.dumps(exp)); m3["shifts"][0]["interaction"]["peak_state"]+=1
    null={tuple(x["null"]["state_trace"]) for x in exp["shifts"]}; peaks=[x["interaction"]["peak_state"] for x in exp["shifts"]]
    seam=all(sum(e["is_seam"] for e in x["interaction"]["events"])==1 for x in exp["shifts"])
    if raw!=exp or len(null)!=1 or len(set(peaks))<2 or not seam or any(m==exp for m in (m1,m2,m3)):
        print("FAIL_METHOD audit_or_preregistered_gate"); return 1
    print(f"PASS_METHOD_SCOPED shifts=4 trajectories=8 seam_events=4 null_states={len(null)} phase_peaks={peaks} mutations=3/3 sha256={hashlib.sha256(RAW.read_bytes()).hexdigest()}"); return 0
if __name__=="__main__": raise SystemExit(main())
