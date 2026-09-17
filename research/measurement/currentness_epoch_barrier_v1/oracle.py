from contract import Scope, DecisionRequest, Invalidation, validate_scope, validate_decision, validate_invalidation, _id

def replay(history):
    epochs={}; decisions={}; seen=set(); last=None
    for op,args in history:
        if op=='install':
            (d,)=args; validate_decision(d)
            if d.decision_id in decisions: raise ValueError('duplicate_decision_id')
            ep=sum(1 for eid,sc in seen if sc==d.scope)
            decisions[d.decision_id]=(d.scope,ep,d.planner_generation)
            last={'status':'DECISION_INSTALLED','decision_id':d.decision_id,'scope':d.scope,'epoch':ep,'planner_generation':d.planner_generation,'grants_input_authority':False}
        elif op=='invalidate':
            (e,)=args; validate_invalidation(e)
            pair=(e.event_id,e.scope)
            duplicate_id=any(eid==e.event_id for eid,_ in seen)
            if duplicate_id:
                ep=sum(1 for _,sc in seen if sc==e.scope)
                last={'status':'DUPLICATE_INVALIDATION_NOOP','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}
            else:
                seen.add(pair)
                ep=sum(1 for _,sc in seen if sc==e.scope)
                last={'status':'CURRENTNESS_INVALIDATED','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}
        elif op=='use':
            scope,did=args; validate_scope(scope)
            if not _id(did): raise ValueError('decision_id')
            cur=sum(1 for _,sc in seen if sc==scope)
            rec=decisions.get(did)
            if rec is None:
                last={'status':'UNKNOWN_DECISION','decision_id':did,'scope':scope,'epoch':cur,'grants_input_authority':False}
            else:
                dscope,dep,pgen=rec
                if dscope!=scope:
                    last={'status':'SCOPE_MISMATCH','decision_id':did,'scope':scope,'decision_scope':dscope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
                elif dep!=cur:
                    last={'status':'STALE_EPOCH_REFUSED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
                else:
                    last={'status':'ADMITTED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'grants_input_authority':False}
        else: raise ValueError('op')
    snap={
        'epochs': tuple(sorted((sc.session,sc.target,sum(1 for _,s in seen if s==sc)) for sc in {s for _,s in seen})),
        'decisions': tuple(sorted((did,sc.session,sc.target,ep,pg) for did,(sc,ep,pg) in decisions.items())),
        'seen_invalidations': tuple(sorted(eid for eid,_ in seen)),
    }
    return last,snap
