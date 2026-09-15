#!/usr/bin/env python3
"""Independent retained-evidence auditor; never imports the controller."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sqlite3


def read(path): return json.loads(Path(path).read_text())
def require(condition, message):
    if not condition: raise AssertionError(message)
def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',', ':'),allow_nan=False)
def log(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()] if Path(path).exists() else []
def table(path, name, key=None):
    db=sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    try:
        if key is None: return [dict(x) for x in db.execute('SELECT * FROM '+name)]
        return [dict(x) for x in db.execute('SELECT * FROM '+name+' WHERE command_id=? ORDER BY seq',(key,))]
    finally: db.close()

def expected(job, after_recovery):
    arm,s=job['arm'],job['scenario']
    if s=='invalid_before_validation': return 0,0
    if s=='pre_commit_exit': return 0,1 if arm=='inline' else 0
    if s=='post_receive_exit':
        if arm=='inline': return 0,1
        return 1,(1 if not after_recovery or job['receiver_dedup'] else 2)
    if s=='post_commit_exit' and arm=='outbox' and not after_recovery: return 1,0
    return 1,1

def check_case(job, initial, final, exit_codes, events, receipt):
    for snapshot, recovered in [(initial,False),(final,True)]:
        lc,rc=expected(job,recovered)
        require(len(snapshot['local']['commands'])==lc,'local command count')
        require(len(snapshot['remote']['effects'])==rc,'receiver effect count')
        for t in ('commands','outbox'):
            for row in snapshot['local'][t]:
                require(row['command_id']==job['id'] and row['payload']==canonical(job['payload']),'payload or identity binding')
        for row in snapshot['remote']['effects']:
            require(row['command_id']==job['id'] and row['payload']==canonical(job['payload']),'remote payload binding')
        require(len(snapshot['local']['outbox'])==(lc if job['arm']=='outbox' else 0),'outbox count')
    s=job['scenario']
    crash=s.endswith('_exit')
    require(exit_codes=={'initial':73 if crash else 0,'recovery':0},'process exits')
    require((receipt is None)==crash,'crash terminal must be absent')
    if receipt is not None:
        expected_outcome='SAFE_YIELD' if s=='invalid_before_validation' else 'TASK_SUCCEEDED'
        require(receipt['outcome']==expected_outcome,'runtime outcome')
        require(receipt['frontier_model_resumptions']==0,'model calls')
        require(receipt['input_authority']=='admission_per_action_only','authority semantics')
        for transition in receipt['transitions']:
            require(transition['release_verified'] is True,'simulated release contract')
    require(len([r for r in events if r['event']=='admission'])==1,'admission count')
    for i,r in enumerate(events):
        if i: require(r['ns']>=events[i-1]['ns'],'monotonic events')
        if r['event']=='observation':
            observed=r['observation']
            correct=hashlib.sha256(canonical({'state':r['state'],'predicates':observed['predicates']}).encode()).hexdigest()
            require(correct==observed['evidence_digest'],'canonical digest')
    admissions=[r for r in events if r['event']=='admission']
    require(admissions[0]['eligible']==(s!='invalid_before_validation'),'final validity')
    if crash:
        require(events[-1]['event']=='injected_exit','crash marker')
    if s=='post_receive_exit':
        acks=[r for r in events if r['event']=='receiver_ack_observed']
        require(len(acks)==1,'crash follows receiver ack')
        require(initial['remote']['effects'][0]['committed_ns']<=acks[0]['ns']<events[-1]['ns'],'receiver/crash order')
    if s=='invalid_before_validation':
        require(not initial['remote']['requests'],'invalid plan sent externally')
    return True

def run(root):
    root=Path(root)
    cases=sorted(root.glob('case-*'))
    schedule=read(root/'schedule.json')
    require(len(cases)==len(schedule),'schedule completeness')
    require(read(root/'run_status.json')['status']=='COMPLETED','completed status')
    summary={'cases':len(cases),'arms':{},'corruption_checks':{}}
    normal=[]
    for case in cases:
        job=read(case/'job.json'); ini=read(case/'after_initial.json'); fin=read(case/'after_recovery.json')
        events=log(case/'initial_events.jsonl')
        receipt=read(case/'runtime_receipt.json') if (case/'runtime_receipt.json').exists() else None
        args=[job,ini,fin,read(case/'exit.json'),events,receipt]
        check_case(*args); normal.append(args)
        for name in ('state','commands','outbox','acknowledgements'):
            require(fin['local'][name]==table(case/'local.sqlite',name),'local retained database mismatch: '+name)
        for name in ('effects','requests'):
            require(fin['remote'][name]==table(root/'receiver.sqlite',name,job['id']),'receiver database mismatch: '+name)
        recovered=read(case/'recovery_receipt.json')
        pending=sum(not x['delivered'] for x in ini['local']['outbox'])
        require(recovered=={'pending_before':pending,'dispatched':pending},'bounded recovery work')
        if pending:
            require(all(x['delivered']==1 for x in fin['local']['outbox']),'outbox not acknowledged')
        counts=summary['arms'].setdefault(job['arm'], {'cases':0,'orphan_effects_before_recovery':0,
            'orphan_effects_after_recovery':0,'duplicate_effects_after_recovery':0,
            'committed_missing_before_recovery':0,'committed_missing_after_recovery':0,
            'invalid_plan_effects':0,'terminal_absent':0,'per_scenario':{}})
        lc=len(fin['local']['commands']); rc=len(fin['remote']['effects'])
        li=len(ini['local']['commands']); ri=len(ini['remote']['effects'])
        counts['cases']+=1
        counts['orphan_effects_before_recovery']+=ri if not li else 0
        counts['orphan_effects_after_recovery']+=rc if not lc else 0
        counts['duplicate_effects_after_recovery']+=max(0,rc-1) if lc else 0
        counts['committed_missing_before_recovery']+=int(li==1 and ri==0)
        counts['committed_missing_after_recovery']+=int(lc==1 and rc==0)
        counts['invalid_plan_effects']+=rc if job['scenario']=='invalid_before_validation' else 0
        counts['terminal_absent']+=int(receipt is None)
        sc=counts['per_scenario'].setdefault(job['scenario'],{'cases':0,'local_after':0,'remote_before':0,'remote_after':0})
        sc['cases']+=1;sc['local_after']+=lc;sc['remote_before']+=ri;sc['remote_after']+=rc
    base=next(x for x in normal if x[0]['scenario']=='stable')
    for kind in ('remote_effect_deleted','local_command_deleted','digest_corruption','exit_corruption','payload_corruption'):
        damaged=copy.deepcopy(base)
        if kind=='remote_effect_deleted': damaged[2]['remote']['effects']=[]
        elif kind=='local_command_deleted': damaged[2]['local']['commands']=[]
        elif kind=='digest_corruption':
            next(x for x in damaged[4] if x['event']=='observation')['observation']['evidence_digest']='0'*64
        elif kind=='exit_corruption': damaged[3]['initial']=73
        else: damaged[2]['remote']['effects'][0]['payload']='{}'
        rejected=False
        try: check_case(*damaged)
        except AssertionError: rejected=True
        require(rejected,'corruption escaped: '+kind)
        summary['corruption_checks'][kind]='REJECTED'
    summary['audit']='PASS'
    (root/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');run(p.parse_args().root)
