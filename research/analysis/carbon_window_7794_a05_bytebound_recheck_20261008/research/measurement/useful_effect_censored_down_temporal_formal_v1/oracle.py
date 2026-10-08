from __future__ import annotations
from candidate import BUCKETS, valid_id

def role(event, acts):
    if event.actuation_id is not None and not valid_id(event.actuation_id):
        return 'invalid_identity'
    if event.t < 0:
        return 'invalid_temporal'
    if not event.independently_scored:
        return 'unscored'
    by={a.actuation_id:a for a in acts}
    a=by.get(event.actuation_id)
    if a is None:
        return 'useful_unbound' if event.useful else None
    possible=list(range(a.down_lo,a.down_hi+1))
    after=[event.t >= d for d in possible]
    if not any(after): return 'invalid_temporal'
    if not all(after): return 'temporal_ambiguous'
    return 'useful_bound' if event.useful else 'nonuseful_bound'

def effects(records,acts):
    out={k:0 for k in BUCKETS}
    for r in records:
        x=role(r.event,acts)
        if x: out[x]+=1
    return out

def occupancy(wait,acts):
    w=set(range(wait.lo,wait.hi)); gl=set(); pu=set(); al=set(); au=set()
    for a in acts:
        auth=set()
        for i in a.authority: auth.update(range(i.lo,i.hi))
        g={x for x in w if a.down_hi<=x<a.up_lo}
        p={x for x in w if a.down_lo<=x<a.up_hi}
        gl|=g; pu|=p; al|=(g&auth); au|=(p&auth)
    return len(gl),len(pu),len(al),len(au)

def exact_parent_role(event,act):
    if event.actuation_id is not None and not valid_id(event.actuation_id): return 'invalid_identity'
    if event.t<0:return 'invalid_temporal'
    if not event.independently_scored:return 'unscored'
    if event.actuation_id!=act.actuation_id:return 'useful_unbound' if event.useful else None
    if event.t<act.down_lo:return 'invalid_temporal'
    return 'useful_bound' if event.useful else 'nonuseful_bound'
