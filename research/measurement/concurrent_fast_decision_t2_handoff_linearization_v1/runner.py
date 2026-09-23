from __future__ import annotations
import argparse, hashlib, json, random, threading, time
from pathlib import Path
from candidate import Authority, CLEAR, HARD
from oracle import evaluate_trace

TASK='CONCURRENT-FAST-DECISION-T2-HANDOFF-LINEARIZATION-A10-20260918-013'
SEED=146120260918013
FORMAL_N=250_000
SCOPES=('s0','s1','s2','s3')


def classify_clock(raw:int, publish:int, commit:int)->str:
    if commit < raw: return 'PRE_RAW'
    if commit < publish: return 'BETWEEN_RAW_AND_PUBLICATION'
    return 'POST_PUBLICATION'


def build_spec(i:int, category:str)->dict:
    scope=SCOPES[i%4]
    base=10_000 + i*100
    R=base+30; P=base+60
    C={'RCP':base+45,'CRP':base+15,'RPC':base+75}.get(category,base+15)
    state=CLEAR; ordinary=True; ps=None; pg=None
    ops=[]
    if category=='RCP': ops=[{'kind':'RAW','ns':R},{'kind':'ADMIT','ns':C,'ordinary_authority':True},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='CRP': ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':True},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='RPC': ops=[{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'},{'kind':'ADMIT','ns':C,'ordinary_authority':True}]
    elif category=='ORD_FALSE':
        ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':False},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='HARD':
        state=HARD; ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':True},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='WRONG_SCOPE':
        ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':True,'presented_scope':'other'},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='FUTURE_GEN':
        ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':True,'presented_generation':99},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='REPLAY':
        ops=[{'kind':'ADMIT','ns':C,'ordinary_authority':True},{'kind':'ADMIT','ns':C+1,'ordinary_authority':True},{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'}]
    elif category=='DUP_PUBLISH':
        ops=[{'kind':'RAW','ns':R},{'kind':'PUBLISH','ns':P,'event_id':'ret'},{'kind':'PUBLISH','ns':P+1,'event_id':'ret'},{'kind':'ADMIT','ns':P+2,'ordinary_authority':True}]
    else: raise ValueError(category)
    return {'trace_id':f't{i:06d}','category':category,'scope':scope,'decision_id':f'd{i:06d}',
            'state':state,'prepared_ns':base,'R':R,'P':P,'C':C,'ops':ops}


def execute_candidate(spec:dict)->dict:
    a=Authority(spec['scope'])
    p=a.prepare(spec['decision_id'],spec['state'],spec['prepared_ns'])
    rows=[]
    for op in spec['ops']:
        if op['kind']=='RAW': a.raw_receive(op['ns']); rows.append({'kind':'raw','ns':op['ns']})
        elif op['kind']=='PUBLISH': rows.append({'kind':'publish','result':a.publish_return(op['event_id'],op['ns']),'ns':op['ns']})
        elif op['kind']=='ADMIT':
            r=a.try_admit(p,op['ns'],op['ordinary_authority'],op.get('presented_scope'),op.get('presented_generation'))
            rows.append({'kind':'admit',**r})
        else: raise ValueError('bad op')
    return {'rows':rows,'state':a.snapshot()}


def compare_result(cand:dict, oracle:dict)->bool:
    crows=[r for r in cand['rows'] if r['kind']!='raw']
    orows=oracle['rows']
    return crows==orows and cand['state']==oracle['state']


def directed_construction()->dict:
    def one(order):
        lock=threading.Lock(); raw_ev=threading.Event(); commit_ev=threading.Event(); pub_ev=threading.Event()
        out={}; auth={'closed':False,'gen':1}
        def recv_thread():
            if order=='CRP': commit_ev.wait(1)
            out['R']=time.perf_counter_ns(); raw_ev.set()
            if order=='RCP': commit_ev.wait(1)
            with lock:
                out['P']=time.perf_counter_ns(); auth['closed']=True; auth['gen']+=1
            pub_ev.set()
        def commit_thread():
            if order in ('RCP','RPC'): raw_ev.wait(1)
            if order=='RPC': pub_ev.wait(1)
            with lock:
                out['C']=time.perf_counter_ns(); out['admitted']=not auth['closed'] and auth['gen']==1
            commit_ev.set()
        if order=='CRP':
            tc=threading.Thread(target=commit_thread); tr=threading.Thread(target=recv_thread); tc.start(); tr.start()
        else:
            tr=threading.Thread(target=recv_thread); tc=threading.Thread(target=commit_thread); tr.start(); tc.start()
        tr.join(1); tc.join(1)
        out['order']=classify_clock(out['R'],out['P'],out['C'])
        out['expected']={'RCP':'BETWEEN_RAW_AND_PUBLICATION','CRP':'PRE_RAW','RPC':'POST_PUBLICATION'}[order]
        return out
    cases=[one(x) for x in ('RCP','CRP','RPC')]
    cats=['RCP','CRP','RPC','ORD_FALSE','HARD','WRONG_SCOPE','FUTURE_GEN','REPLAY','DUP_PUBLISH']
    semantic=[]
    for i,cat in enumerate(cats):
        spec=build_spec(i,cat); cand=execute_candidate(spec); ora=evaluate_trace(spec)
        semantic.append({'category':cat,'match':compare_result(cand,ora),'candidate':cand,'oracle':ora})
    return {'task':TASK,'phase':'construction','formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,
            'thread_cases':cases,'semantic_controls':semantic}


def schedule_categories()->list[str]:
    counts=[('RCP',60_000),('CRP',40_000),('RPC',60_000),('ORD_FALSE',20_000),('HARD',20_000),
            ('WRONG_SCOPE',15_000),('FUTURE_GEN',15_000),('REPLAY',10_000),('DUP_PUBLISH',10_000)]
    arr=[]
    for cat,n in counts: arr.extend([cat]*n)
    assert len(arr)==FORMAL_N
    rng=random.Random(SEED); rng.shuffle(arr)
    return arr


def formal(source_sha256:dict)->dict:
    cats=schedule_categories()
    m={'traces':0,'candidate_oracle_mismatch':0,'post_publication_effects':0,'stale_generation_effects':0,
       'rcp_rows':0,'rcp_between_classified':0,'post_publication_attempts':0,'fresh_effects':0,
       'ordinary_false_effects':0,'hard_effects':0,'wrong_scope_effects':0,'future_generation_effects':0,
       'replay_second_effects':0,'duplicate_publish_double_advance':0,'discriminator_hidden_after_raw_effects':0}
    digest=hashlib.sha256()
    sample_rows=[]
    for i,cat in enumerate(cats):
        spec=build_spec(i,cat); cand=execute_candidate(spec); ora=evaluate_trace(spec)
        m['traces']+=1
        if not compare_result(cand,ora): m['candidate_oracle_mismatch']+=1
        admits=[r for r in cand['rows'] if r['kind']=='admit' and r['admitted']]
        for r in admits:
            cls=classify_clock(spec['R'],spec['P'],r['commit_ns'])
            if cls=='POST_PUBLICATION': m['post_publication_effects']+=1
            if r['generation_at_commit']!=1: m['stale_generation_effects']+=1
        if cat=='RCP':
            m['rcp_rows']+=1
            ar=[r for r in cand['rows'] if r['kind']=='admit'][0]
            if classify_clock(spec['R'],spec['P'],ar['commit_ns'])=='BETWEEN_RAW_AND_PUBLICATION': m['rcp_between_classified']+=1
            if ar['admitted'] and spec['R'] < ar['commit_ns'] < spec['P'] and ar['commit_ns'] < spec['P']:
                m['discriminator_hidden_after_raw_effects']+=1
        if cat=='RPC':
            m['post_publication_attempts']+=1
        if cat in ('RCP','CRP'):
            m['fresh_effects'] += len(admits)
        if cat=='ORD_FALSE': m['ordinary_false_effects'] += len(admits)
        if cat=='HARD': m['hard_effects'] += len(admits)
        if cat=='WRONG_SCOPE': m['wrong_scope_effects'] += len(admits)
        if cat=='FUTURE_GEN': m['future_generation_effects'] += len(admits)
        if cat=='REPLAY':
            ars=[r for r in cand['rows'] if r['kind']=='admit']
            m['replay_second_effects'] += int(len(ars)>1 and ars[1]['admitted'])
        if cat=='DUP_PUBLISH':
            pubs=[r for r in cand['rows'] if r['kind']=='publish']
            m['duplicate_publish_double_advance'] += int(cand['state']['generation']!=2 or [p['result'] for p in pubs] != ['PUBLISHED','DUPLICATE_NOOP'])
        row={'i':i,'cat':cat,'cand':cand,'oracle':ora}
        digest.update(json.dumps(row,sort_keys=True,separators=(',',':')).encode())
        if len(sample_rows)<20: sample_rows.append(row)
    return {'task':TASK,'phase':'formal','seed':SEED,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
            'source_sha256':source_sha256,'metrics':m,'ledger_sha256':digest.hexdigest(),'samples':sample_rows}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['construction','formal'],required=True); ap.add_argument('--out',required=True); ap.add_argument('--source-manifest')
    a=ap.parse_args()
    if a.phase=='construction': out=directed_construction()
    else:
        if not a.source_manifest: raise SystemExit('--source-manifest required for formal')
        sm=json.loads(Path(a.source_manifest).read_text())
        out=formal(sm['sha256'])
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'phase':a.phase,'out':a.out,'metrics':out.get('metrics')},sort_keys=True))
if __name__=='__main__': main()
