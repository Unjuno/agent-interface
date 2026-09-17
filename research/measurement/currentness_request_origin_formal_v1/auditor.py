import argparse, hashlib, json, random
from dataclasses import dataclass

SEED=112620260918106; TRANSITIONS=600000; STRESS_CASES=5000
PGENS=[0,1,2,100,1000000,2147483647]
@dataclass(frozen=True,order=True)
class S: session:str; target:str
SCOPES=[S('s0','t0'),S('s0','t1'),S('s1','t0'),S('s1','t1')]
STATUSES=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','UNKNOWN_REQUEST_REFUSED','RESPONSE_REPLAY_REFUSED','STALE_RESPONSE_REFUSED','DECISION_INSTALLED','UNKNOWN_DECISION','SCOPE_MISMATCH','STALE_EPOCH_REFUSED','ADMITTED']

def cscope(s): return {'session':s.session,'target':s.target}
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'))

def regenerate():
    h=hashlib.sha256(); counts={k:0 for k in STATUSES}; total=0; traces=0; stress_refused=0; pgens=set(); fresh_i=fresh_a=0
    def newstate(): return {'epochs':{},'requests':{},'decisions':{},'seen':set()}
    def snap(st):
        return {'epochs':[[a,b,e] for (a,b),e in sorted(st['epochs'].items())], 'requests':[[rid,k[0],k[1],ep,c] for rid,(k,ep,c) in sorted(st['requests'].items())], 'decisions':[[did,k[0],k[1],ep,pg,rid] for did,(k,ep,pg,rid) in sorted(st['decisions'].items())], 'seen_invalidations':sorted(st['seen'])}
    def step(st,op,args):
        nonlocal total,fresh_i,fresh_a
        if op=='begin':
            s,rid=args; key=(s.session,s.target); ep=st['epochs'].get(key,0); st['requests'][rid]=[key,ep,False]; out={'status':'REQUEST_BEGUN','request_id':rid,'scope':cscope(s),'request_epoch':ep,'grants_input_authority':False}
        elif op=='invalidate':
            eid,s=args; key=(s.session,s.target)
            if eid in st['seen']: out={'status':'DUPLICATE_INVALIDATION_NOOP','event_id':eid,'scope':cscope(s),'epoch':st['epochs'].get(key,0),'grants_input_authority':False}
            else: st['seen'].add(eid); st['epochs'][key]=st['epochs'].get(key,0)+1; out={'status':'CURRENTNESS_INVALIDATED','event_id':eid,'scope':cscope(s),'epoch':st['epochs'][key],'grants_input_authority':False}
        elif op=='install':
            rid,did,pg=args; pgens.add(pg); req=st['requests'].get(rid)
            if req is None: out={'status':'UNKNOWN_REQUEST_REFUSED','request_id':rid,'decision_id':did,'planner_generation':pg,'grants_input_authority':False}
            else:
                key,origin,cons=req; cur=st['epochs'].get(key,0); s=S(*key)
                if cons: out={'status':'RESPONSE_REPLAY_REFUSED','request_id':rid,'decision_id':did,'scope':cscope(s),'request_epoch':origin,'epoch':cur,'planner_generation':pg,'grants_input_authority':False}
                else:
                    req[2]=True
                    if origin!=cur: out={'status':'STALE_RESPONSE_REFUSED','request_id':rid,'decision_id':did,'scope':cscope(s),'request_epoch':origin,'epoch':cur,'planner_generation':pg,'grants_input_authority':False}
                    else: st['decisions'][did]=(key,origin,pg,rid); fresh_i+=1; out={'status':'DECISION_INSTALLED','request_id':rid,'decision_id':did,'scope':cscope(s),'epoch':origin,'planner_generation':pg,'grants_input_authority':False}
        else:
            s,did=args; key=(s.session,s.target); cur=st['epochs'].get(key,0); rec=st['decisions'].get(did)
            if rec is None: out={'status':'UNKNOWN_DECISION','decision_id':did,'scope':cscope(s),'epoch':cur,'grants_input_authority':False}
            else:
                dkey,dep,pg,rid=rec; ds=S(*dkey)
                if dkey!=key: out={'status':'SCOPE_MISMATCH','decision_id':did,'scope':cscope(s),'decision_scope':cscope(ds),'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
                elif dep!=cur: out={'status':'STALE_EPOCH_REFUSED','decision_id':did,'scope':cscope(s),'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
                else: fresh_a+=1; out={'status':'ADMITTED','decision_id':did,'scope':cscope(s),'epoch':cur,'decision_epoch':dep,'planner_generation':pg,'request_id':rid,'grants_input_authority':False}
        counts[out['status']]=counts.get(out['status'],0)+1; h.update(canon({'out':out,'snapshot':snap(st)}).encode()+b'\n'); total+=1; return out
    for i in range(STRESS_CASES):
        st=newstate(); s=SCOPES[i%4]; pg=PGENS[i%6]; rid=f'stress-r{i}'; did=f'stress-d{i}'
        step(st,'begin',(s,rid)); step(st,'invalidate',(f'stress-e{i}',s)); o=step(st,'install',(rid,did,pg)); u=step(st,'use',(s,did)); stress_refused += (o['status']=='STALE_RESPONSE_REFUSED' and u['status']=='UNKNOWN_DECISION'); traces+=1
    rng=random.Random(SEED)
    while total<TRANSITIONS:
        st=newstate(); requests=[]; decisions=[]; inv=[]; n=min(rng.randint(16,64),TRANSITIONS-total)
        for k in range(n):
            s=rng.choice(SCOPES); p=rng.random()
            if p<.28: rid=f'r{traces}:{k}'; requests.append((rid,s)); step(st,'begin',(s,rid))
            elif p<.49:
                if inv and rng.random()<.20: eid=rng.choice(inv)
                else: eid=f'e{traces}:{k}'; inv.append(eid)
                step(st,'invalidate',(eid,s))
            elif p<.76:
                if requests and rng.random()<.84: rid,_=rng.choice(requests)
                else: rid=f'unknown{traces}:{k}'
                did=f'd{traces}:{k}'; pg=rng.choice(PGENS); decisions.append((did,rid)); step(st,'install',(rid,did,pg))
            else:
                if decisions and rng.random()<.84: did,_=rng.choice(decisions); q=s if rng.random()<.35 else rng.choice(SCOPES)
                else: did=f'unknownD{traces}:{k}'; q=s
                step(st,'use',(q,did))
        traces+=1
    return {'transitions':total,'traces':traces,'stress_cases':STRESS_CASES,'stress_refused':stress_refused,'counts':counts,'transition_digest':h.hexdigest(),'fresh_installs':fresh_i,'fresh_admissions':fresh_a,'planner_generations_seen':sorted(pgens)}

def validate(got,exp):
    errors=[]
    for k,v in exp.items():
        if got.get(k)!=v: errors.append(k)
    fixed={'task':'CURRENTNESS-REQUEST-ORIGIN-FORMAL-20260918-006','seed':SEED,'candidate_oracle_mismatches':0,'stale_response_installs':0,'stale_old_epoch_admissions':0,'response_replay_rebinds':0,'duplicate_invalidation_double_advances':0,'cross_scope_mutations':0,'authority_promotions':0,'planner_generation_influence':0,'malformed_controls_passed':10,'primary_invocations':1,'reruns':0,'decision':'PASS_CURRENTNESS_REQUEST_ORIGIN_FORMAL_SCOPED','stress_wrong':0}
    for k,v in fixed.items():
        if got.get(k)!=v: errors.append(k)
    return sorted(set(errors))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args(); got=json.load(open(a.result)); exp=regenerate(); errors=validate(got,exp); obj={'audit':'PASS' if not errors else 'FAIL','errors':errors,'regenerated':exp}; open(a.out,'w').write(json.dumps(obj,indent=2,sort_keys=True)+'\n'); print(json.dumps({'audit':obj['audit'],'errors':errors},sort_keys=True)); raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
