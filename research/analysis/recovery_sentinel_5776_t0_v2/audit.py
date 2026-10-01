#!/usr/bin/env python3
"""Independent exact event-ledger replay; does not import candidate code."""
import hashlib,json
from pathlib import Path
f=Path('/work/fixtures.json'); fx=json.loads(f.read_text()); raw=json.loads(Path('/work/raw.json').read_text())
assert raw['schema']=='recovery-sentinel-raw-v2'
assert raw['fixture_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
assert len(raw['episodes'])==len(fx['loads'])*len(fx['mechanisms'])*fx['episodes_per_load']
seen=set(); rows=0; mismatch=[]
for e in raw['episodes']:
    assert e['episode_id'] not in seen; seen.add(e['episode_id'])
    ev=e['events']; assert len(ev)==fx['horizon_ticks']
    b=0; rec=[]; pending=None; probe=0
    for t,x in enumerate(ev):
        assert x['tick']==t
        if x['disturbance']: probe+=1
        expected=max(0,b+x['demand']+x['injected_delay']+x['breaker_jump']+x['spontaneous_jump']-x['service'])
        if x['backlog_before']!=b or x['backlog']!=expected: mismatch.append([e['episode_id'],t,'state'])
        b=expected; env=b<=fx['return_envelope_backlog_max']
        if x['in_envelope']!=env: mismatch.append([e['episode_id'],t,'envelope'])
        if x['disturbance']: pending={'probe':probe,'start':t,'delay':x['injected_delay']}
        elif pending is not None and env:
            rec.append({'probe':pending['probe'],'start':pending['start'],'tick':t,'recovery_ticks':t-pending['start'],'delay':pending['delay']}); pending=None
        rows+=1
    if rec!=e['returns']: mismatch.append([e['episode_id'],'return'])
    ds=[x['recovery_ticks'] for x in rec]; ratio=ds[-1]/ds[0] if len(ds)>=2 and ds[0] else 1.0
    warn=ratio>=fx['warning']['threshold_slowdown_ratio']
    if ratio!=e['slowdown_ratio'] or warn!=e['warning']: mismatch.append([e['episode_id'],'stat'])
    losses=[x['tick'] for x in ev if x['breaker_jump'] or x['spontaneous_jump']]
    if losses!=e['loss_ticks']: mismatch.append([e['episode_id'],'loss'])
    expected_probes=fx['disturbance']['start_ticks']
    if [x['tick'] for x in ev if x['disturbance']]!=expected_probes: mismatch.append([e['episode_id'],'schedule'])
assert not mismatch,json.dumps(mismatch[:10])
groups={}
for e in raw['episodes']:
    g=groups.setdefault(e['load']+':'+e['mechanism'],{'episodes':0,'warnings':0,'loss_episodes':0})
    g['episodes']+=1;g['warnings']+=int(e['warning']);g['loss_episodes']+=int(bool(e['loss_ticks']))
print(json.dumps({'audit':'PASS_EVENT_REPLAY_SCOPED','episodes':len(seen),'event_rows':rows,'mismatches':0,'groups':groups},sort_keys=True,separators=(',',':')))

