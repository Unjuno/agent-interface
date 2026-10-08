from __future__ import annotations
from dataclasses import dataclass

DOWN_STATUSES={'CONFIRMED_PHYSICAL_DOWN','OWNER_ALREADY_HELD','PREEXISTING_PHYSICAL_DOWN','PRESS_UNCONFIRMED'}
UP_STATUSES={'CONFIRMED_PHYSICAL_UP','NOOP_ALREADY_UP','FOREIGN_OR_STALE_DOWN','OWNER_PHYSICAL_MISMATCH','RELEASE_UNCONFIRMED'}

@dataclass(frozen=True)
class Edge:
    edge:str
    status:str
    actuation_id:str
    owner_id:str
    intent_token:str
    key:str
    interval:tuple[int,int]|None

def _id(x): return isinstance(x,str) and bool(x.strip())
def _validate(e:Edge):
    if e.edge not in ('down','up'): raise ValueError('edge')
    allowed=DOWN_STATUSES if e.edge=='down' else UP_STATUSES
    if e.status not in allowed: raise ValueError('status')
    if any(not _id(x) for x in (e.actuation_id,e.owner_id,e.intent_token,e.key)): raise ValueError('lineage')
    confirmed=(e.status=='CONFIRMED_PHYSICAL_DOWN' if e.edge=='down' else e.status=='CONFIRMED_PHYSICAL_UP')
    if confirmed:
        if not isinstance(e.interval,tuple) or len(e.interval)!=2: raise ValueError('missing interval')
        a,b=e.interval
        if type(a) is not int or type(b) is not int or a<0 or b<a: raise ValueError('interval')
    elif e.interval is not None:
        raise ValueError('nonconfirmed interval')

def compose(down:Edge,up:Edge):
    _validate(down);_validate(up)
    if down.edge!='down' or up.edge!='up': raise ValueError('edge order')
    keys=('actuation_id','owner_id','intent_token','key')
    if any(getattr(down,k)!=getattr(up,k) for k in keys):
        return {'status':'LINEAGE_MISMATCH','actuation':None,'grants_input_authority':False}
    if down.status!='CONFIRMED_PHYSICAL_DOWN' or up.status!='CONFIRMED_PHYSICAL_UP':
        return {'status':'INCOMPLETE_EDGE_EVIDENCE','actuation':None,'grants_input_authority':False}
    dlo,dhi=down.interval; ulo,uhi=up.interval
    if dhi>ulo:
        return {'status':'EDGE_ORDER_AMBIGUOUS','actuation':None,'grants_input_authority':False}
    return {'status':'COMPOSED_PHYSICAL_ACTUATION','actuation':{'actuation_id':down.actuation_id,'owner_id':down.owner_id,'intent_token':down.intent_token,'key':down.key,'down_lo':dlo,'down_hi':dhi,'up_lo':ulo,'up_hi':uhi},'grants_input_authority':False}
