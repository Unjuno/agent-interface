#!/usr/bin/env python3
import json, sys
from pathlib import Path
ARMS=('FOCUS_ONLY','FOCUS_KEYBOARD_PROBE')
STATES=('CLEAR','GRAB_BEFORE_PROBE','GRAB_AFTER_PROBE')
S=[]
for rep in range(3):
    order=ARMS if rep%2==0 else ARMS[::-1]
    for state in STATES:
        for arm in order:S.append({'arm':arm,'state':state,'rep':rep})
S += [{'arm':'NO_TASK_INPUT','state':'CLEAR','rep':0},{'arm':'NO_TASK_INPUT','state':'GRAB_BEFORE_PROBE','rep':0}]
def expected(cfg):
    a,s=cfg['arm'],cfg['state']
    if a=='NO_TASK_INPUT': return dict(sent=False,a='',foreign=0)
    if s=='CLEAR': return dict(sent=True,a='7',foreign=0)
    if a=='FOCUS_KEYBOARD_PROBE' and s=='GRAB_BEFORE_PROBE': return dict(sent=False,a='',foreign=0)
    return dict(sent=True,a='',foreign=1)
def audit(root):
    root=Path(root); errors=[]; checks=0; summary=[]
    def c(ok,msg):
        nonlocal checks; checks+=1
        if not ok: errors.append(msg)
    files=sorted(root.glob('case-*.json')); c(len(files)==20,'denominator')
    for i,cfg in enumerate(S):
        p=f'case{i}:'
        try:r=json.loads((root/f'case-{i:02d}.json').read_text()); x=expected(cfg)
        except Exception as e: errors.append(p+'load:'+type(e).__name__); continue
        c(r['cfg']['index']==i and all(r['cfg'][k]==cfg[k] for k in cfg),p+'schedule')
        c(r['app_exit']==0 and r['grabber_exit']==0 and r['app_stderr']=='' and r['grabber_stderr']=='',p+'child_exit')
        c(r['pre']['focus']=='.a',p+'focus_basis')
        c(r['neutral'] is True,p+'neutral')
        c(r['sent'] is x['sent'],p+'sent')
        c(r['final']['a']==x['a'] and r['final']['b']=='',p+'text')
        c(r['grabber']['press']==x['foreign'] and r['grabber']['release']==x['foreign'],p+'foreign_count')
        c(len(r['grabber']['events'])==2*x['foreign'],p+'foreign_events')
        if x['foreign']:
            c([e['kind'] for e in r['grabber']['events']]==['press','release'],p+'foreign_order')
            c(all(type(e['detail']) is int and e['detail']==r['keycode'] for e in r['grabber']['events']),p+'foreign_keycode')
        if cfg['arm']=='FOCUS_KEYBOARD_PROBE':
            c(type(r['probe']) is int,p+'probe_type')
            if cfg['state']=='GRAB_BEFORE_PROBE': c(r['probe']!=0,p+'probe_refusal')
            else: c(r['probe']==0,p+'probe_success')
        if cfg['arm']=='NO_TASK_INPUT': c(r['keycode'] is None,p+'no_task_keycode')
        if x['a']=='7':
            c([e['kind'] for e in r['final']['keys']]==['press','release'],p+'app_key_events')
            c(all(e['target']=='a' and e['keysym']=='7' for e in r['final']['keys']),p+'app_key_identity')
        else: c(r['final']['keys']==[],p+'no_app_key_event')
        summary.append({'index':i,'arm':cfg['arm'],'state':cfg['state'],'sent':r['sent'],'a':r['final']['a'],
                        'foreign_press':r['grabber']['press'],'probe':r['probe'],'focus_basis':r['pre']['focus'],
                        'focus_after':r['final']['focus']})
    return {'decision':'PASS_KEYBOARD_GRAB_DELIVERY_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_HOLD',
            'errors':errors,'checks':checks,'rows':summary}
if __name__=='__main__':
    r=audit(sys.argv[1]); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(bool(r['errors']))
