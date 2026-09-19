from dataclasses import dataclass

PARENT_FRESHNESS_BLOB='404a452aa304b4bde73ec0182450d241e2a744af'
CAPACITY=4
CRITICAL=frozenset({'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED'})
STATE_KINDS=frozenset({'FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH'})
ALL_KINDS=CRITICAL|STATE_KINDS

@dataclass(frozen=True)
class Record:
    event_id:str; seq:int; t_ns:int; session:str; target:str; stream:str; kind:str

def _id(x): return isinstance(x,str) and bool(x.strip())

def validate(records,now_ns,max_age_ns):
    if type(now_ns) is not int or type(max_age_ns) is not int or now_ns<0 or max_age_ns<0: raise ValueError('clock')
    seen=set(); prev=None
    for r in records:
        if not isinstance(r,Record): raise ValueError('record')
        if not _id(r.event_id) or not all(_id(x) for x in (r.session,r.target,r.stream)): raise ValueError('identity')
        if type(r.seq) is not int or type(r.t_ns) is not int or r.seq<0 or r.t_ns<0 or r.t_ns>now_ns: raise ValueError('time_or_seq')
        if r.kind not in ALL_KINDS: raise ValueError('kind')
        if r.event_id in seen: raise ValueError('duplicate_id')
        seen.add(r.event_id)
        if prev is not None and r.seq<=prev: raise ValueError('nonmonotonic_seq')
        prev=r.seq

def reduce_composed(records,now_ns,max_age_ns):
    validate(records,now_ns,max_age_ns)
    retained_critical=[]; counts={}; overflow={}
    latest={}; stale=[]; fresh=[]
    sessions=[]; seen_sessions=set()
    for r in records:
        if r.session not in seen_sessions:
            seen_sessions.add(r.session); sessions.append(r.session)
        if r.kind in CRITICAL:
            n=counts.get(r.session,0); counts[r.session]=n+1
            if n<CAPACITY:
                retained_critical.append(r.event_id)
            else:
                if r.session not in overflow:
                    overflow[r.session]={'status':'RESYNC_REQUIRED','first_unretained_event_id':r.event_id,
                        'first_unretained_seq':r.seq,'first_unretained_kind':r.kind,'unretained_count':1}
                else:
                    overflow[r.session]['unretained_count']+=1
            continue
        if now_ns-r.t_ns>max_age_ns:
            stale.append(r.event_id)
        else:
            fresh.append(r.event_id); latest[(r.session,r.target,r.stream)]=r.event_id
    selected=set(retained_critical)|set(latest.values())
    delivered=[r.event_id for r in records if r.event_id in selected]
    coalesced=[x for x in fresh if x not in selected]
    coverage={s:s not in overflow for s in sessions}
    return {'delivered_ids':delivered,'retained_critical_ids':retained_critical,
        'stale_ids':stale,'coalesced_ids':coalesced,'overflow_by_session':overflow,
        'coverage_complete_by_session':coverage,'stale_count':len(stale),
        'coalesced_count':len(coalesced),'delivered_count':len(delivered),
        'grants_input_authority':False}
