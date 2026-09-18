import argparse, hashlib, json, multiprocessing as mp, os, random, socket, threading, time
from candidate_copy import Scope, Invalidation, RequestOriginBarrier

TASK='CURRENTNESS-REQUEST-ORIGIN-AFUNIX-SHADOW-20260918-007'
SEED=124420260918007
CASES_PER_STRATUM=128
STRATA=['INVALIDATE_BEFORE_RESPONSE','INVALIDATE_BEFORE_REQUEST','RESPONSE_BEFORE_INVALIDATE','TRANSPORT_REPLAY']
PGENS=[0,1,2,100,1000000,2147483647]
SCOPES=[Scope('s0','t0'),Scope('s0','t1'),Scope('s1','t0'),Scope('s1','t1')]

def sendj(f,obj):
    f.write((json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()); f.flush()

def recvj(f):
    line=f.readline()
    if not line: raise EOFError('socket_eof')
    return json.loads(line)

def planner_worker(fd):
    sock=socket.socket(fileno=fd); f=sock.makefile('rwb',buffering=0)
    try:
        while True:
            msg=recvj(f)
            if msg.get('cmd')=='stop':
                sendj(f,{'kind':'stopped','worker_ns':time.monotonic_ns()}); return
            if msg.get('cmd')!='request': raise RuntimeError('bad_request_cmd')
            cid=msg['case_id']; sendj(f,{'kind':'ack','case_id':cid,'worker_ns':time.monotonic_ns()})
            rel=recvj(f)
            if rel.get('cmd')!='release' or rel.get('case_id')!=cid: raise RuntimeError('bad_release')
            response={'kind':'response','case_id':cid,'request_id':msg['request_id'],'decision_id':msg['decision_id'],'planner_generation':msg['planner_generation'],'worker_ns':time.monotonic_ns()}
            sendj(f,response)
            if msg.get('replay'):
                rr=recvj(f)
                if rr.get('cmd')!='replay_release' or rr.get('case_id')!=cid: raise RuntimeError('bad_replay_release')
                response2=dict(response); response2['worker_ns']=time.monotonic_ns(); response2['replay']=True; sendj(f,response2)
    finally:
        try: f.close()
        finally: sock.close()

def summarize_output(out):
    if out is None: return None
    z={k:v for k,v in out.items() if k not in ('scope','decision_scope')}
    if 'scope' in out: z['scope']=[out['scope'].session,out['scope'].target]
    if 'decision_scope' in out: z['decision_scope']=[out['decision_scope'].session,out['decision_scope'].target]
    return z

def one_case(f,case_id,stratum,scope,pg):
    b=RequestOriginBarrier(); rid=f'r-{case_id}'; did=f'd-{case_id}'; eid=f'e-{case_id}'
    tl={}; outs={}; parse_errors=0; exception=None
    def stamp(k): tl[k]=time.monotonic_ns()
    def inv_thread():
        stamp('invalidate_thread_start'); outs['invalidate']=b.invalidate(Invalidation(eid,scope)); stamp('invalidate_thread_end')
    try:
        if stratum=='INVALIDATE_BEFORE_REQUEST':
            t=threading.Thread(target=inv_thread,name=f'inv-{case_id}'); t.start(); t.join(); assert not t.is_alive()
        stamp('begin_start'); outs['begin']=b.begin_request(scope,rid,False); stamp('begin_end')
        sendj(f,{'cmd':'request','case_id':case_id,'request_id':rid,'decision_id':did,'planner_generation':pg,'replay':stratum=='TRANSPORT_REPLAY'}); stamp('request_sent')
        ack=recvj(f); stamp('ack_received')
        if ack.get('kind')!='ack' or ack.get('case_id')!=case_id: raise RuntimeError('bad_ack')
        if stratum=='INVALIDATE_BEFORE_RESPONSE':
            t=threading.Thread(target=inv_thread,name=f'inv-{case_id}'); t.start(); t.join(); assert not t.is_alive()
        sendj(f,{'cmd':'release','case_id':case_id}); stamp('release_sent')
        resp=recvj(f); stamp('response_received')
        if resp.get('kind')!='response' or resp.get('case_id')!=case_id: raise RuntimeError('bad_response')
        snap_before=b.snapshot(); stamp('install1_start'); outs['install1']=b.install_response(resp['request_id'],resp['decision_id'],resp['planner_generation'],False); stamp('install1_end'); snap_after1=b.snapshot()
        if stratum=='RESPONSE_BEFORE_INVALIDATE':
            t=threading.Thread(target=inv_thread,name=f'inv-{case_id}'); t.start(); t.join(); assert not t.is_alive()
        if stratum=='TRANSPORT_REPLAY':
            sendj(f,{'cmd':'replay_release','case_id':case_id}); stamp('replay_release_sent')
            resp2=recvj(f); stamp('replay_response_received')
            if not resp2.get('replay') or resp2.get('case_id')!=case_id: raise RuntimeError('bad_replay_response')
            before_replay=b.snapshot(); stamp('install2_start'); outs['install2']=b.install_response(resp2['request_id'],resp2['decision_id'],resp2['planner_generation'],False); stamp('install2_end'); after_replay=b.snapshot()
            outs['replay_decisions_equal']=before_replay['decisions']==after_replay['decisions']
        stamp('use_start'); outs['use']=b.try_use(scope,did); stamp('use_end')
        final=b.snapshot()
    except Exception as e:
        exception=type(e).__name__+':'+str(e); final=b.snapshot()
    row={'case_id':case_id,'stratum':stratum,'scope':[scope.session,scope.target],'planner_generation':pg,'timeline':tl,'outputs':{k:(summarize_output(v) if isinstance(v,dict) else v) for k,v in outs.items()},'exception':exception,'parse_errors':parse_errors,'final_decisions':len(final['decisions']),'final_epoch':next((x[2] for x in final['epochs'] if x[0]==scope.session and x[1]==scope.target),0)}
    return row

def timeline_ok(row):
    t=row['timeline']; s=row['stratum']
    try:
        if s=='INVALIDATE_BEFORE_RESPONSE': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['use_start']
        if s=='INVALIDATE_BEFORE_REQUEST': return t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['begin_start']<=t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['use_start']
        if s=='RESPONSE_BEFORE_INVALIDATE': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['use_start']
        if s=='TRANSPORT_REPLAY': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['replay_release_sent']<=t['replay_response_received']<=t['install2_start']<=t['install2_end']<=t['use_start']
    except KeyError: return False
    return False

def expected(row):
    s=row['stratum']
    if s=='INVALIDATE_BEFORE_RESPONSE': return ('STALE_RESPONSE_REFUSED','UNKNOWN_DECISION',None)
    if s=='INVALIDATE_BEFORE_REQUEST': return ('DECISION_INSTALLED','ADMITTED',None)
    if s=='RESPONSE_BEFORE_INVALIDATE': return ('DECISION_INSTALLED','STALE_EPOCH_REFUSED',None)
    if s=='TRANSPORT_REPLAY': return ('DECISION_INSTALLED','ADMITTED','RESPONSE_REPLAY_REFUSED')
    raise AssertionError(s)

def run(out_result,out_trace,cases_per_stratum=CASES_PER_STRATUM):
    parent,child=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
    ctx=mp.get_context('fork'); proc=ctx.Process(target=planner_worker,args=(child.detach(),),name='planner-shadow'); proc.start(); child.close() if child.fileno()!=-1 else None
    f=parent.makefile('rwb',buffering=0)
    schedule=[]
    for i in range(cases_per_stratum):
        for s in STRATA: schedule.append((s,i))
    rng=random.Random(SEED); rng.shuffle(schedule)
    rows=[]; errors=[]
    try:
        for idx,(stratum,within) in enumerate(schedule):
            scope=SCOPES[(idx+within)%len(SCOPES)]; pg=PGENS[idx % len(PGENS)]; row=one_case(f,idx,stratum,scope,pg); rows.append(row)
    finally:
        try: sendj(f,{'cmd':'stop'}); stop=recvj(f)
        except Exception as e: stop={'error':type(e).__name__+':'+str(e)}
        try: f.close()
        finally: parent.close()
        proc.join(5.0)
        residual=1 if proc.is_alive() else 0
        if proc.is_alive(): proc.terminate(); proc.join(2.0)
    with open(out_trace,'w') as tf:
        for r in rows: tf.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    counts={s:0 for s in STRATA}; mismatch=timeline_bad=exceptions=parse_errors=authority=0; pgens=set(); strata_status={s:{} for s in STRATA}; replay_rebinds=0
    for r in rows:
        counts[r['stratum']]+=1; pgens.add(r['planner_generation']); exceptions+=r['exception'] is not None; parse_errors+=r['parse_errors']; timeline_bad+=not timeline_ok(r)
        exp1,expu,exp2=expected(r); got1=(r['outputs'].get('install1') or {}).get('status'); gotu=(r['outputs'].get('use') or {}).get('status'); got2=(r['outputs'].get('install2') or {}).get('status')
        mismatch += (got1!=exp1 or gotu!=expu or (exp2 is not None and got2!=exp2))
        if r['stratum']=='TRANSPORT_REPLAY' and not r['outputs'].get('replay_decisions_equal',False): replay_rebinds+=1
        for v in r['outputs'].values():
            if isinstance(v,dict) and v.get('grants_input_authority') is not False: authority+=1
        key=f'{got1}|{gotu}|{got2}'; strata_status[r['stratum']][key]=strata_status[r['stratum']].get(key,0)+1
    trace_bytes=open(out_trace,'rb').read(); trace_sha=hashlib.sha256(trace_bytes).hexdigest()
    samples={s:next((r for r in rows if r['stratum']==s),None) for s in STRATA}
    planner_influence=0
    for s in STRATA:
        by={}
        for r in rows:
            if r['stratum']==s:
                sig=((r['outputs'].get('install1') or {}).get('status'),(r['outputs'].get('use') or {}).get('status'),(r['outputs'].get('install2') or {}).get('status'))
                by.setdefault(r['planner_generation'],set()).add(sig)
        if len({next(iter(v)) for v in by.values() if len(v)==1})>1 or any(len(v)!=1 for v in by.values()): planner_influence+=1
    ok=(len(rows)==4*cases_per_stratum and all(counts[s]==cases_per_stratum for s in STRATA) and mismatch==0 and timeline_bad==0 and exceptions==0 and parse_errors==0 and residual==0 and replay_rebinds==0 and authority==0 and sorted(pgens)==PGENS and planner_influence==0)
    result={'task':TASK,'seed':SEED,'cases_per_stratum':cases_per_stratum,'total_cases':len(rows),'stratum_counts':counts,'candidate_oracle_mismatches':mismatch,'timeline_violations':timeline_bad,'exceptions':exceptions,'parse_errors':parse_errors,'cleanup_residual_processes':residual,'response_replay_rebinds':replay_rebinds,'authority_promotions':authority,'planner_generations_seen':sorted(pgens),'planner_generation_influence':planner_influence,'status_counts':strata_status,'trace_sha256':trace_sha,'trace_bytes':len(trace_bytes),'samples':samples,'stop_reply':stop,'primary_invocations':1,'reruns':0,'decision':'PASS_REQUEST_ORIGIN_AFUNIX_SHADOW_SCOPED' if ok else 'FAIL_REQUEST_ORIGIN_AFUNIX_SHADOW'}
    open(out_result,'w').write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result'); ap.add_argument('--trace'); ap.add_argument('--construction',action='store_true'); a=ap.parse_args(); n=6 if a.construction else CASES_PER_STRATUM; r=run(a.result,a.trace,n); print(json.dumps({'decision':r['decision'],'total_cases':r['total_cases'],'trace_sha256':r['trace_sha256']},sort_keys=True))
if __name__=='__main__': main()
