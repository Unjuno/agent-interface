import argparse,json,pathlib,random,time
from candidate import RequestOriginBound,InstallTimeOnly,VALID,HARD,AMBIG,SCOPES
from oracle import new_state,apply,snapshot
GENS=(0,1,7,65535,2**31-1,2**63-1)
CATS=[('stale',20000,5),('fresh_replay',20000,6),('installed_invalidate',20000,4),('hard',20000,4),('ambig',20000,4),('cross_scope',20000,3),('duplicate_invalidation',20000,2),('generation',10000,4)]

def ops_for(cat,i,g):
    s=SCOPES[i%4]; other=SCOPES[(i+1)%4]; rid=f'r-{cat}-{i}';resp=f'p-{cat}-{i}';inv=f'i-{cat}-{i}'
    if cat=='stale':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INVALIDATE',scope=s,invalidation_id=inv),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=GENS[(i+1)%len(GENS)]),dict(op='OBSERVE',scope=s,regime=VALID),dict(op='USE',scope=s)]
    if cat=='fresh_replay':return [dict(op='INVALIDATE',scope=s,invalidation_id=inv),dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=GENS[(i+2)%len(GENS)]),dict(op='OBSERVE',scope=s,regime=VALID),dict(op='USE',scope=s),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=g)]
    if cat=='installed_invalidate':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=g),dict(op='INVALIDATE',scope=s,invalidation_id=inv),dict(op='USE',scope=s)]
    if cat=='hard':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=g),dict(op='OBSERVE',scope=s,regime=HARD),dict(op='USE',scope=s)]
    if cat=='ambig':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=g),dict(op='OBSERVE',scope=s,regime=AMBIG),dict(op='USE',scope=s)]
    if cat=='cross_scope':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=other,request_id=rid,response_id=resp,planner_generation=g),dict(op='USE',scope=other)]
    if cat=='duplicate_invalidation':return [dict(op='INVALIDATE',scope=s,invalidation_id=inv),dict(op='INVALIDATE',scope=s,invalidation_id=inv)]
    if cat=='generation':return [dict(op='BEGIN',scope=s,request_id=rid,planner_generation=g),dict(op='INSTALL',scope=s,request_id=rid,response_id=resp,planner_generation=GENS[(i+3)%len(GENS)]),dict(op='OBSERVE',scope=s,regime=VALID),dict(op='USE',scope=s)]
    raise ValueError(cat)
def invoke(c,op):
    k=op['op']
    if k=='BEGIN':return c.begin(op['scope'],op['request_id'],op['planner_generation'],op.get('authority',False))
    if k=='INVALIDATE':return c.invalidate(op['scope'],op['invalidation_id'])
    if k=='INSTALL':return c.install(op['scope'],op['request_id'],op['response_id'],op['planner_generation'],op.get('authority',False))
    if k=='OBSERVE':return c.observe(op['scope'],op['regime'])
    if k=='USE':return c.use(op['scope'])
    raise ValueError(k)
def malformed_controls():
    cs=[]
    tests=[('empty_request',lambda c:c.begin('A','',0)),('bad_scope',lambda c:c.begin('Z','r',0)),('authority_begin',lambda c:c.begin('A','r',0,True)),('authority_install',lambda c:(c.begin('A','r',0),c.install('A','r','p',0,True))[1]),('empty_invalidation',lambda c:c.invalidate('A','')),('bad_regime',lambda c:c.observe('A','BAD')),('bad_response',lambda c:(c.begin('A','r',0),c.install('A','r','',0))[1])]
    for n,f in tests:
        r=f(RequestOriginBound());cs.append({'name':n,'rejected':r['status'].startswith('REFUSE')})
    return cs
