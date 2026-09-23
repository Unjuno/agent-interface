import argparse, hashlib, json, random
from candidate_copy import Scope, DecisionRequest, Invalidation, EpochBarrier

SEED=109220260918103
TRANSITIONS=300_000
SCOPES=(Scope('s0','t0'),Scope('s1','t1'),Scope('s2','t2'),Scope('s3','t3'))
PGENS=(0,1,2,100,10**6,2**31-1)

def canon(x):
    def conv(v):
        if isinstance(v, Scope): return {'session':v.session,'target':v.target}
        if isinstance(v, dict): return {k:conv(v[k]) for k in sorted(v)}
        if isinstance(v, (tuple,list)): return [conv(z) for z in v]
        return v
    return json.dumps(conv(x),sort_keys=True,separators=(',',':'))

def malformed_controls():
    good=Scope('s','t'); passed=0
    bad_decisions=[DecisionRequest('',good,0),DecisionRequest('a',Scope('','t'),0),DecisionRequest('b',good,-1),DecisionRequest('c',good,1.5),DecisionRequest('d',good,0,True)]
    for d in bad_decisions:
        try: EpochBarrier().install(d)
        except ValueError: passed+=1
        else: raise AssertionError('malformed decision accepted')
    b=EpochBarrier(); b.install(DecisionRequest('dup',good,0))
    try: b.install(DecisionRequest('dup',good,1))
    except ValueError: passed+=1
    else: raise AssertionError('duplicate decision accepted')
    for e in [Invalidation('',good),Invalidation('e',Scope('s',''))]:
        try: EpochBarrier().invalidate(e)
        except ValueError: passed+=1
        else: raise AssertionError('malformed invalidation accepted')
    return passed

def predecessor_and_generation_controls():
    # predecessor escape: high planner generation must not survive invalidation
    s=Scope('pre','target'); b=EpochBarrier()
    b.install(DecisionRequest('high',s,2**31-1)); b.invalidate(Invalidation('pre-e',s))
    after=b.try_use(s,'high')
    if after['status']!='STALE_EPOCH_REFUSED': raise AssertionError('predecessor escape')
    # planner generation magnitude must not change runtime epoch semantics
    s0=Scope('pair0','t'); s1=Scope('pair1','t'); a=EpochBarrier(); c=EpochBarrier()
    ra=a.install(DecisionRequest('lo',s0,0)); rc=c.install(DecisionRequest('hi2',s1,2**31-1))
    if (ra['epoch'],ra['status']) != (rc['epoch'],rc['status']): raise AssertionError('planner generation influence install')
    a.invalidate(Invalidation('ia',s0)); c.invalidate(Invalidation('ic',s1))
    if a.try_use(s0,'lo')['status']!='STALE_EPOCH_REFUSED' or c.try_use(s1,'hi2')['status']!='STALE_EPOCH_REFUSED':
        raise AssertionError('planner generation influence invalidation')
    return {'predecessor_escape':0,'planner_generation_influence':0}

def run(seed=SEED, transitions=TRANSITIONS):
    rng=random.Random(seed); h=hashlib.sha256(); total=0; traces=0
    counts={k:0 for k in ['DECISION_INSTALLED','CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','ADMITTED','STALE_EPOCH_REFUSED','UNKNOWN_DECISION','SCOPE_MISMATCH']}
    stale_escape=0; cross_scope_mutation=0; duplicate_double_advance=0; authority_promotions=0
    while total < transitions:
        b=EpochBarrier(); known=[]; inv_ids=[]; n=min(rng.randint(12,48),transitions-total)
        for step in range(n):
            before=b.snapshot(); scope=rng.choice(SCOPES); p=rng.random()
            if p < .34:
                did=f'd{traces}:{step}'; known.append((did,scope)); out=b.install(DecisionRequest(did,scope,rng.choice(PGENS)))
            elif p < .62:
                if inv_ids and rng.random()<.18: eid=rng.choice(inv_ids)
                else: eid=f'e{traces}:{step}'; inv_ids.append(eid)
                old_epoch=dict(b.epoch); seen_before=eid in b.seen_invalidations
                out=b.invalidate(Invalidation(eid,scope))
                if seen_before and b.epoch!=old_epoch: duplicate_double_advance+=1
                for sc,ep in old_epoch.items():
                    if sc!=scope and b.epoch.get(sc,0)!=ep: cross_scope_mutation+=1
            else:
                if known and rng.random()<.83:
                    did,dscope=rng.choice(known)
                    # often query owning scope, sometimes wrong scope
                    qscope=dscope if rng.random()<.78 else rng.choice(SCOPES)
                else:
                    did=f'unknown{traces}:{step}'; qscope=scope
                out=b.try_use(qscope,did)
                if out['status']=='ADMITTED' and out['decision_epoch']!=out['epoch']: stale_escape+=1
            if out.get('grants_input_authority') is not False: authority_promotions+=1
            if out['status'] in counts: counts[out['status']]+=1
            h.update(canon({'out':out,'snapshot':b.snapshot()}).encode()+b'\n')
            total+=1
        traces+=1
    controls=predecessor_and_generation_controls(); malformed=malformed_controls()
    result={'task':'CURRENTNESS-RUNTIME-EPOCH-BARRIER-FORMAL-20260918-003','decision':'PASS_RUNTIME_CURRENTNESS_EPOCH_BARRIER_SCOPED' if stale_escape==cross_scope_mutation==duplicate_double_advance==authority_promotions==0 else 'FAIL','seed':seed,'formal_invocations':1,'reruns':0,'transitions':total,'traces':traces,'counts':counts,'stale_old_epoch_admissions':stale_escape,'cross_scope_mutations':cross_scope_mutation,'duplicate_invalidation_double_advances':duplicate_double_advance,'authority_promotions':authority_promotions,'malformed_controls_passed':malformed,**controls,'transition_digest':h.hexdigest()}
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--smoke',action='store_true'); ap.add_argument('--output',default='FORMAL_RESULT.json'); args=ap.parse_args()
    if args.smoke:
        r=run(seed=7,transitions=5000); print(json.dumps(r,sort_keys=True,indent=2)); return
    r=run(); open(args.output,'w').write(json.dumps(r,sort_keys=True,indent=2)+'\n'); print(json.dumps(r,sort_keys=True,indent=2))
if __name__=='__main__': main()
