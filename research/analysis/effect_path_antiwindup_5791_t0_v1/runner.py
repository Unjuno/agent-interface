#!/usr/bin/env python3
"""Finite synthetic event generator for Issue #5791; emits canonical raw JSON."""
import hashlib, json
from pathlib import Path
f=Path('/work/fixture.json'); fx=json.loads(f.read_text())

def simulate(case, policy):
    k=case['kind']; actions=[]; effects=[]; state={'unknown':False,'stale_generation_effects':0,'cancel_latency':None}
    if k=='integrator':
        if policy=='unrestricted_accumulation':
            actions=[{'tick':t,'goal_generation':1,'correction':1,'reason':'error_integrated_while_blocked'} for t in case['blocked_ticks']]
            effects=[{'tick':case['release_tick'],'generation':1,'delta':sum(a['correction'] for a in actions)}]
        elif policy=='transport_ack_queue_cap':
            actions=[{'tick':0,'goal_generation':1,'correction':1,'reason':'single_queued_correction'}]
            effects=[{'tick':case['release_tick'],'generation':1,'delta':1}]
        else:
            actions=[{'tick':case['release_tick'],'goal_generation':1,'correction':1,'reason':'fresh_error_after_unblock'}]
            effects=[{'tick':case['release_tick']+case['effect_delay'],'generation':1,'delta':1}]
    elif k=='ambiguous_effect':
        if policy=='unrestricted_accumulation':
            actions=[{'tick':t,'goal_generation':1,'correction':1,'reason':'retry_without_semantic_receipt'} for t in range(case['transport_ack_tick']+1)]
            effects=[{'tick':case['effect_tick'],'generation':1,'delta':case['effect']},{'tick':case['effect_tick']+1,'generation':1,'delta':case['effect']}]
        elif policy=='transport_ack_queue_cap':
            actions=[{'tick':case['dispatch_tick'],'goal_generation':1,'correction':1,'reason':'dispatch'}, {'tick':case['transport_ack_tick'],'goal_generation':1,'correction':1,'reason':'slot_freed_on_transport_ack'}]
            effects=[{'tick':case['effect_tick'],'generation':1,'delta':case['effect']},{'tick':case['effect_tick']+1,'generation':1,'delta':case['effect']}]
        else:
            actions=[{'tick':case['dispatch_tick'],'goal_generation':1,'correction':1,'reason':'dispatch'}]
            effects=[{'tick':case['effect_tick'],'generation':1,'delta':case['effect']}]
            state['unknown']=True
    elif k=='no_integrator':
        actions=[{'tick':t,'goal_generation':1,'correction':1,'reason':'fresh_error_feedback'} for t in case['effect_ticks']]
        effects=[{'tick':t,'generation':1,'delta':case['effect_per_command']} for t in case['effect_ticks']]
    elif k=='goal_change':
        if policy=='unrestricted_accumulation':
            actions=[{'tick':t,'goal_generation':1,'correction':1,'reason':'old_goal_integrated'} for t in case['blocked_ticks']]
            effects=[{'tick':case['release_tick'],'generation':1,'delta':len(actions)}]
            state['stale_generation_effects']=len(actions)
        elif policy=='transport_ack_queue_cap':
            actions=[{'tick':0,'goal_generation':1,'correction':1,'reason':'old_goal_pending'}]
            effects=[{'tick':case['release_tick'],'generation':1,'delta':1}]
            state['stale_generation_effects']=1
        else:
            actions=[{'tick':case['release_tick'],'goal_generation':2,'correction':0,'reason':'recompute_new_goal'}]
            effects=[]
    elif k=='safety_cancel':
        actions=[{'tick':case['cancel_tick'],'goal_generation':1,'correction':0,'reason':'mandatory_cancel_bypass','critical':True}]
        state['cancel_latency']=0
    achieved=sum(e['delta'] for e in effects)
    target=case.get('new_target',case.get('target',0))
    overshoot=max(0,achieved-target) if target>=0 else max(0,target-achieved)
    duplicate_effects=max(0,len(effects)-1) if k!='safety_cancel' else 0
    return {'case_id':case['id'],'policy':policy,'actions':actions,'effects':effects,'achieved':achieved,'target':target,'final_error':abs(target-achieved),'overshoot':overshoot,'duplicate_effects':duplicate_effects,**state}

rows=[simulate(c,p) for c in fx['cases'] for p in fx['policies']]
print(json.dumps({'schema':'effect-path-antiwindup-raw-v1','fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'rows':rows},sort_keys=True,separators=(',',':')))