def run(seed):
    rng=random.Random(seed); order=[]
    for cat,n,steps in CATS:order += [(cat,i,steps) for i in range(n)]
    rng.shuffle(order)
    transitions=traces=mismatch=result_mismatch=state_mismatch=0;stale_refused=stale_installs=stale_effects=fresh_installs=fresh_effects=replay_attempts=replay_refused=rebinds=0;hard_effects=ambig_effects=double_advance=cross_mut=authority_promotions=generation_failures=0;gen_seen=set();negative_stale_effects=0
    for cat,i,expected_steps in order:
        g=GENS[i%len(GENS)];gen_seen.add(g);ops=ops_for(cat,i,g);assert len(ops)==expected_steps
        c=RequestOriginBound();o=new_state()
        for op in ops:
            cr=invoke(c,op);orr=apply(o,op);transitions+=1
            if cr!=orr:result_mismatch+=1
            if c.snapshot()!=snapshot(o):state_mismatch+=1
            if cr!=orr or c.snapshot()!=snapshot(o):mismatch+=1
            if cat=='stale' and op['op']=='INSTALL':
                if cr['status']=='REFUSE_STALE_ORIGIN':stale_refused+=1
                if cr['status']=='INSTALLED':stale_installs+=1
            if cat=='stale' and op['op']=='USE' and cr.get('effect'):stale_effects+=1
            if cat=='fresh_replay' and op['op']=='INSTALL':
                if cr['status']=='INSTALLED':fresh_installs+=1
                else:
                    replay_attempts+=1
                    if cr['status'].startswith('REFUSE'):replay_refused+=1
                    if cr['status']=='INSTALLED':rebinds+=1
            if cat=='fresh_replay' and op['op']=='USE' and cr.get('effect'):fresh_effects+=1
            if cat=='hard' and op['op']=='USE' and cr.get('effect'):hard_effects+=1
            if cat=='ambig' and op['op']=='USE' and cr.get('effect'):ambig_effects+=1
        if cat=='duplicate_invalidation' and c.epochs[SCOPES[i%4]]!=1:double_advance+=1
        if cat=='cross_scope':
            other=SCOPES[(i+1)%4]
            if c.cache[other] is not None or c.epochs[other]!=0:cross_mut+=1
        if cat=='generation':
            s=SCOPES[i%4]
            if c.cache[s] is None or invoke(c,dict(op='USE',scope=s)).get('effect') is not True:generation_failures+=1
        traces+=1
        if cat=='stale':
            u=InstallTimeOnly()
            for op in ops:
                rr=invoke(u,op)
                if op['op']=='USE' and rr.get('effect'):negative_stale_effects+=1
    ctrls=malformed_controls();authority_promotions=sum(c['rejected'] is False for c in ctrls if c['name'].startswith('authority'))
    return {'task':'CACHE-REQUEST-ORIGIN-COMPOSITION-A2-20260918-002','seed':seed,'formal_invocations':1,'reruns':0,'traces':traces,'transitions':transitions,'candidate_oracle_mismatch':mismatch,'result_mismatch':result_mismatch,'state_mismatch':state_mismatch,'stale_stress':20000,'stale_refused':stale_refused,'stale_origin_cache_installs':stale_installs,'stale_semantic_effects':stale_effects,'fresh_controls':20000,'fresh_installs':fresh_installs,'fresh_effects':fresh_effects,'response_replay_attempts':replay_attempts,'response_replay_refused':replay_refused,'response_rebinds':rebinds,'hard_effects':hard_effects,'ambiguous_effects':ambig_effects,'duplicate_invalidation_double_advance':double_advance,'cross_scope_mutations':cross_mut,'generation_magnitudes_seen':sorted(gen_seen),'generation_specific_failures':generation_failures,'accepted_authority_promotions':authority_promotions,'malformed_controls':ctrls,'install_time_only_stale_semantic_effects':negative_stale_effects}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args()
    if a.out.exists():raise SystemExit('result exists')
    t=time.perf_counter_ns();r=run(a.seed);r['wall_ns']=time.perf_counter_ns()-t;a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
