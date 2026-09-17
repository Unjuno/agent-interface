import argparse, hashlib, json, random
from dataclasses import dataclass

SEED=112620260918005; TRANSITIONS=600000
PGENS=[0,1,2,100,1000000,2147483647]
@dataclass(frozen=True,order=True)
class S: session:str; target:str
SCOPES=[S('s0','t0'),S('s0','t1'),S('s1','t0'),S('s1','t1')]

def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'))

def oracle_schedule_digest(seed=SEED, transitions=TRANSITIONS):
    rng=random.Random(seed); h=hashlib.sha256(); total=0; traces=0; counts={}; stale_installs=0; stale_admits=0; replay_installs=0; dup_double=0; cross=0; auth=0; fresh_i=0; fresh_a=0; pgens=set()
    while total<transitions:
      epochs={}; req={}; dec={}; seen=set(); req_list=[]; dec_list=[]; inv_ids=[]; n=min(rng.randint(16,64),transitions-total)
      def snap(): return {'epochs':sorted((a,b,e) for (a,b),e in epochs.items()),'requests':sorted((rid,k[0],k[1],ep,c) for rid,(k,ep,c) in req.items()),'decisions':sorted((did,k[0],k[1],ep,pg,rid) for did,(k,ep,pg,rid) in dec.items()),'seen_invalidations':sorted(seen)}
      for step in range(n):
        scope=rng.choice(SCOPES); key=(scope.session,scope.target); p=rng.random(); before=snap()
        if p<.28:
          rid=f'r{traces}:{step}'; req_list.append((rid,scope)); ep=epochs.get(key,0); req[rid]=[key,ep,False]; out={'status':'REQUEST_BEGUN','request_id':rid,'scope':{'session':scope.session,'target':scope.target},'request_epoch':ep,'grants_input_authority':False}
        elif p<.49:
          if inv_ids and rng.random()<.20: eid=rng.choice(inv_ids)
          else: eid=f'e{traces}:{step}'; inv_ids.append(eid)
          if eid in seen: out={'status':'DUPLICATE_INVALIDATION_NOOP','event_id':eid,'scope':{'session':scope.session,'target':scope.target},'epoch':epochs.get(key,0),'grants_input_authority':False}
          else: seen.add(eid); epochs[key]=epochs.get(key,0)+1; out={'status':'CURRENTNESS_INVALIDATED','event_id':eid,'scope':{'session':scope.session,'target':scope.target},'epoch':epochs[key],'grants_input_authority':False}
        elif p<.76:
          if req_list and rng.random()<.84: rid,rsc=rng.choice(req_list)
          else: rid=f'unknown{traces}:{step}'
          did=f'd{traces}:{step}'; pg=rng.choice(PGENS); dec_list.append((did,rid)); q=req.get(rid)
          if q is None: out={'status':'UNKNOWN_REQUEST_REFUSED','request_id':rid,'decision_id':did,'planner_generation':pg,'grants_input_authority':False}
          else:
            k,origin,cons=q; cur=epochs.get(k,0); sc={'session':k[0],'target':k[1]}
            if cons: out={'status':'RESPONSE_REPLAY_REFUSED','request_id':rid,'decision_id':did,'scope':sc,'request_epoch':origin,'epoch':cur,'planner_generation':pg,'grants_input_authority':False}
            else:
              q[2]=True
              if origin!=cur: out={'status':'STALE_RESPONSE_REFUSED','request_id':rid,'decision_id':did,'scope':sc,'request_epoch':origin,'epoch':cur,'planner_generation':pg,'grants_input_authority':False}
              else: dec[did]=(k,origin,pg,rid); out={'status':'DECISION_INSTALLED','request_id':rid,'decision_id':did,'scope':sc,'epoch':origin,'planner_generation':pg,'grants_input_authority':False}
        else:
          if dec_list and rng.random()<.84: did,_=rng.choice(dec_list); qscope=scope if rng.random()<.35 else rng.choice(SCOPES)
          else: did=f'unknownD{traces}:{step}'; qscope=scope
          qk=(qscope.session,qscope.target); cur=epochs.get(qk,0); rec=dec.get(did); sc={'session':qscope.session,'target':qscope.target}
          if rec is None: out={'status':'UNKNOWN_DECISION','decision_id':did,'scope':sc,'epoch':cur,'grants_input_authority':False}
          else:
            dk,dep,pg,rid=rec; dsc={'session':dk[0],'target':dk[1]}
            if dk!=qk: out={'status':'SCOPE_MISMATCH','decision_id':did,'scope':sc,'decision_scope':dsc,'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
            elif dep!=cur: out={'status':'STALE_EPOCH_REFUSED','decision_id':did,'scope':sc,'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
            else: out={'status':'ADMITTED','decision_id':did,'scope':sc,'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
        st=out['status']; counts[st]=counts.get(st,0)+1
        if out.get('grants_input_authority') is not False: auth+=1
        if st=='DECISION_INSTALLED': fresh_i+=1; pgens.add(out['planner_generation']); k,ep,_,_=dec[out['decision_id']]; stale_installs += ep!=epochs.get(k,0)
        if st=='ADMITTED': fresh_a+=1; k,ep,_,_=dec[out['decision_id']]; stale_admits += ep!=epochs.get(k,0)
        if st=='RESPONSE_REPLAY_REFUSED' and out['decision_id'] in dec: replay_installs+=1
        if st=='DUPLICATE_INVALIDATION_NOOP' and before['epochs']!=snap()['epochs']: dup_double+=1
        h.update(canon({'out':out,'snapshot':snap()}).encode()+b'\n'); total+=1
      traces+=1
    return {'transitions':total,'traces':traces,'counts':counts,'transition_digest':h.hexdigest(),'stale_response_installs':stale_installs,'stale_old_epoch_admissions':stale_admits,'response_replay_installs':replay_installs,'duplicate_invalidation_double_advances':dup_double,'cross_scope_mutations':cross,'authority_promotions':auth,'fresh_installs':fresh_i,'fresh_admissions':fresh_a,'planner_generations_seen':sorted(pgens)}

def audit(result):
    exp=oracle_schedule_digest(); errors=[]
    for k in exp:
      if result.get(k)!=exp[k]: errors.append(k)
    if result.get('task')!='CURRENTNESS-REQUEST-ORIGIN-TOKEN-20260918-005': errors.append('task')
    if result.get('seed')!=SEED: errors.append('seed')
    if result.get('formal_invocations')!=1 or result.get('reruns')!=0: errors.append('invocation')
    if result.get('malformed_controls_passed')!=10: errors.append('malformed')
    if result.get('exhaustive',{}).get('candidate_oracle_mismatches')!=0 or result.get('exhaustive',{}).get('stale_installs')!=0: errors.append('exhaustive')
    if result.get('decision')!='PASS_CURRENTNESS_REQUEST_ORIGIN_TOKEN_SCOPED': errors.append('decision')
    return {'audit':'PASS' if not errors else 'FAIL','errors':errors,'regenerated':exp}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args(); r=json.load(open(a.result)); x=audit(r); open(a.out,'w').write(json.dumps(x,indent=2,sort_keys=True)+'\n'); print(json.dumps({'audit':x['audit'],'errors':x['errors']},sort_keys=True)); raise SystemExit(0 if x['audit']=='PASS' else 1)
if __name__=='__main__':main()
