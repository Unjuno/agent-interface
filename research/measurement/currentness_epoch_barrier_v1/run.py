import itertools, random, json, hashlib
from contract import *
from oracle import replay

S0=Scope('s0','t0'); S1=Scope('s1','t1'); SCOPES=(S0,S1)

def apply(c,history,op,args):
    if op=='install': got=c.install(*args)
    elif op=='invalidate': got=c.invalidate(*args)
    elif op=='use': got=c.try_use(*args)
    else: raise AssertionError(op)
    history.append((op,args))
    want,snap=replay(history)
    if got!=want or c.snapshot()!=snap:
        raise AssertionError(('mismatch',op,args,got,want,c.snapshot(),snap,history))
    if got.get('grants_input_authority') is not False:
        raise AssertionError('authority promotion')
    return got

c=EpochBarrier(); h=[]
apply(c,h,'install',(DecisionRequest('hi',S0,100),))
assert apply(c,h,'use',(S0,'hi'))['status']=='ADMITTED'
apply(c,h,'invalidate',(Invalidation('e0',S0),))
assert apply(c,h,'use',(S0,'hi'))['status']=='STALE_EPOCH_REFUSED'
apply(c,h,'install',(DecisionRequest('fresh',S0,0),))
assert apply(c,h,'use',(S0,'fresh'))['status']=='ADMITTED'
apply(c,h,'invalidate',(Invalidation('e1',S0),))
apply(c,h,'invalidate',(Invalidation('e2',S0),))
assert apply(c,h,'use',(S0,'fresh'))['status']=='STALE_EPOCH_REFUSED'
ep_before=c.snapshot()
assert apply(c,h,'invalidate',(Invalidation('e2',S1),))['status']=='DUPLICATE_INVALIDATION_NOOP'
assert c.snapshot()==ep_before
apply(c,h,'install',(DecisionRequest('other',S1,999999),))
assert apply(c,h,'use',(S1,'other'))['status']=='ADMITTED'
assert apply(c,h,'use',(S0,'other'))['status']=='SCOPE_MISMATCH'
try: c.install(DecisionRequest('other',S1,1)); raise AssertionError('duplicate decision accepted')
except ValueError as e: assert str(e)=='duplicate_decision_id'
for bad in [DecisionRequest('',S0,0),DecisionRequest('x',Scope('','t'),0),DecisionRequest('x2',S0,-1),DecisionRequest('x3',S0,0,True)]:
    try: EpochBarrier().install(bad); raise AssertionError('malformed install accepted')
    except ValueError: pass
for bad in [Invalidation('',S0),Invalidation('x',Scope('s',''))]:
    try: EpochBarrier().invalidate(bad); raise AssertionError('malformed invalidation accepted')
    except ValueError: pass

rng=random.Random(109220260918002)
transitions=0; traces=0; stale_refusals=0; admitted=0; invalidations=0; duplicate_invalidations=0
while transitions < 520_000:
    c=EpochBarrier(); h=[]; known=[]; inv_ids=[]
    n=rng.randint(8,42)
    for step in range(n):
        scope=rng.choice(SCOPES)
        p=rng.random()
        if p < .34:
            if known and rng.random()<.10:
                did=rng.choice(known)
                d=DecisionRequest(did,scope,rng.choice([0,1,2,100,10**6]))
                try: c.install(d); raise AssertionError('duplicate decision accepted random')
                except ValueError as e: assert str(e)=='duplicate_decision_id'
            else:
                did=f'd{traces}:{step}'; known.append(did)
                apply(c,h,'install',(DecisionRequest(did,scope,rng.choice([0,1,2,3,100,10**6])),))
        elif p < .62:
            if inv_ids and rng.random()<.18: eid=rng.choice(inv_ids)
            else: eid=f'e{traces}:{step}'; inv_ids.append(eid)
            out=apply(c,h,'invalidate',(Invalidation(eid,scope),)); invalidations+=1
            duplicate_invalidations += out['status']=='DUPLICATE_INVALIDATION_NOOP'
        else:
            did=rng.choice(known) if known and rng.random()<.82 else f'unknown{traces}:{step}'
            out=apply(c,h,'use',(scope,did))
            stale_refusals += out['status']=='STALE_EPOCH_REFUSED'
            admitted += out['status']=='ADMITTED'
        transitions+=1
    traces+=1

A=[
 ('install',(DecisionRequest('a',S0,100),)),
 ('install',(DecisionRequest('b',S0,0),)),
 ('install',(DecisionRequest('c',S1,7),)),
 ('invalidate',(Invalidation('x',S0),)),
 ('invalidate',(Invalidation('y',S1),)),
 ('use',(S0,'a')),('use',(S0,'b')),('use',(S1,'c')),
]
exhaustive=0; exhaustive_rejected=0
for length in range(0,6):
    for seq in itertools.product(range(len(A)), repeat=length):
        c=EpochBarrier(); h=[]
        for idx in seq:
            op,args=A[idx]
            try: apply(c,h,op,args)
            except ValueError:
                exhaustive_rejected+=1; break
        exhaustive+=1

summary={
 'task':'CURRENTNESS-RUNTIME-EPOCH-BARRIER-20260918-002',
 'status':'CONSTRUCTION_PASS',
 'seed':109220260918002,
 'random_transitions':transitions,
 'random_traces':traces,
 'stale_epoch_refusals':stale_refusals,
 'admitted_uses':admitted,
 'invalidation_calls':invalidations,
 'duplicate_invalidation_noops':duplicate_invalidations,
 'exhaustive_traces':exhaustive,
 'exhaustive_expected_rejections':exhaustive_rejected,
 'candidate_oracle_mismatches':0,
 'predecessor_generation100_escape_closed':True,
 'authority_promotions':0,
}
summary['digest']=hashlib.sha256(json.dumps(summary,sort_keys=True,separators=(',',':')).encode()).hexdigest()
print(json.dumps(summary,sort_keys=True,indent=2))
