import argparse, hashlib, json, random
from candidate_copy import Scope, Invalidation, RequestOriginBarrier
from oracle import replay

SEED=112620260918106; TRANSITIONS=600000; STRESS_CASES=5000
SCOPES=[Scope('s0','t0'),Scope('s0','t1'),Scope('s1','t0'),Scope('s1','t1')]
PGENS=[0,1,2,100,1000000,2147483647]
STATUSES=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','UNKNOWN_REQUEST_REFUSED','RESPONSE_REPLAY_REFUSED','STALE_RESPONSE_REFUSED','DECISION_INSTALLED','UNKNOWN_DECISION','SCOPE_MISMATCH','STALE_EPOCH_REFUSED','ADMITTED']

def conv(v):
    if isinstance(v,Scope): return {'session':v.session,'target':v.target}
    if isinstance(v,tuple): return [conv(z) for z in v]
    if isinstance(v,list): return [conv(z) for z in v]
    if isinstance(v,dict): return {k:conv(v[k]) for k in sorted(v)}
    return v

def canon(v): return json.dumps(conv(v),sort_keys=True,separators=(',',':'))

def apply(b,op,args):
    if op=='begin': return b.begin_request(*args)
    if op=='invalidate': return b.invalidate(*args)
    if op=='install': return b.install_response(*args)
    if op=='use': return b.try_use(*args)
    raise AssertionError(op)

def malformed_controls():
    s=SCOPES[0]; cases=[]
    def rejected(fn):
        try: fn(); return False
        except (ValueError,TypeError): return True
    cases += [rejected(lambda:RequestOriginBarrier().begin_request(s,' ')),rejected(lambda:RequestOriginBarrier().begin_request(Scope('','t'),'r'))]
    cases += [rejected(lambda:RequestOriginBarrier().begin_request(s,'r',True)),rejected(lambda:RequestOriginBarrier().install_response('', 'd',0))]
    cases += [rejected(lambda:RequestOriginBarrier().install_response('r','',0)),rejected(lambda:RequestOriginBarrier().install_response('r','d',-1))]
    cases += [rejected(lambda:RequestOriginBarrier().install_response('r','d',1.0)),rejected(lambda:RequestOriginBarrier().install_response('r','d',0,True))]
    cases += [rejected(lambda:RequestOriginBarrier().invalidate(Invalidation('',s))),rejected(lambda:RequestOriginBarrier().try_use(s,''))]
    assert all(cases); return len(cases)

def directed_controls():
    statuses={'fresh':set(),'stale':set()}
    for pg in PGENS:
        s=SCOPES[0]
        b=RequestOriginBarrier(); h=[]
        for op,args in [('begin',(s,f'rf{pg}',False)),('install',(f'rf{pg}',f'df{pg}',pg,False)),('use',(s,f'df{pg}'))]:
            out=apply(b,op,args); h.append((op,args)); want,snap=replay(h); assert out==want and b.snapshot()==snap
        statuses['fresh'].add(out['status'])
        b=RequestOriginBarrier(); h=[]
        outs=[]
        for op,args in [('begin',(s,f'rs{pg}',False)),('invalidate',(Invalidation(f'e{pg}',s),)),('install',(f'rs{pg}',f'ds{pg}',pg,False)),('use',(s,f'ds{pg}'))]:
            out=apply(b,op,args); h.append((op,args)); want,snap=replay(h); assert out==want and b.snapshot()==snap; outs.append(out)
        assert outs[2]['status']=='STALE_RESPONSE_REFUSED' and outs[3]['status']=='UNKNOWN_DECISION'; statuses['stale'].add(outs[2]['status'])
    assert statuses=={'fresh':{'ADMITTED'},'stale':{'STALE_RESPONSE_REFUSED'}}
    return {'planner_generation_influence':0,'fresh_status':'ADMITTED','stale_status':'STALE_RESPONSE_REFUSED','generations':PGENS}

