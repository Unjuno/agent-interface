from collections import defaultdict
from candidate import Record,CRITICAL,CAPACITY,validate

def reduce_oracle(records,now_ns,max_age_ns):
    validate(records,now_ns,max_age_ns)
    sessions=[]
    for r in records:
        if r.session not in sessions: sessions.append(r.session)
    crit=defaultdict(list)
    for r in records:
        if r.kind in CRITICAL: crit[r.session].append(r)
    retained=set(); retained_order=[]; overflow={}
    for s in sessions:
        rows=crit.get(s,[])
        for r in rows[:CAPACITY]: retained.add(r.event_id)
        if len(rows)>CAPACITY:
            u=rows[CAPACITY]
            overflow[s]={'status':'RESYNC_REQUIRED','first_unretained_event_id':u.event_id,
                'first_unretained_seq':u.seq,'first_unretained_kind':u.kind,
                'unretained_count':len(rows)-CAPACITY}
    for r in records:
        if r.event_id in retained: retained_order.append(r.event_id)
    stale=[]; newest={}
    for r in reversed(records):
        if r.kind in CRITICAL: continue
        if now_ns-r.t_ns>max_age_ns: continue
        k=(r.session,r.target,r.stream)
        if k not in newest: newest[k]=r.event_id
    fresh=[]
    for r in records:
        if r.kind in CRITICAL: continue
        if now_ns-r.t_ns>max_age_ns: stale.append(r.event_id)
        else: fresh.append(r.event_id)
    selected=retained|set(newest.values())
    delivered=[r.event_id for r in records if r.event_id in selected]
    coalesced=[x for x in fresh if x not in selected]
    return {'delivered_ids':delivered,'retained_critical_ids':retained_order,
        'stale_ids':stale,'coalesced_ids':coalesced,'overflow_by_session':overflow,
        'coverage_complete_by_session':{s:s not in overflow for s in sessions},
        'stale_count':len(stale),'coalesced_count':len(coalesced),'delivered_count':len(delivered),
        'grants_input_authority':False}
