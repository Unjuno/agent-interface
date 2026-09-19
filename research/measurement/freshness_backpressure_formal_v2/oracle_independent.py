CRITICAL={'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED'}
STATE={'FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH'}
def _good(x): return type(x) is str and bool(x.strip())
def reduce_oracle(records,now_ns,max_age_ns):
    if type(now_ns) is not int or type(max_age_ns) is not int or now_ns<0 or max_age_ns<0: raise ValueError('clock')
    seen=set(); last_seq=None
    for r in records:
        if not all(hasattr(r,k) for k in ['event_id','seq','t_ns','session','target','stream','kind']): raise ValueError('record')
        if not _good(r.event_id) or not _good(r.session) or not _good(r.target) or not _good(r.stream): raise ValueError('identity')
        if type(r.seq) is not int or type(r.t_ns) is not int or r.seq<0 or r.t_ns<0 or r.t_ns>now_ns: raise ValueError('time_or_seq')
        if r.kind not in CRITICAL|STATE: raise ValueError('kind')
        if r.event_id in seen: raise ValueError('duplicate_id')
        if last_seq is not None and r.seq<=last_seq: raise ValueError('nonmonotonic_seq')
        seen.add(r.event_id);last_seq=r.seq
    last_fresh={}; stale=[]
    for r in records:
        if r.kind in CRITICAL: continue
        if now_ns-r.t_ns>max_age_ns: stale.append(r.event_id)
        else: last_fresh[(r.session,r.target,r.stream)]=r.event_id
    critical=[r.event_id for r in records if r.kind in CRITICAL]
    keep_critical=set(critical); keep_state=set(last_fresh.values())
    delivered=[r.event_id for r in records if r.event_id in keep_critical or r.event_id in keep_state]
    fresh=[r.event_id for r in records if r.kind not in CRITICAL and now_ns-r.t_ns<=max_age_ns]
    coalesced=[x for x in fresh if x not in keep_state]
    return {'delivered_ids':delivered,'critical_ids':critical,'stale_ids':stale,'coalesced_ids':coalesced,'stale_count':len(stale),'coalesced_count':len(coalesced),'delivered_count':len(delivered),'grants_input_authority':False}
