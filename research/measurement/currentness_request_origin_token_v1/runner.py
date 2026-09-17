import argparse, hashlib, itertools, json, random
from candidate import Scope, Invalidation, RequestOriginBarrier
from oracle import replay

SEED=112620260918005; TRANSITIONS=600000
SCOPES=[Scope('s0','t0'),Scope('s0','t1'),Scope('s1','t0'),Scope('s1','t1')]
PGENS=[0,1,2,100,1000000,2147483647]
STATUSES=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','UNKNOWN_REQUEST_REFUSED','RESPONSE_REPLAY_REFUSED','STALE_RESPONSE_REFUSED','DECISION_INSTALLED','UNKNOWN_DECISION','SCOPE_MISMATCH','STALE_EPOCH_REFUSED','ADMITTED']

def canon(x):
    def conv(v):
        if isinstance(v,Scope): return {'session':v.session,'target':v.target}
        if isinstance(v,tuple): return [conv(z) for z in v]
        if isinstance(v,list): return [conv(z) for z in v]
        if isinstance(v,dict): return {k:conv(v[k]) for k in sorted(v)}
        return v
    return json.dumps(conv(x),sort_keys=True,separators=(',',':'))

def apply(b,op,args):
    if op=='begin': return b.begin_request(*args)
    if op=='invalidate': return b.invalidate(*args)
    if op=='install': return b.install_response(*args)
    if op=='use': return b.try_use(*args)
    raise AssertionError(op)

def directed_controls():
    def run(ops):
        b=RequestOriginBarrier(); hist=[]; outs=[]
        for op,args in ops:
            out=apply(b,op,args); hist.append((op,args)); want,snap=replay(hist); assert out==want and b.snapshot()==snap; outs.append(out)
        return outs,b
    s=SCOPES[0]; s2=SCOPES[1]
    controls={}
    controls['1118_stale']=run([('begin',(s,'r',False)),('invalidate',(Invalidation('e',s),)),('install',('r','d',100,False)),('use',(s,'d'))])[0]
    assert controls['1118_stale'][2]['status']=='STALE_RESPONSE_REFUSED' and controls['1118_stale'][3]['status']=='UNKNOWN_DECISION'
    controls['fresh']=run([('begin',(s,'r',False)),('install',('r','d',1,False)),('use',(s,'d'))])[0]; assert controls['fresh'][-1]['status']=='ADMITTED'
    controls['post_inv_fresh']=run([('invalidate',(Invalidation('e',s),)),('begin',(s,'r',False)),('install',('r','d',2**31-1,False)),('use',(s,'d'))])[0]; assert controls['post_inv_fresh'][-1]['status']=='ADMITTED'
    controls['two_inv_stale']=run([('begin',(s,'r',False)),('invalidate',(Invalidation('e1',s),)),('invalidate',(Invalidation('e2',s),)),('install',('r','d',2,False))])[0]; assert controls['two_inv_stale'][-1]['status']=='STALE_RESPONSE_REFUSED'
    controls['unknown']=run([('install',('missing','d',0,False))])[0]; assert controls['unknown'][-1]['status']=='UNKNOWN_REQUEST_REFUSED'
    controls['cross_scope']=run([('begin',(s,'r',False)),('install',('r','d',0,False)),('use',(s2,'d'))])[0]; assert controls['cross_scope'][-1]['status']=='SCOPE_MISMATCH'
    controls['dup_invalidation']=run([('invalidate',(Invalidation('same',s),)),('invalidate',(Invalidation('same',s),))])[0]; assert controls['dup_invalidation'][-1]['status']=='DUPLICATE_INVALIDATION_NOOP'
    controls['replay']=run([('begin',(s,'r',False)),('install',('r','d',0,False)),('install',('r','d2',1,False))])[0]; assert controls['replay'][-1]['status']=='RESPONSE_REPLAY_REFUSED'
    b=RequestOriginBarrier(); b.begin_request(s,'r'); ok=False
    try: b.begin_request(s,'r')
    except ValueError: ok=True
    assert ok; controls['duplicate_request_rejected']=True
    return controls

