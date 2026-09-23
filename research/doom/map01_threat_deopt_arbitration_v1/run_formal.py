from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from policy import latest_ready, authority_guarded

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def proposal(pid, resource, source, action, at, authority_id=None):
    return {"proposal_id":pid,"resource":resource,"source":source,"authority_id":authority_id,"action":action,"proposed_at":at,"ready":True}

def fixture(name):
    lease={"authority_id":"T1","resource":"locomotion","active":True,"valid_context":True,"start_tick":0,"end_tick":20}
    threat=proposal("threat-1","locomotion","threat","strafe_left",10,"T1")
    deopt=proposal("deopt-1","locomotion","deopt","turn_right_6x",11)
    if name=="overlap_deopt_late": return [threat,deopt],[lease]
    if name=="overlap_threat_late": return [{**deopt,"proposed_at":10},{**threat,"proposed_at":11}],[lease]
    if name=="active_lease_missing_threat_command": return [deopt],[lease]
    if name=="expired_lease_deopt": return [deopt],[{**lease,"end_tick":10}]
    if name=="invalid_context_deopt": return [deopt],[{**lease,"valid_context":False}]
    if name=="nonoverlap_resources":
        return [proposal("threat-fire","fire","threat","fire",10,"T1"),deopt],[{**lease,"resource":"fire"}]
    if name=="deopt_only": return [deopt],[]
    if name=="threat_only": return [threat],[lease]
    raise KeyError(name)

def expected(name):
    if name=="overlap_deopt_late": return {"latest_ready":{"locomotion":"deopt"},"authority_guarded":{"locomotion":"threat"}}
    if name=="overlap_threat_late": return {"latest_ready":{"locomotion":"threat"},"authority_guarded":{"locomotion":"threat"}}
    if name=="active_lease_missing_threat_command": return {"latest_ready":{"locomotion":"deopt"},"authority_guarded":{}}
    if name in ("expired_lease_deopt","invalid_context_deopt","deopt_only"): return {"latest_ready":{"locomotion":"deopt"},"authority_guarded":{"locomotion":"deopt"}}
    if name=="nonoverlap_resources": return {"latest_ready":{"fire":"threat","locomotion":"deopt"},"authority_guarded":{"fire":"threat","locomotion":"deopt"}}
    if name=="threat_only": return {"latest_ready":{"locomotion":"threat"},"authority_guarded":{"locomotion":"threat"}}
    raise KeyError(name)

def simplify(out):
    return {r:p['source'] for r,p in sorted(out['selected'].items())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    plan_path=Path(a.plan); plan=json.loads(plan_path.read_text()); out_path=Path(a.out)
    if out_path.exists(): raise SystemExit('refuse existing output')
    rows=[]
    schedule=[(rep,s) for rep in range(plan['repetitions']) for s in plan['scenarios']]
    random.Random(plan['seed']).shuffle(schedule)
    for idx,(rep,scenario) in enumerate(schedule):
        proposals,leases=fixture(scenario); exp=expected(scenario)
        for policy_name,fn in (("latest_ready",latest_ready),("authority_guarded",authority_guarded)):
            res=fn(proposals,leases,int(plan['tick'])); simple=simplify(res)
            rows.append({
                "row_id":f"m{idx:02d}-{policy_name}","schedule_index":idx,"rep":rep,"scenario":scenario,"policy":policy_name,
                "proposals":proposals,"leases":leases,"selected":simple,"deferred":res['deferred'],
                "expected":exp[policy_name],"correct":simple==exp[policy_name]
            })
    result={"schema":"agent-interface/map01-threat-deopt-arbitration-result-v1","task":plan['task'],"plan_sha256":sha(plan_path),"rows":rows}
    out_path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({"rows":len(rows),"correct":sum(r['correct'] for r in rows)},sort_keys=True))
if __name__=='__main__': main()
