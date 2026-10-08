from dataclasses import dataclass
CRIT=frozenset({'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED','CURRENTNESS_INVALIDATED'})
STATE=frozenset({'FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH'})
@dataclass(frozen=True)
class R: event_id:str; seq:int; t_ns:int; session:str; target:str; stream:str; kind:str
def okstr(x): return type(x) is str and bool(x.strip())
def reduce_ref(rows,now,max_age):
    if type(now) is not int or type(max_age) is not int or now<0 or max_age<0: raise ValueError('clock')
    seen=set(); prev=None
    for x in rows:
        if not isinstance(x,R): raise ValueError('record')
        if not okstr(x.event_id) or not all(okstr(y) for y in (x.session,x.target,x.stream)): raise ValueError('identity')
        if type(x.seq) is not int or type(x.t_ns) is not int or x.seq<0 or x.t_ns<0 or x.t_ns>now: raise ValueError('time_or_seq')
        if x.kind not in CRIT|STATE: raise ValueError('kind')
        if x.event_id in seen: raise ValueError('duplicate_id')
        if prev is not None and x.seq<=prev: raise ValueError('nonmonotonic_seq')
        seen.add(x.event_id); prev=x.seq
    keep=set(); critical=[]; stale=[]; latest={}
    for x in rows:
        if x.kind in CRIT: critical.append(x.event_id); keep.add(x.event_id)
        elif now-x.t_ns>max_age: stale.append(x.event_id)
        else: latest[(x.session,x.target,x.stream)]=x.event_id
    keep.update(latest.values())
    fresh_noncrit=[x.event_id for x in rows if x.kind not in CRIT and now-x.t_ns<=max_age]
    coalesced=[x for x in fresh_noncrit if x not in keep]
    return {'delivered_ids':[x.event_id for x in rows if x.event_id in keep],'critical_ids':critical,'stale_ids':stale,'coalesced_ids':coalesced,'stale_count':len(stale),'coalesced_count':len(coalesced),'delivered_count':len(keep),'grants_input_authority':False}