def malformed_controls():
    s=SCOPES[0]; cases=[]
    def rejected(fn):
        try: fn(); return False
        except (ValueError,TypeError): return True
    cases += [rejected(lambda:RequestOriginBarrier().begin_request(s,' ')), rejected(lambda:RequestOriginBarrier().begin_request(Scope('','t'),'r'))]
    cases += [rejected(lambda:RequestOriginBarrier().begin_request(s,'r',True)), rejected(lambda:RequestOriginBarrier().install_response('', 'd',0))]
    cases += [rejected(lambda:RequestOriginBarrier().install_response('r','',0)), rejected(lambda:RequestOriginBarrier().install_response('r','d',-1))]
    cases += [rejected(lambda:RequestOriginBarrier().install_response('r','d',1.0)), rejected(lambda:RequestOriginBarrier().install_response('r','d',0,True))]
    cases += [rejected(lambda:RequestOriginBarrier().invalidate(Invalidation('',s))), rejected(lambda:RequestOriginBarrier().try_use(s,''))]
    assert all(cases); return len(cases)

def exhaustive():
    total=0; mismatch=0; stale_escape=0
    alphabet='BIRU'
    for n in range(1,6):
      for seq in itertools.product(alphabet,repeat=n):
        b=RequestOriginBarrier(); hist=[]; rid='r'; last_d='none'
        for step,sym in enumerate(seq):
          try:
            if sym=='B': op,args='begin',(SCOPES[0],rid,False)
            elif sym=='I': op,args='invalidate',(Invalidation(f'e{step}',SCOPES[0]),)
            elif sym=='R': last_d=f'd{step}'; op,args='install',(rid,last_d,PGENS[step%len(PGENS)],False)
            else: op,args='use',(SCOPES[0],last_d)
            out=apply(b,op,args); hist.append((op,args)); want,snap=replay(hist)
            if out!=want or b.snapshot()!=snap: mismatch+=1
            if sym=='R' and out['status']=='DECISION_INSTALLED':
              req=b.requests[rid]
              if req[1] != b.epoch.get(req[0],0): stale_escape+=1
          except ValueError:
            break
        total+=1
    return {'traces':total,'candidate_oracle_mismatches':mismatch,'stale_installs':stale_escape}

