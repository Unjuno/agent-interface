#!/usr/bin/env python3
"""Independent oracle for the frozen finite ledger; candidate code is not imported."""
import hashlib,json
from pathlib import Path
f=Path('/work/fixture.json'); fx=json.loads(f.read_text()); raw=json.loads(Path('/work/raw.json').read_text())
assert raw['schema']=='effect-path-antiwindup-raw-v1'
assert raw['fixture_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
assert len(raw['rows'])==len(fx['cases'])*len(fx['policies'])
expected={
('integrator_saturation_release','unrestricted_accumulation'):(4,3,0,False,0),
('integrator_saturation_release','transport_ack_queue_cap'):(1,0,0,False,0),
('integrator_saturation_release','receipt_aware_antiwindup'):(1,0,0,False,0),
('transport_ack_before_effect','unrestricted_accumulation'):(2,1,1,False,0),
('transport_ack_before_effect','transport_ack_queue_cap'):(2,1,1,False,0),
('transport_ack_before_effect','receipt_aware_antiwindup'):(1,0,0,True,0),
('no_integrator_state','unrestricted_accumulation'):(2,0,0,False,0),
('no_integrator_state','transport_ack_queue_cap'):(2,0,0,False,0),
('no_integrator_state','receipt_aware_antiwindup'):(2,0,0,False,0),
('goal_generation_changes_while_blocked','unrestricted_accumulation'):(3,3,3,False,0),
('goal_generation_changes_while_blocked','transport_ack_queue_cap'):(1,1,1,False,0),
('goal_generation_changes_while_blocked','receipt_aware_antiwindup'):(0,0,0,False,0),
('mandatory_cancel_bypasses_gate','unrestricted_accumulation'):(0,0,0,False,0),
('mandatory_cancel_bypasses_gate','transport_ack_queue_cap'):(0,0,0,False,0),
('mandatory_cancel_bypasses_gate','receipt_aware_antiwindup'):(0,0,0,False,0),
}
seen=set(); errors=[]
for r in raw['rows']:
    key=(r['case_id'],r['policy']); assert key not in seen; seen.add(key)
    if key not in expected: errors.append([key,'unexpected']) ; continue
    achieved,overshoot,dups,unknown,stale=expected[key]
    if (r['achieved'],r['overshoot'],r['final_error'],r['duplicate_effects'],r['unknown'],r['stale_generation_effects'])!=(achieved,overshoot,abs(r['target']-achieved),dups,unknown,stale): errors.append([key,'metrics'])
    if key[0]=='mandatory_cancel_bypasses_gate' and r['cancel_latency']!=0: errors.append([key,'cancel_latency'])
    if key[0]=='transport_ack_before_effect' and key[1]=='receipt_aware_antiwindup' and any(e['tick']<3 for e in r['effects']): errors.append([key,'effect_before_oracle'])
    if key[0]=='integrator_saturation_release':
        want=4 if key[1]=='unrestricted_accumulation' else 1
        if sum(a['correction'] for a in r['actions'])!=want: errors.append([key,'integrated_command_count'])
    if key[0]=='no_integrator_state':
        if [a['tick'] for a in r['actions']]!=[2,4] or [e['tick'] for e in r['effects']]!=[2,4]: errors.append([key,'negative_control_schedule'])
    if key[0]=='goal_generation_changes_while_blocked' and key[1]=='receipt_aware_antiwindup':
        if any(a['goal_generation']!=2 or a['correction']!=0 for a in r['actions']): errors.append([key,'stale_generation_command'])
    if key[0]=='mandatory_cancel_bypasses_gate':
        if len(r['actions'])!=1 or r['actions'][0].get('critical') is not True or r['actions'][0]['reason']!='mandatory_cancel_bypass' or r['actions'][0]['tick']!=1: errors.append([key,'cancel_not_bypassed'])
assert seen==set(expected), 'missing case/policy pair'
assert not errors,json.dumps(errors)
neg=[r for r in raw['rows'] if r['case_id']=='no_integrator_state']
assert len({(r['achieved'],r['overshoot'],r['duplicate_effects'],r['unknown']) for r in neg})==1, 'anti-windup changed the no-integrator negative control'
summary={}
for r in raw['rows']:
    x=summary.setdefault(r['case_id'],{})
    x[r['policy']]={'overshoot':r['overshoot'],'final_error':r['final_error'],'duplicate_effects':r['duplicate_effects'],'unknown':r['unknown'],'stale_generation_effects':r['stale_generation_effects'],'cancel_latency':r['cancel_latency']}
print(json.dumps({'audit':'PASS_METHOD_SCOPED','rows':len(seen),'errors':0,'summary':summary},sort_keys=True,separators=(',',':')))

