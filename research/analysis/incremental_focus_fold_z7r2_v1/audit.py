"""Read-only independent prefix oracle. Imports no study implementation.

It validates the whole prefix, then selects the last valid focus/map basis
and the last target edge. This is not the candidate's incremental recurrence.
"""
import json,hashlib,statistics,sys
from pathlib import Path
class AuditError(Exception):pass

def digest(b):return hashlib.sha256(b).hexdigest()
def compact(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def integer(x,a=0,b=2**63-1):return type(x)is int and a<=x<=b
def bits(x):
    if type(x)is not str or len(x)!=64 or any(c not in '0123456789abcdef' for c in x):raise ValueError()
    return bytes.fromhex(x)
def valid_answer(a):
    return type(a)is dict and set(a)=={'status','shift_down','authority','input_dispatched'} and type(a['status'])is str and a['status'] in ('TYPE','WAIT','UNKNOWN') and (a['shift_down'] is None or type(a['shift_down'])is bool) and type(a['authority'])is str and a['authority']=='none' and a['input_dispatched'] is False
def answer(state):return dict(status='UNKNOWN' if state is None else ('WAIT' if state else 'TYPE'),shift_down=state,authority='none',input_dispatched=False)

def oracle(context,events,mode):
    try:
        if type(context)is not dict or set(context)!={'epoch','expected_epoch','window','keycode','seed_keymap','seed_focused','first_ordinal','coverage_complete'}:return answer(None)
        if mode not in ('KEY_EDGES','FOCUS_KEYMAP') or type(events)is not list:return answer(None)
        if type(context['epoch'])is not str or not context['epoch'] or context['epoch']!=context['expected_epoch']:return answer(None)
        if not integer(context['window'],1) or not integer(context['keycode'],8,255) or not integer(context['first_ordinal']):return answer(None)
        if context['seed_focused'] is not True or context['coverage_complete'] is not True:return answer(None)
        key=context['keycode'];seed=bits(context['seed_keymap']);state=bool(seed[key//8]&(1<<(key%8)))
        for i,e in enumerate(events):
            if type(e)is not dict or not integer(e.get('ordinal')) or e['ordinal']!=context['first_ordinal']+i or e.get('send_event') is not False or not integer(e.get('type')):return answer(None)
            t=e['type']
            if t in (2,3):
                if not integer(e.get('window'),1) or e['window']!=context['window'] or not integer(e.get('keycode'),8,255):return answer(None)
            elif t in (9,10):
                if not integer(e.get('window'),1) or e['window']!=context['window'] or not integer(e.get('mode'),0,3) or not integer(e.get('detail'),0,7):return answer(None)
            elif t==11:
                bits(e.get('keymap'))
                if mode=='FOCUS_KEYMAP' and (i==0 or events[i-1]['type']!=9 or events[i-1]['mode']!=0):return answer(None)
            else:return answer(None)
        start=0
        if mode=='FOCUS_KEYMAP':
            focus=[i for i,e in enumerate(events) if e['type'] in (9,10)]
            if focus:
                k=focus[-1]
                if events[k]['type']!=9 or events[k]['mode']!=0 or k+1==len(events) or events[k+1]['type']!=11:return answer(None)
                value=bits(events[k+1]['keymap']);state=bool(value[key//8]&(1<<(key%8)));start=k+2
        edges=[e for e in events[start:] if e['type'] in (2,3) and e['keycode']==key]
        if edges:state=(edges[-1]['type']==2)
        return answer(state)
    except (ValueError,KeyError,TypeError):return answer(None)

def audit_correctness(cases,rows):
    checks=0;decisions=0;counts={};statuses={};old_matches=0
    def ck(x,msg):
        nonlocal checks;checks+=1
        if not x:raise AuditError(msg)
    ck(len(rows)==len(cases),'case denominator')
    ck(len({c['id'] for c in cases})==len(cases),'case identity')
    for c,r in zip(cases,rows):
        counts[c['kind']]=counts.get(c['kind'],0)+1
        ck(r['id']==c['id'],'record order');ck(r['input_sha256']==digest(compact(c).encode()),'input binding')
        ck(r['input_unchanged'] is True,'input mutation')
        ck(set(r['outputs'])==set(c['partitions']),'partitions')
        for name,ends in c['partitions'].items():
            steps=r['outputs'][name];ck(len(steps)==len(ends),'endpoints')
            for end,row in zip(ends,steps):
                expected=oracle(c['context'],c['events'][:end],c['mode'])
                ck(type(row['end'])is int and row['end']==end,'cut identity')
                ck(valid_answer(row['candidate']) and row['candidate']==expected,'incremental oracle disagreement')
                ck(valid_answer(row['reference']) and row['reference']==expected,'reference oracle disagreement')
                ck(integer(row['visited']) and row['visited']<=end,'visit bound')
                decisions+=1;statuses[expected['status']]=statuses.get(expected['status'],0)+1
        if c['kind']=='retained':
            got=[x['candidate'] for x in r['outputs']['original_batches']][1:]
            ck(got==c['old_decisions'],'retained historical parity');old_matches+=len(got)
    return dict(checks=checks,cases=len(cases),decisions=decisions,families=counts,statuses=statuses,retained_decisions=old_matches)

def audit_benchmark(spec,inp,row):
    checks=0
    def ck(x,msg):
        nonlocal checks;checks+=1
        if not x:raise AuditError(msg)
    ck(row['spec']==spec,'benchmark plan');ck(row['input_unchanged']is True,'benchmark input mutation')
    ck(row['input_sha256']==digest(compact(inp).encode()),'benchmark input identity')
    ck(row['affinity']==[0],'affinity')
    ck(set(row['arms'])=={'FULL_PREFIX','INCREMENTAL'},'arm count')
    n=spec['length'];b=spec['batch'];ends=list(range(b,n+1,b))
    expected=[oracle(inp['context'],inp['events'][:end],'FOCUS_KEYMAP') for end in ends]
    for a in row['arms'].values():
        ck(all(valid_answer(x) for x in a['outputs']) and a['outputs']==expected,'benchmark outputs')
        for prefix in ('wall','cpu'):
            x=a[prefix+'_before_ns'];y=a[prefix+'_after_ns'];ck(integer(x) and integer(y) and y>x,'clock bracket')
    ck(row['arms']['INCREMENTAL']['visited']==n and type(row['arms']['INCREMENTAL']['visited'])is int,'all delta visits')
    ck(row['arms']['FULL_PREFIX']['visited']is None,'unmeasured reference visits')
    f=row['arms']['FULL_PREFIX'];i=row['arms']['INCREMENTAL']
    def duration(a,p):return a[p+'_after_ns']-a[p+'_before_ns']
    return dict(checks=checks,length=n,batch=b,rep=spec['rep'],full_wall_ns=duration(f,'wall'),incremental_wall_ns=duration(i,'wall'),
                full_cpu_ns=duration(f,'cpu'),incremental_cpu_ns=duration(i,'cpu'),cpu_ratio=duration(i,'cpu')/duration(f,'cpu'),
                wall_ratio=duration(i,'wall')/duration(f,'wall'),analytic_reference_visits=sum(ends),candidate_visits=n)

def audit(root):
    root=Path(root);freeze=json.loads((root/'FREEZE.json').read_text());checks=0
    def ck(x,msg):
        nonlocal checks;checks+=1
        if not x:raise AuditError(msg)
    for name,h in freeze['files'].items():ck(digest((root/name).read_bytes())==h,'frozen source/input '+name)
    cases=json.loads((root/'CASES.json').read_text());plan=json.loads((root/'BENCH_PLAN.json').read_text());inputs=json.loads((root/'BENCH_INPUTS.json').read_text())
    # The original native records are immutable retained inputs, not new acquisitions.
    for c in cases:
        if c['kind']=='retained':
            d=json.loads((root/c['source']).read_text());s=[s for s in d['samples'] if s['mode']=='EVENT_SYNC']
            ck(c['events']==[e for x in s for e in x['events']],'original event bytes')
            ck(c['old_decisions']==[x['decision'] for x in s],'original decisions')
            ck(c['context']['seed_keymap']==d['seed']['result']['keymap'] and c['context']['window']==d['window'] and c['context']['keycode']==d['keycode'] and c['context']['first_ordinal']==d['first_ordinal'],'retained context')
    benches=[];correct=None;pids=[]
    for stage in range(7):
        p=root/'formal'/f'stage-{stage}'
        end=json.loads((p/'END.json').read_text());outer=json.loads((p/'OUTER.json').read_text())
        ck(end['status']=='COMPLETE' and end['stage']==stage,'stage completion')
        ck(type(outer['returncode'])is int and outer['returncode']==0 and outer['timeout']is False,'outer exit')
        jobs=[('correctness',0)] if stage==0 else [('bench',i) for i in range((stage-1)*5,stage*5)]
        ck(end['processes']==[f'{k}-{i}' for k,i in jobs],'stage job denominator')
        for kind,index in jobs:
            name=f'{kind}-{index}';r=json.loads((p/(name+'.process.json')).read_text());raw=(p/(name+'.jsonl')).read_bytes();err=(p/(name+'.stderr')).read_bytes()
            ck(type(r['returncode'])is int and r['returncode']==0 and r['timeout']is False,'child exit')
            ck(r['kind']==kind and type(r['index'])is int and r['index']==index,'child identity')
            ck(r['argv'][-2:]==[kind,str(index)] and r['argv'][-3].endswith('/evaluate.py') and r['argv'][1:3]==['-S','-B'],'command')
            ck(digest(raw)==r['stdout_sha256'] and digest(err)==r['stderr_sha256'] and not err,'process bytes')
            ck(integer(r['start_ns']) and integer(r['end_ns']) and r['end_ns']>r['start_ns'],'process time')
            pids.append(r['pid']);rows=[json.loads(x) for x in raw.splitlines()]
            if kind=='correctness':correct=audit_correctness(cases,rows)
            else:
                ck(len(rows)==1,'bench process row');ck(rows[0]['pid']==r['pid'],'bench PID')
                b=audit_benchmark(plan[index],inputs[str(plan[index]['length'])],rows[0]);benches.append(b)
                seq=[rows[0]['arms'][arm] for arm in plan[index]['order']]
                ck(r['start_ns']<=seq[0]['wall_before_ns']<seq[0]['wall_after_ns']<=seq[1]['wall_before_ns']<seq[1]['wall_after_ns']<=r['end_ns'],'timed order/bounds')
    ck(len(pids)==31 and len(set(pids))==31,'process denominator')
    cells=[]
    for n in (64,256,1024):
        for b in (1,16):
            rows=[r for r in benches if r['length']==n and r['batch']==b];ck(len(rows)==5,'timing repetitions')
            cell=dict(length=n,batch=b)
            for key in ('full_wall_ns','incremental_wall_ns','full_cpu_ns','incremental_cpu_ns','cpu_ratio','wall_ratio'):
                vals=[r[key] for r in rows];cell[key]=dict(min=min(vals),median=statistics.median(vals),max=max(vals))
            cell['analytic_reference_visits']=rows[0]['analytic_reference_visits'];cell['candidate_visits']=n;cells.append(cell)
    primary=next(x for x in cells if x['length']==1024 and x['batch']==1)
    speed=primary['cpu_ratio']['median']<=0.50
    return dict(status='PASS_INCREMENTAL_FOCUS_FOLD_CONTRACT',speed_status='PASS_LOCAL_REDUCER_CPU_GATE' if speed else 'HOLD_LOCAL_REDUCER_CPU_GATE',
                checks=checks+correct['checks']+sum(x['checks'] for x in benches),correctness=correct,cells=cells,processes=len(pids),errors=[],
                source_files=len(freeze['files']),gui_runs=0,model_calls=0,production_adoption=False)
if __name__=='__main__':
    try:result=audit(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent)
    except Exception as e:print(json.dumps(dict(status='HOLD_AUDIT',error=type(e).__name__+': '+str(e))));raise SystemExit(2)
    print(json.dumps(result,sort_keys=True,indent=2))