def formal():
    h=hashlib.sha256(); counts={k:0 for k in STATUSES}; mismatch=0; total=0; traces=0
    stale_installs=stale_admits=replay_rebinds=dup_double=cross=authority=0
    fresh_installs=fresh_admits=0; pgens=set(); stress_refused=stress_wrong=0
    def step(b,hist,op,args):
        nonlocal mismatch,total,stale_installs,stale_admits,replay_rebinds,dup_double,cross,authority,fresh_installs,fresh_admits
        before=b.snapshot(); out=apply(b,op,args); hist.append((op,args)); want,snap=replay(hist)
        if out!=want or b.snapshot()!=snap: mismatch+=1
        st=out['status']; counts[st]=counts.get(st,0)+1
        if out.get('grants_input_authority') is not False: authority+=1
        if op=='install': pgens.add(args[2])
        if st=='DECISION_INSTALLED':
            fresh_installs+=1; req=b.requests[out['request_id']]
            if req[1]!=b.epoch.get(req[0],0): stale_installs+=1
        if st=='ADMITTED':
            fresh_admits+=1; rec=b.decisions[out['decision_id']]
            if rec[1]!=b.epoch.get(rec[0],0): stale_admits+=1
        if st=='RESPONSE_REPLAY_REFUSED' and before['decisions']!=b.snapshot()['decisions']: replay_rebinds+=1
        if st=='DUPLICATE_INVALIDATION_NOOP' and before['epochs']!=b.snapshot()['epochs']: dup_double+=1
        if op=='invalidate':
            a={(x[0],x[1]):x[2] for x in before['epochs']}; z={(x[0],x[1]):x[2] for x in b.snapshot()['epochs']}
            expected=(args[0].scope.session,args[0].scope.target)
            if any(k!=expected and a.get(k,0)!=z.get(k,0) for k in set(a)|set(z)): cross+=1
        h.update(canon({'out':out,'snapshot':b.snapshot()}).encode()+b'\n'); total+=1
        return out
    # Explicit fresh stale-inflight stress: 4 transitions each.
    for i in range(STRESS_CASES):
        b=RequestOriginBarrier(); hist=[]; s=SCOPES[i%len(SCOPES)]; pg=PGENS[i%len(PGENS)]
        rid=f'stress-r{i}'; did=f'stress-d{i}'
        step(b,hist,'begin',(s,rid,False)); step(b,hist,'invalidate',(Invalidation(f'stress-e{i}',s),)); out=step(b,hist,'install',(rid,did,pg,False)); use=step(b,hist,'use',(s,did))
        if out['status']=='STALE_RESPONSE_REFUSED' and use['status']=='UNKNOWN_DECISION': stress_refused+=1
        else: stress_wrong+=1
        traces+=1
    rng=random.Random(SEED)
    while total<TRANSITIONS:
        b=RequestOriginBarrier(); hist=[]; requests=[]; decisions=[]; inv_ids=[]; n=min(rng.randint(16,64),TRANSITIONS-total)
        for k in range(n):
            s=rng.choice(SCOPES); p=rng.random()
            if p<.28:
                rid=f'r{traces}:{k}'; op,args='begin',(s,rid,False); requests.append((rid,s))
            elif p<.49:
                if inv_ids and rng.random()<.20: eid=rng.choice(inv_ids)
                else: eid=f'e{traces}:{k}'; inv_ids.append(eid)
                op,args='invalidate',(Invalidation(eid,s),)
            elif p<.76:
                if requests and rng.random()<.84: rid,_=rng.choice(requests)
                else: rid=f'unknown{traces}:{k}'
                did=f'd{traces}:{k}'; pg=rng.choice(PGENS); op,args='install',(rid,did,pg,False); decisions.append((did,rid))
            else:
                if decisions and rng.random()<.84: did,_=rng.choice(decisions); qscope=s if rng.random()<.35 else rng.choice(SCOPES)
                else: did=f'unknownD{traces}:{k}'; qscope=s
                op,args='use',(qscope,did)
            step(b,hist,op,args)
        traces+=1
    controls=directed_controls(); malformed=malformed_controls()
    ok=(mismatch==0 and stale_installs==0 and stale_admits==0 and stress_refused==STRESS_CASES and stress_wrong==0 and replay_rebinds==0 and dup_double==0 and cross==0 and authority==0 and fresh_installs>0 and fresh_admits>0 and sorted(pgens)==PGENS and controls['planner_generation_influence']==0 and malformed==10)
    return {'task':'CURRENTNESS-REQUEST-ORIGIN-FORMAL-20260918-006','seed':SEED,'transitions':total,'traces':traces,'stress_cases':STRESS_CASES,'stress_refused':stress_refused,'stress_wrong':stress_wrong,'counts':counts,'candidate_oracle_mismatches':mismatch,'transition_digest':h.hexdigest(),'stale_response_installs':stale_installs,'stale_old_epoch_admissions':stale_admits,'response_replay_rebinds':replay_rebinds,'duplicate_invalidation_double_advances':dup_double,'cross_scope_mutations':cross,'authority_promotions':authority,'fresh_installs':fresh_installs,'fresh_admissions':fresh_admits,'planner_generations_seen':sorted(pgens),'planner_generation_influence':controls['planner_generation_influence'],'malformed_controls_passed':malformed,'primary_invocations':1,'reruns':0,'decision':'PASS_CURRENTNESS_REQUEST_ORIGIN_FORMAL_SCOPED' if ok else 'FAIL_CURRENTNESS_REQUEST_ORIGIN_FORMAL'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        print(json.dumps({'self_test':'PASS','directed':directed_controls(),'malformed':malformed_controls()},sort_keys=True)); return
    r=formal(); open(a.out,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':r['decision'],'digest':r['transition_digest'],'transitions':r['transitions']},sort_keys=True))
if __name__=='__main__': main()
