from __future__ import annotations
VALID_DOWN={'CONFIRMED_PHYSICAL_DOWN','OWNER_ALREADY_HELD','PREEXISTING_PHYSICAL_DOWN','PRESS_UNCONFIRMED'}
VALID_UP={'CONFIRMED_PHYSICAL_UP','NOOP_ALREADY_UP','FOREIGN_OR_STALE_DOWN','OWNER_PHYSICAL_MISMATCH','RELEASE_UNCONFIRMED'}
def nonblank(x):return type(x) is str and bool(x.strip())
def oracle(d,u):
    # Independent dictionary-style oracle; does not call candidate/parent.
    for rec,edge,allowed,confirmed in ((d,'down',VALID_DOWN,'CONFIRMED_PHYSICAL_DOWN'),(u,'up',VALID_UP,'CONFIRMED_PHYSICAL_UP')):
        if rec['edge']!=edge: raise ValueError('edge order')
        if rec['status'] not in allowed: raise ValueError('status')
        if any(not nonblank(rec[k]) for k in ('actuation_id','owner_id','intent_token','key')): raise ValueError('lineage')
        if rec['status']==confirmed:
            iv=rec['interval']
            if type(iv) is not tuple or len(iv)!=2 or any(type(x) is not int for x in iv) or iv[0]<0 or iv[1]<iv[0]:raise ValueError('interval')
        elif rec['interval'] is not None:raise ValueError('nonconfirmed interval')
    if any(d[k]!=u[k] for k in ('actuation_id','owner_id','intent_token','key')):
        return ('LINEAGE_MISMATCH',None,False)
    if d['status']!='CONFIRMED_PHYSICAL_DOWN' or u['status']!='CONFIRMED_PHYSICAL_UP':
        return ('INCOMPLETE_EDGE_EVIDENCE',None,False)
    vals=(d.get('clock_domain'),d.get('clock_epoch'),u.get('clock_domain'),u.get('clock_epoch'))
    if not all(nonblank(x) for x in vals):return ('CLOCK_PROVENANCE_MISSING',None,False)
    if vals[:2]!=vals[2:]:return ('CLOCK_DOMAIN_MISMATCH',None,False)
    if d['interval'][1]>u['interval'][0]:return ('EDGE_ORDER_AMBIGUOUS',None,False)
    act={k:d[k] for k in ('actuation_id','owner_id','intent_token','key')}
    act.update(down_lo=d['interval'][0],down_hi=d['interval'][1],up_lo=u['interval'][0],up_hi=u['interval'][1])
    return ('COMPOSED_PHYSICAL_ACTUATION',act,False)
