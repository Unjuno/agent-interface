from __future__ import annotations
from dataclasses import dataclass
from parent_996 import Edge, compose as parent_compose

@dataclass(frozen=True)
class ClockedEdge:
    edge: Edge
    clock_domain: str | None
    clock_epoch: str | None

def _nonblank(v):
    return isinstance(v,str) and bool(v.strip())

def compose_clock_bound(down: ClockedEdge, up: ClockedEdge):
    # Validate parent evidence first without performing any temporal comparison ourselves.
    # Missing/mismatched clock provenance is checked before parent composition, as required
    # because numeric ordering across clocks is meaningless.
    for c in (down,up):
        if not isinstance(c,ClockedEdge) or not isinstance(c.edge,Edge):
            raise ValueError('clocked edge')
    # Preserve parent structural validation / status / lineage behavior. The parent itself
    # may compare intervals, so we reproduce only its pre-temporal gates locally first.
    de,ue=down.edge,up.edge
    from parent_996 import _validate
    _validate(de); _validate(ue)
    if de.edge!='down' or ue.edge!='up': raise ValueError('edge order')
    keys=('actuation_id','owner_id','intent_token','key')
    if any(getattr(de,k)!=getattr(ue,k) for k in keys):
        return {'status':'LINEAGE_MISMATCH','actuation':None,'grants_input_authority':False}
    if de.status!='CONFIRMED_PHYSICAL_DOWN' or ue.status!='CONFIRMED_PHYSICAL_UP':
        return {'status':'INCOMPLETE_EDGE_EVIDENCE','actuation':None,'grants_input_authority':False}
    if not all(_nonblank(x) for x in (down.clock_domain,down.clock_epoch,up.clock_domain,up.clock_epoch)):
        return {'status':'CLOCK_PROVENANCE_MISSING','actuation':None,'grants_input_authority':False}
    if (down.clock_domain,down.clock_epoch)!=(up.clock_domain,up.clock_epoch):
        return {'status':'CLOCK_DOMAIN_MISMATCH','actuation':None,'grants_input_authority':False}
    return parent_compose(de,ue)