def formal(seed=SEED,transitions=TRANSITIONS):
    rng=random.Random(seed); h=hashlib.sha256(); total=0; traces=0; mismatch=0
    counts={k:0 for k in STATUSES}; stale_install=0; stale_admission=0; replay_install=0; authority=0; cross_scope_mutation=0; dup_double=0
    fresh_installs=0; fresh_admits=0; pgen_status={str(x):set() for x in PGENS}
    while total<transitions:
      b=RequestOriginBarrier(); hist=[]; requests=[]; decisions=[]; inv_ids=[]; n=min(rng.randint(16,64),transitions-total)
      for step in range(n):
        scope=rng.choice(SCOPES); p=rng.random()
        if p<.28:
          rid=f'r{traces}:{step}'; op,args='begin',(scope,rid,False); requests.append((rid,scope))
        elif p<.49:
          if inv_ids and rng.random()<.20: eid=rng.choice(inv_ids)
          else: eid=f'e{traces}:{step}'; inv_ids.append(eid)
          op,args='invalidate',(Invalidation(eid,scope),)
        elif p<.76:
          if requests and rng.random()<.84:
            rid,rsc=rng.choice(requests)
          else: rid=f'unknown{traces}:{step}'
          did=f'd{traces}:{step}'; pg=rng.choice(PGENS); op,args='install',(rid,did,pg,False); decisions.append((did,rid))
        else:
          if decisions and rng.random()<.84:
            did,_=rng.choice(decisions); qscope=scope if rng.random()<.35 else rng.choice(SCOPES)
          else: did=f'unknownD{traces}:{step}'; qscope=scope
          op,args='use',(qscope,did)
        before=b.snapshot(); out=apply(b,op,args); hist.append((op,args)); want,snap=replay(hist)
        if out!=want or b.snapshot()!=snap: mismatch+=1
        st=out['status']; counts[st]=counts.get(st,0)+1
        if out.get('grants_input_authority') is not False: authority+=1
        if st=='DECISION_INSTALLED':
          fresh_installs+=1; pgen_status[str(out['planner_generation'])].add(st)
          req=b.requests[out['request_id']]
          if req[1] != b.epoch.get(req[0],0): stale_install+=1
        if st=='ADMITTED':
          fresh_admits+=1
          rec=b.decisions[out['decision_id']]
          if rec[1] != b.epoch.get(rec[0],0): stale_admission+=1
        if st=='RESPONSE_REPLAY_REFUSED' and out['decision_id'] in b.decisions: replay_install+=1
        if st=='DUPLICATE_INVALIDATION_NOOP' and before['epochs']!=b.snapshot()['epochs']: dup_double+=1
        if op=='invalidate':
          changed=[]; a=dict(((x[0],x[1]),x[2]) for x in before['epochs']); z=dict(((x[0],x[1]),x[2]) for x in b.snapshot()['epochs'])
          for sc in set(a)|set(z):
            if a.get(sc,0)!=z.get(sc,0): changed.append(sc)
          expected=(args[0].scope.session,args[0].scope.target)
          if any(sc!=expected for sc in changed): cross_scope_mutation+=1
        h.update(canon({'out':out,'snapshot':b.snapshot()}).encode()+b'\n'); total+=1
      traces+=1
    return {'transitions':total,'traces':traces,'counts':counts,'candidate_oracle_mismatches':mismatch,'transition_digest':h.hexdigest(),'stale_response_installs':stale_install,'stale_old_epoch_admissions':stale_admission,'response_replay_installs':replay_install,'duplicate_invalidation_double_advances':dup_double,'cross_scope_mutations':cross_scope_mutation,'authority_promotions':authority,'fresh_installs':fresh_installs,'fresh_admissions':fresh_admits,'planner_generations_seen':sorted(int(k) for k,v in pgen_status.items() if v)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
      c=directed_controls(); ex=exhaustive(); m=malformed_controls(); assert ex['candidate_oracle_mismatches']==0 and ex['stale_installs']==0
      print(json.dumps({'SELF_TEST':'PASS','controls':len(c),'exhaustive':ex,'malformed':m},sort_keys=True)); return
    r=formal(); r['task']='CURRENTNESS-REQUEST-ORIGIN-TOKEN-20260918-005'; r['seed']=SEED; r['directed_controls']=len(directed_controls()); r['exhaustive']=exhaustive(); r['malformed_controls_passed']=malformed_controls(); r['formal_invocations']=1; r['reruns']=0
    ok=(r['candidate_oracle_mismatches']==0 and r['stale_response_installs']==0 and r['stale_old_epoch_admissions']==0 and r['response_replay_installs']==0 and r['duplicate_invalidation_double_advances']==0 and r['cross_scope_mutations']==0 and r['authority_promotions']==0 and r['fresh_installs']>0 and r['fresh_admissions']>0 and r['exhaustive']['candidate_oracle_mismatches']==0 and r['exhaustive']['stale_installs']==0 and r['malformed_controls_passed']==10 and r['planner_generations_seen']==PGENS)
    r['decision']='PASS_CURRENTNESS_REQUEST_ORIGIN_TOKEN_SCOPED' if ok else 'FAIL_CURRENTNESS_REQUEST_ORIGIN_TOKEN'
    open(a.out,'w').write(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':r['decision'],'transitions':r['transitions'],'digest':r['transition_digest']},sort_keys=True))
if __name__=='__main__':main()
