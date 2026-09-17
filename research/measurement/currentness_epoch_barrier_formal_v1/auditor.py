import hashlib, json, random, sys
from candidate_copy import Scope, DecisionRequest, Invalidation, EpochBarrier
from formal_runner import SEED, TRANSITIONS, SCOPES, PGENS, canon, malformed_controls, predecessor_and_generation_controls

# Independent history oracle; does not call EpochBarrier methods.
def oracle_replay(history):
    seen_ids=set(); inv=[]; dec={}; last=None
    for op,args in history:
        if op=='install':
            d=args[0]
            if d.decision_id in dec: raise ValueError('duplicate decision')
            ep=sum(1 for eid,sc in inv if sc==d.scope)
            dec[d.decision_id]=(d.scope,ep,d.planner_generation)
            last={'status':'DECISION_INSTALLED','decision_id':d.decision_id,'scope':d.scope,'epoch':ep,'planner_generation':d.planner_generation,'grants_input_authority':False}
        elif op=='invalidate':
            e=args[0]
            ep_before=sum(1 for eid,sc in inv if sc==e.scope)
            if e.event_id in seen_ids:
                last={'status':'DUPLICATE_INVALIDATION_NOOP','event_id':e.event_id,'scope':e.scope,'epoch':ep_before,'grants_input_authority':False}
            else:
                seen_ids.add(e.event_id); inv.append((e.event_id,e.scope)); ep=ep_before+1
                last={'status':'CURRENTNESS_INVALIDATED','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}
        elif op=='use':
            scope,did=args; cur=sum(1 for eid,sc in inv if sc==scope); rec=dec.get(did)
            if rec is None: last={'status':'UNKNOWN_DECISION','decision_id':did,'scope':scope,'epoch':cur,'grants_input_authority':False}
            else:
                dscope,dep,pgen=rec
                if dscope!=scope: last={'status':'SCOPE_MISMATCH','decision_id':did,'scope':scope,'decision_scope':dscope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
                elif dep!=cur: last={'status':'STALE_EPOCH_REFUSED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
                else: last={'status':'ADMITTED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
    snap={'epochs':tuple(sorted((sc.session,sc.target,sum(1 for _,s in inv if s==sc)) for sc in {s for _,s in inv})),'decisions':tuple(sorted((did,sc.session,sc.target,ep,pg) for did,(sc,ep,pg) in dec.items())),'seen_invalidations':tuple(sorted(seen_ids))}
    return last,snap

def regenerate():
    rng=random.Random(SEED); h=hashlib.sha256(); total=0; traces=0; mismatches=0
    counts={k:0 for k in ['DECISION_INSTALLED','CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','ADMITTED','STALE_EPOCH_REFUSED','UNKNOWN_DECISION','SCOPE_MISMATCH']}
    while total < TRANSITIONS:
        b=EpochBarrier(); history=[]; known=[]; inv_ids=[]; n=min(rng.randint(12,48),TRANSITIONS-total)
        for step in range(n):
            scope=rng.choice(SCOPES); p=rng.random()
            if p < .34:
                did=f'd{traces}:{step}'; known.append((did,scope)); d=DecisionRequest(did,scope,rng.choice(PGENS)); out=b.install(d); history.append(('install',(d,)))
            elif p < .62:
                if inv_ids and rng.random()<.18: eid=rng.choice(inv_ids)
                else: eid=f'e{traces}:{step}'; inv_ids.append(eid)
                e=Invalidation(eid,scope); out=b.invalidate(e); history.append(('invalidate',(e,)))
            else:
                if known and rng.random()<.83:
                    did,dscope=rng.choice(known); qscope=dscope if rng.random()<.78 else rng.choice(SCOPES)
                else: did=f'unknown{traces}:{step}'; qscope=scope
                out=b.try_use(qscope,did); history.append(('use',(qscope,did)))
            want,snap=oracle_replay(history)
            if out!=want or b.snapshot()!=snap: mismatches+=1
            if out['status'] in counts: counts[out['status']]+=1
            h.update(canon({'out':out,'snapshot':b.snapshot()}).encode()+b'\n'); total+=1
        traces+=1
    return {'transitions':total,'traces':traces,'counts':counts,'candidate_oracle_mismatches':mismatches,'transition_digest':h.hexdigest()}

def audit(path):
    got=json.load(open(path)); regen=regenerate(); errors=[]
    if got.get('task') != 'CURRENTNESS-RUNTIME-EPOCH-BARRIER-FORMAL-20260918-003': errors.append('task')
    if got.get('seed') != SEED: errors.append('seed')
    for k in ('transitions','traces','counts','transition_digest'):
        if got.get(k)!=regen.get(k): errors.append(k)
    if regen['candidate_oracle_mismatches']!=0: errors.append('oracle_mismatch')
    for k in ('stale_old_epoch_admissions','cross_scope_mutations','duplicate_invalidation_double_advances','authority_promotions','predecessor_escape','planner_generation_influence'):
        if got.get(k)!=0: errors.append(k)
    if got.get('malformed_controls_passed')!=8: errors.append('malformed_controls')
    if got.get('formal_invocations')!=1 or got.get('reruns')!=0: errors.append('invocation')
    if got.get('decision')!='PASS_RUNTIME_CURRENTNESS_EPOCH_BARRIER_SCOPED': errors.append('decision')
    return {'audit':'PASS' if not errors else 'FAIL','errors':errors,'regenerated':regen}
if __name__=='__main__':
    r=audit(sys.argv[1]); print(json.dumps(r,sort_keys=True,indent=2)); sys.exit(0 if r['audit']=='PASS' else 1)
