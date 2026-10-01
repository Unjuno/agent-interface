#!/usr/bin/env python3
"""Issue #5791 v2 finite candidate ledger; no real interface is exercised."""
import hashlib,json
from pathlib import Path
f=Path('/work/fixture.json'); fx=json.loads(f.read_text())

def run(c,p):
    k=c['kind']; actions=[]; effects=[]; unknown=False; stale=0; cancelled=0; cancel_latency=None
    if k=='integrator':
        if p=='unrestricted_accumulation':
            actions=[{'tick':t,'generation':1,'correction':1} for t in c['blocked_ticks']]
            effects=[{'tick':c['release_tick'],'generation':1,'delta':len(actions)}]
        elif p=='semantic_receipt_queue_cap':
            actions=[{'tick':c['blocked_ticks'][0],'generation':1,'correction':1}]
            effects=[{'tick':c['release_tick'],'generation':1,'delta':1}]
        else:
            actions=[{'tick':c['release_tick'],'generation':1,'correction':1,'fresh_observation':True}]
            effects=[{'tick':c['release_tick']+c['effect_delay'],'generation':1,'delta':1}]
    elif k=='ambiguous_effect':
        if p=='unrestricted_accumulation':
            actions=[{'tick':t,'generation':1,'correction':1} for t in [c['dispatch_tick'],c['transport_ack_tick']]]
            effects=[{'tick':c['effect_tick'],'generation':1,'delta':c['effect']},{'tick':c['effect_tick']+1,'generation':1,'delta':c['effect']}]
        else:
            actions=[{'tick':c['dispatch_tick'],'generation':1,'correction':1,'hold_until_semantic_receipt':True}]
            effects=[{'tick':c['effect_tick'],'generation':1,'delta':c['effect']}]
        unknown=True
    elif k=='no_integrator':
        actions=[{'tick':t,'generation':1,'correction':1,'fresh_observation':True} for t in c['effect_ticks']]
        effects=[{'tick':t,'generation':1,'delta':c['effect_per_command']} for t in c['effect_ticks']]
    elif k=='goal_change':
        if p=='unrestricted_accumulation':
            actions=[{'tick':t,'generation':1,'correction':1} for t in c['blocked_ticks']]
        elif p=='semantic_receipt_queue_cap':
            actions=[{'tick':c['blocked_ticks'][0],'generation':1,'correction':1}]
        else:
            actions=[{'tick':c['release_tick'],'generation':2,'correction':0,'fresh_observation':True}]
        cancelled=sum(a['generation']==1 for a in actions)
        # Mandatory generation invalidation cancels all old-goal queued corrections.
        effects=[]
    elif k=='safety_cancel':
        actions=[{'tick':c['cancel_tick'],'generation':1,'correction':0,'critical':True}]
        cancel_latency=c['cancel_latency_ticks']
    target=c.get('new_target',c.get('target',0)); achieved=sum(e['delta'] for e in effects)
    overshoot=max(0,achieved-target) if target>=0 else max(0,target-achieved)
    duplicate_effects=(len(effects)-1) if k=='ambiguous_effect' and len(effects)>1 else 0
    return {'case_id':c['id'],'policy':p,'actions':actions,'effects':effects,'achieved':achieved,'target':target,'final_error':abs(target-achieved),'overshoot':overshoot,'duplicate_effects':duplicate_effects,'unknown':unknown,'stale_generation_effects':stale,'cancelled_old_generation':cancelled,'cancel_latency':cancel_latency}

rows=[run(c,p) for c in fx['cases'] for p in fx['policies']]
print(json.dumps({'schema':'effect-path-antiwindup-raw-v2','fixture_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'rows':rows},sort_keys=True,separators=(',',':')))
