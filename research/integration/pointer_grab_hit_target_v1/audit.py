#!/usr/bin/env python3
import json,sys
from pathlib import Path
ARMS=('HIT_ONLY','HIT_GRAB_PROBE');STATES=('CLEAR','GRAB_BEFORE_CHECK','GRAB_AFTER_CHECK')
S=[]
for rep in range(3):
    order=ARMS if rep%2==0 else ARMS[::-1]
    for st in STATES:
        for arm in order:S.append({'arm':arm,'state':st,'rep':rep})
S += [{'arm':'NO_TASK_INPUT','state':'CLEAR','rep':0},{'arm':'NO_TASK_INPUT','state':'GRAB_BEFORE_CHECK','rep':0}]
def expected(c):
    a,s=c['arm'],c['state']
    if a=='NO_TASK_INPUT':return {'clicked':False,'typed':False,'a':'','foreign':0}
    if s=='CLEAR':return {'clicked':True,'typed':True,'a':'7','foreign':0}
    if s=='GRAB_BEFORE_CHECK' and a=='HIT_GRAB_PROBE':return {'clicked':False,'typed':False,'a':'','foreign':0}
    return {'clicked':True,'typed':False,'a':'','foreign':1}
def audit(root):
    root=Path(root);errors=[];checks=0;metrics=[]
    def c(ok,msg):
        nonlocal checks;checks+=1
        if not ok:errors.append(msg)
    files=sorted(root.glob('case-*.json'));c(len(files)==20,'denominator')
    for i,cfg in enumerate(S):
        try:r=json.loads((root/f'case-{i:02d}.json').read_text());x=expected(cfg);p=f'case{i}:'
        except Exception as e:errors.append(f'case{i}:load:{e}');continue
        c(r['cfg']['index']==i and all(r['cfg'][k]==cfg[k] for k in cfg),p+'schedule')
        c(r['app_exit']==0 and r['grabber_exit']==0 and r['app_stderr']=='' and r['grabber_stderr']=='',p+'exits')
        c(r['neutral'] is True,p+'neutral')
        c(r['leaf']==r['ready']['a_xid'],p+'hit_was_a')
        c(r['clicked'] is x['clicked'] and r['typed'] is x['typed'],p+'actions')
        c(r['final']['a']==x['a'] and r['final']['b']=='',p+'text_effect')
        c(r['grabber']['press']==x['foreign'] and r['grabber']['release']==x['foreign'],p+'foreign_effect')
        if cfg['arm']=='HIT_GRAB_PROBE':
            c(type(r['probe']) is int,p+'probe_type')
            if cfg['state']=='GRAB_BEFORE_CHECK':c(r['probe']!=0,p+'probe_refuses_existing_grab')
            else:c(r['probe']==0,p+'probe_success')
        metrics.append({'index':i,'arm':cfg['arm'],'state':cfg['state'],'clicked':r['clicked'],'typed':r['typed'],'foreign':r['grabber']['press'],'a':r['final']['a']})
    decision='PASS_POINTER_GRAB_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_HOLD'
    return {'decision':decision,'errors':errors,'checks':checks,'rows':metrics}
if __name__=='__main__':
    r=audit(sys.argv[1]);print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(bool(r['errors']))
