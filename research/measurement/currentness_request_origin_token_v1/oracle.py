# Independent history replay: no candidate imports.

def sid(s): return (s.session, s.target)

def replay(history):
    epochs={}; requests={}; decisions={}; seen=set(); last=None
    for op,args in history:
        if op=='begin':
            scope,rid,*rest=args; key=sid(scope)
            if rid in requests: raise ValueError('duplicate_request_id')
            ep=epochs.get(key,0); requests[rid]=[key,ep,False]
            last={'status':'REQUEST_BEGUN','request_id':rid,'scope':scope,'request_epoch':ep,'grants_input_authority':False}
        elif op=='invalidate':
            e=args[0]; key=sid(e.scope)
            if e.event_id in seen:
                last={'status':'DUPLICATE_INVALIDATION_NOOP','event_id':e.event_id,'scope':e.scope,'epoch':epochs.get(key,0),'grants_input_authority':False}
            else:
                seen.add(e.event_id); ep=epochs.get(key,0)+1; epochs[key]=ep
                last={'status':'CURRENTNESS_INVALIDATED','event_id':e.event_id,'scope':e.scope,'epoch':ep,'grants_input_authority':False}
        elif op=='install':
            rid,did,pgen,*rest=args; req=requests.get(rid)
            if req is None:
                last={'status':'UNKNOWN_REQUEST_REFUSED','request_id':rid,'decision_id':did,'planner_generation':pgen,'grants_input_authority':False}
            else:
                key,origin,cons=req; cur=epochs.get(key,0)
                scope=next(a[0] for o,a in history if o=='begin' and a[1]==rid)
                if cons:
                    last={'status':'RESPONSE_REPLAY_REFUSED','request_id':rid,'decision_id':did,'scope':scope,'request_epoch':origin,'epoch':cur,'planner_generation':pgen,'grants_input_authority':False}
                else:
                    if did in decisions: raise ValueError('duplicate_decision_id')
                    req[2]=True
                    if origin != cur:
                        last={'status':'STALE_RESPONSE_REFUSED','request_id':rid,'decision_id':did,'scope':scope,'request_epoch':origin,'epoch':cur,'planner_generation':pgen,'grants_input_authority':False}
                    else:
                        decisions[did]=(key,origin,pgen,rid,scope)
                        last={'status':'DECISION_INSTALLED','request_id':rid,'decision_id':did,'scope':scope,'epoch':origin,'planner_generation':pgen,'grants_input_authority':False}
        elif op=='use':
            scope,did=args; key=sid(scope); cur=epochs.get(key,0); rec=decisions.get(did)
            if rec is None:
                last={'status':'UNKNOWN_DECISION','decision_id':did,'scope':scope,'epoch':cur,'grants_input_authority':False}
            else:
                dkey,dep,pgen,rid,dscope=rec
                if dkey != key:
                    last={'status':'SCOPE_MISMATCH','decision_id':did,'scope':scope,'decision_scope':dscope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}
                elif dep != cur:
                    last={'status':'STALE_EPOCH_REFUSED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}
                else:
                    last={'status':'ADMITTED','decision_id':did,'scope':scope,'epoch':cur,'decision_epoch':dep,'planner_generation':pgen,'request_id':rid,'grants_input_authority':False}
    snap={
      'epochs':tuple(sorted((a,b,e) for (a,b),e in epochs.items())),
      'requests':tuple(sorted((rid,a,b,ep,cons) for rid,((a,b),ep,cons) in requests.items())),
      'decisions':tuple(sorted((did,key[0],key[1],ep,pg,rid) for did,(key,ep,pg,rid,_) in decisions.items())),
      'seen_invalidations':tuple(sorted(seen)),
    }
    return last,snap
