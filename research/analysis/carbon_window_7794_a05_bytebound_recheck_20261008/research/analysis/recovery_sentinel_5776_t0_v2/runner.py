#!/usr/bin/env python3
"""V2 synthetic recovery ledger; all state-changing inputs are explicit events."""
import hashlib, json
from pathlib import Path
F=Path('/work/fixtures.json'); fx=json.loads(F.read_text())

def make(load, mech, i):
    base={'low':5,'near':4,'high':3}[load]
    svc=base; backlog=0; rows=[]; returns=[]; pending=None; probe=0; loss=[]
    for t in range(fx['horizon_ticks']):
        demand=2 if mech=='demand_drift' and t>=52 else 1
        disturbance=t in fx['disturbance']['start_ticks']
        delay=fx['disturbance']['delay_ticks'] if disturbance else 0
        if mech=='variable_disturbance' and disturbance and probe%2: delay=1
        if disturbance: probe+=1
        if mech=='gradual_recovery' and disturbance and load=='high': svc+=1
        if mech=='gradual_recovery' and disturbance and load=='near' and probe>=3: svc+=1
        breaker_jump=9 if mech=='abrupt_breaker' and load=='high' and t==64 else 0
        spontaneous_jump=9 if mech=='spontaneous_failure' and load=='high' and t==67 else 0
        before=backlog
        backlog=max(0,backlog+demand+delay+breaker_jump+spontaneous_jump-svc)
        if breaker_jump or spontaneous_jump: loss.append(t)
        in_env=backlog<=fx['return_envelope_backlog_max']
        if disturbance: pending={'probe':probe,'start':t,'delay':delay}
        elif pending is not None and in_env:
            returns.append({'probe':pending['probe'],'start':pending['start'],'tick':t,
                            'recovery_ticks':t-pending['start'],'delay':pending['delay']})
            pending=None
        rows.append({'tick':t,'demand':demand,'service':svc,'disturbance':disturbance,
                     'injected_delay':delay,'breaker_jump':breaker_jump,
                     'spontaneous_jump':spontaneous_jump,'backlog_before':before,
                     'backlog':backlog,'in_envelope':in_env})
    durations=[r['recovery_ticks'] for r in returns]
    ratio=durations[-1]/durations[0] if len(durations)>=2 and durations[0] else 1.0
    warn=ratio>=fx['warning']['threshold_slowdown_ratio']
    return {'episode_id':f'{load}-{mech}-{i:02d}','load':load,'mechanism':mech,
            'events':rows,'returns':returns,'loss_ticks':loss,'slowdown_ratio':ratio,'warning':warn}

episodes=[make(l,m,i) for l in fx['loads'] for m in fx['mechanisms'] for i in range(fx['episodes_per_load'])]
print(json.dumps({'schema':'recovery-sentinel-raw-v2','fixture_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'episodes':episodes},sort_keys=True,separators=(',',':')))

