#!/usr/bin/env python3
"""Independent oracle for v2; does not import candidate implementation."""
import hashlib,json
from pathlib import Path
f=Path('/work/fixture.json'); fx=json.loads(f.read_text()); raw=json.loads(Path('/work/raw.json').read_text())
assert raw['schema']=='effect-path-antiwindup-raw-v2'
assert raw['fixture_sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
assert len(raw['rows'])==15
expected={
('integrator_saturation_release','unrestricted_accumulation'):(4,3,0,0,False,0),
('integrator_saturation_release','semantic_receipt_queue_cap'):(1,0,0,0,False,0),
('integrator_saturation_release','receipt_aware_antiwindup'):(1,0,0,0,False,0),
('transport_ack_before_effect','unrestricted_accumulation'):(2,1,1,0,True,0),
('transport_ack_before_effect','semantic_receipt_queue_cap'):(1,0,0,0,True,0),
('transport_ack_before_effect','receipt_aware_antiwindup'):(1,0,0,0,True,0),
('no_integrator_state','unrestricted_accumulation'):(2,0,0,0,False,0),
('no_integrator_state','semantic_receipt_queue_cap'):(2,0,0,0,False,0),
('no_integrator_state','receipt_aware_antiwindup'):(2,0,0,0,False,0),
('goal_generation_changes_while_blocked','unrestricted_accumulation'):(0,0,0,3,False,0),
('goal_generation_changes_while_blocked','semantic_receipt_queue_cap'):(0,0,0,1,False,0),
('goal_generation_changes_while_blocked','receipt_aware_antiwindup'):(0,0,0,0,False,0),
('mandatory_cancel_bypasses_gate','unrestricted_accumulation'):(0,0,0,0,False,0),
('mandatory_cancel_bypasses_gate','semantic_receipt_queue_cap'):(0,0,0,0,False,0),
('mandatory_cancel_bypasses_gate','receipt_aware_antiwindup'):(0,0,0,0,False,0)}
seen=set(); failures=[]
for r in raw['rows']:
    key=(r['case_id'],r['policy']); assert key not in seen; seen.add(key)
    assert key in expected,key
    achieved,over,dups,cancelled,unknown,stale=expected[key]
    if (r['achieved'],r['overshoot'],r['final_error'],r['duplicate_effects'],r['cancelled_old_generation'],r['unknown'],r['stale_generation_effects'])!=(achieved,over,abs(r['target']-achieved),dups,cancelled,unknown,stale): failures.append([key,'metric'])
    if key[0]=='integrator_saturation_release' and key[1]=='unrestricted_accumulation' and len(r['actions'])!=4: failures.append([key,'accumulation'])
    if key[0]=='transport_ack_before_effect' and key[1]=='unrestricted_accumulation' and len(r['effects'])!=2: failures.append([key,'duplicate_effect'])
    if key[0]=='transport_ack_before_effect' and key[1]!='unrestricted_accumulation' and (len(r['actions'])!=1 or r['actions'][0].get('hold_until_semantic_receipt') is not True): failures.append([key,'receipt_hold'])
    if key[0]=='no_integrator_state' and ([a['tick'] for a in r['actions']]!=[2,4] or [e['tick'] for e in r['effects']]!=[2,4]): failures.append([key,'fresh_feedback_control'])
    if key[0]=='goal_generation_changes_while_blocked' and r['effects']: failures.append([key,'old_generation_effect'])
    if key[0]=='mandatory_cancel_bypasses_gate' and (len(r['actions'])!=1 or r['actions'][0].get('critical') is not True or r['cancel_latency']!=0): failures.append([key,'cancel_gate'])
assert seen==set(expected)
assert not failures,json.dumps(failures)
neg=[r for r in raw['rows'] if r['case_id']=='no_integrator_state']
assert len({(r['achieved'],r['overshoot'],r['final_error'],r['duplicate_effects']) for r in neg})==1
summary={}
for r in raw['rows']:
    summary.setdefault(r['case_id'],{})[r['policy']]={'overshoot':r['overshoot'],'final_error':r['final_error'],'duplicates':r['duplicate_effects'],'unknown':r['unknown'],'old_generation_cancelled':r['cancelled_old_generation'],'cancel_latency':r['cancel_latency']}
print(json.dumps({'audit':'PASS_EVENT_ORACLE_SCOPED','rows':len(seen),'errors':0,'summary':summary},sort_keys=True,separators=(',',':')))
