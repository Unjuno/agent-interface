from dataclasses import dataclass

CRITICAL = frozenset({'FOCUS_CHANGED','AUTHORITY_REVOKED','LEASE_EXPIRED','ACTION_REJECTED','SAFETY_VIOLATION','EFFECT_VERIFIED'})
STATE_KINDS = frozenset({'FRAME','STATUS','POINTER_STATE','QUEUE_HEALTH'})
ALL_KINDS = CRITICAL | STATE_KINDS

@dataclass(frozen=True)
class Record:
    event_id: str
    seq: int
    t_ns: int
    session: str
    target: str
    stream: str
    kind: str

def _valid_id(x):
    return isinstance(x, str) and bool(x.strip())

def validate(records, now_ns, max_age_ns):
    if type(now_ns) is not int or type(max_age_ns) is not int or now_ns < 0 or max_age_ns < 0:
        raise ValueError('clock')
    seen=set(); prev=None
    for r in records:
        if not isinstance(r, Record): raise ValueError('record')
        if not _valid_id(r.event_id) or not all(_valid_id(x) for x in (r.session,r.target,r.stream)):
            raise ValueError('identity')
        if type(r.seq) is not int or type(r.t_ns) is not int or r.seq < 0 or r.t_ns < 0 or r.t_ns > now_ns:
            raise ValueError('time_or_seq')
        if r.kind not in ALL_KINDS: raise ValueError('kind')
        if r.event_id in seen: raise ValueError('duplicate_id')
        seen.add(r.event_id)
        if prev is not None and r.seq <= prev: raise ValueError('nonmonotonic_seq')
        prev=r.seq

def reduce_candidate(records, now_ns, max_age_ns):
    validate(records, now_ns, max_age_ns)
    latest={}; stale=[]; critical=[]; fresh=[]
    for r in records:
        if r.kind in CRITICAL:
            critical.append(r.event_id)
        elif now_ns-r.t_ns > max_age_ns:
            stale.append(r.event_id)
        else:
            fresh.append(r.event_id)
            latest[(r.session,r.target,r.stream)] = r.event_id
    selected=set(critical) | set(latest.values())
    delivered=[r.event_id for r in records if r.event_id in selected]
    coalesced=[eid for eid in fresh if eid not in selected]
    return {'delivered_ids':delivered,'critical_ids':critical,'stale_ids':stale,'coalesced_ids':coalesced,'stale_count':len(stale),'coalesced_count':len(coalesced),'delivered_count':len(delivered),'grants_input_authority':False}

def reduce_reference(records, now_ns, max_age_ns):
    validate(records, now_ns, max_age_ns)
    delivered=[]; critical=[]; stale=[]; coalesced=[]
    for i,r in enumerate(records):
        if r.kind in CRITICAL:
            delivered.append(r.event_id); critical.append(r.event_id); continue
        if now_ns-r.t_ns > max_age_ns:
            stale.append(r.event_id); continue
        key=(r.session,r.target,r.stream)
        later=False
        for q in records[i+1:]:
            if q.kind not in CRITICAL and (q.session,q.target,q.stream)==key and now_ns-q.t_ns <= max_age_ns:
                later=True; break
        if later: coalesced.append(r.event_id)
        else: delivered.append(r.event_id)
    return {'delivered_ids':delivered,'critical_ids':critical,'stale_ids':stale,'coalesced_ids':coalesced,'stale_count':len(stale),'coalesced_count':len(coalesced),'delivered_count':len(delivered),'grants_input_authority':False}
