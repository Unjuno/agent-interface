#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
POLICIES={'EXISTING_CURRENTNESS_ONLY','EXPLICIT_DECISION_DEADLINE'}
SCENARIOS={'ON_TIME','NEAR_BEFORE','NEAR_AFTER','WELL_AFTER'}

def strict_int(x): return isinstance(x,int) and not isinstance(x,bool)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def audit(raw_path, root=HERE):
    errors=[]; checks=0
    raw=json.loads(Path(raw_path).read_text()); rows=raw.get('rows',[])
    checks+=1
    if len(rows)!=24: errors.append('case_count')
    ids=[r.get('case_id') for r in rows]; checks+=1
    if len(set(ids))!=len(ids): errors.append('duplicate_case')
    counts={}
    stale_accepts=0
    for r in rows:
        cid=r.get('case_id','?'); checks+=1
        p=r.get('policy'); s=r.get('scenario'); counts[(p,s)]=counts.get((p,s),0)+1
        if p not in POLICIES or s not in SCENARIOS: errors.append(f'{cid}:identity')
        for k in ['proposal_ready_ns','requested_delay_ns','actual_ready_delay_ns','policy_exit','app_exit']:
            checks+=1
            if not strict_int(r.get(k)): errors.append(f'{cid}:{k}_type')
        checks+=2
        if r.get('policy_exit')!=0: errors.append(f'{cid}:policy_exit')
        if r.get('app_exit')!=0: errors.append(f'{cid}:app_exit')
        if r.get('policy_stderr')!='' or r.get('app_stderr')!='': errors.append(f'{cid}:stderr')
        obs=r.get('observation',{}); pkt=r.get('packet',{}); dec=r.get('decision',{}); eff=r.get('effect')
        for k in ['observation_available_ns','decision_deadline_ns','lease_valid_until_ns','freshness_budget_ns']:
            checks+=1
            if not strict_int(obs.get(k)): errors.append(f'{cid}:obs_{k}')
        ready=r.get('proposal_ready_ns'); deadline=obs.get('decision_deadline_ns'); lease=obs.get('lease_valid_until_ns'); budget=obs.get('freshness_budget_ns'); start=obs.get('observation_available_ns')
        if all(strict_int(x) for x in [ready,deadline,lease,budget,start]):
            current_ok = ready<=lease and ready-start<=budget
            sem_ready = ready<=deadline
            checks+=3
            if not current_ok: errors.append(f'{cid}:currentness_not_held')
            expected='ADMIT' if (p=='EXISTING_CURRENTNESS_ONLY' or sem_ready) else 'REFUSE_DECISION_DEADLINE'
            if dec.get('decision')!=expected: errors.append(f'{cid}:decision')
            if dec.get('authority') is not False: errors.append(f'{cid}:authority')
            if expected=='ADMIT':
                checks+=3
                if not isinstance(eff,dict): errors.append(f'{cid}:missing_effect')
                else:
                    if eff.get('effect_count')!=1: errors.append(f'{cid}:effect_count')
                    recv=eff.get('received_ns');
                    if not strict_int(recv): errors.append(f'{cid}:effect_time')
                    else:
                        app_sem=recv<=deadline
                        if eff.get('semantic_valid') is not app_sem: errors.append(f'{cid}:semantic_flag')
                        if not app_sem and p=='EXISTING_CURRENTNESS_ONLY': stale_accepts+=1
                if r.get('closed',{}).get('effect_count')!=1: errors.append(f'{cid}:closed_count')
            else:
                checks+=2
                if eff is not None: errors.append(f'{cid}:effect_on_refusal')
                if r.get('closed',{}).get('effect_count')!=0: errors.append(f'{cid}:closed_refusal_count')
    for p in POLICIES:
        for s in SCENARIOS:
            checks+=1
            if counts.get((p,s))!=3: errors.append(f'coverage:{p}:{s}')
    # Decision gates: on-time/near-before effects valid in both arms; late A admits invalid; late B refuses.
    for r in rows:
        s=r['scenario']; p=r['policy']; d=r['decision']['decision']; eff=r['effect']; checks+=1
        if s in {'ON_TIME','NEAR_BEFORE'}:
            if d!='ADMIT' or not eff or eff.get('semantic_valid') is not True: errors.append(f"{r['case_id']}:valid_rejected_or_late")
        else:
            if p=='EXISTING_CURRENTNESS_ONLY':
                if d!='ADMIT' or not eff or eff.get('semantic_valid') is not False: errors.append(f"{r['case_id']}:late_not_exposed")
            else:
                if d!='REFUSE_DECISION_DEADLINE' or eff is not None: errors.append(f"{r['case_id']}:deadline_escape")
    checks+=1
    if stale_accepts<1: errors.append('no_stale_acceptance_witness')
    status='PASS_DEADLINE_VALIDITY_SCOPED' if not errors else 'FAIL_AUDIT'
    return {'status':status,'cases':len(rows),'checks':checks,'errors':errors,'stale_acceptance_witnesses':stale_accepts}

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: audit.py RAW.json')
    result=audit(sys.argv[1]); print(json.dumps(result,sort_keys=True,indent=2)); raise SystemExit(0 if not result['errors'] else 1)
if __name__=='__main__': main()
