from __future__ import annotations
from typing import Any

def lease_active(lease: dict[str, Any], tick: int, resource: str) -> bool:
    return bool(
        lease.get('resource') == resource
        and lease.get('active') is True
        and lease.get('valid_context') is True
        and int(lease.get('start_tick', 0)) <= tick < int(lease.get('end_tick', 0))
    )

def _latest(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows: return None
    return max(rows, key=lambda p: (int(p['proposed_at']), str(p['proposal_id'])))

def authority_guarded(proposals: list[dict[str, Any]], leases: list[dict[str, Any]], generations: dict[str,int], tick: int) -> dict[str, Any]:
    selected={}; deferred=[]
    resources=sorted({str(p['resource']) for p in proposals if p.get('ready')} | set(generations) | {str(l['resource']) for l in leases})
    for resource in resources:
        ready=[dict(p) for p in proposals if p.get('ready') and str(p['resource'])==resource]
        active=[l for l in leases if lease_active(l,tick,resource)]
        if active:
            if len(active)!=1: raise ValueError(f'multiple_active_authorities:{resource}')
            lease=active[0]
            allowed=[p for p in ready if p.get('source')=='threat' and p.get('authority_id')==lease.get('authority_id')]
            for p in ready:
                if p not in allowed: deferred.append({'proposal_id':p['proposal_id'],'resource':resource,'reason':'ACTIVE_THREAT_AUTHORITY'})
            chosen=_latest(allowed)
            if chosen: selected[resource]=chosen
        else:
            chosen=_latest(ready)
            if chosen: selected[resource]=chosen
    return {'selected':selected,'deferred':deferred,'policy':'authority_guarded'}

def handoff_fenced(proposals: list[dict[str, Any]], leases: list[dict[str, Any]], generations: dict[str,int], tick: int) -> dict[str, Any]:
    selected={}; deferred=[]
    resources=sorted({str(p['resource']) for p in proposals if p.get('ready')} | set(generations) | {str(l['resource']) for l in leases})
    for resource in resources:
        current_gen=int(generations[resource])
        ready=[dict(p) for p in proposals if p.get('ready') and str(p['resource'])==resource]
        active=[l for l in leases if lease_active(l,tick,resource)]
        if active:
            if len(active)!=1: raise ValueError(f'multiple_active_authorities:{resource}')
            lease=active[0]
            if int(lease.get('generation',-1))!=current_gen: raise ValueError(f'active_generation_mismatch:{resource}')
            allowed=[p for p in ready if int(p.get('generation',-1))==current_gen and p.get('source')=='threat' and p.get('authority_id')==lease.get('authority_id')]
            for p in ready:
                if p not in allowed: deferred.append({'proposal_id':p['proposal_id'],'resource':resource,'reason':'ACTIVE_THREAT_AUTHORITY_OR_GENERATION'})
            chosen=_latest(allowed)
            if chosen: selected[resource]=chosen
            continue
        allowed=[]
        for p in ready:
            if int(p.get('generation',-1))!=current_gen:
                deferred.append({'proposal_id':p['proposal_id'],'resource':resource,'reason':'STALE_RESOURCE_GENERATION'}); continue
            if p.get('authority_id') is not None:
                deferred.append({'proposal_id':p['proposal_id'],'resource':resource,'reason':'AUTHORITY_NOT_ACTIVE'}); continue
            allowed.append(p)
        chosen=_latest(allowed)
        if chosen: selected[resource]=chosen
    return {'selected':selected,'deferred':deferred,'policy':'handoff_fenced'}
