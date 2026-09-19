from __future__ import annotations

def _clip(lo, hi, wlo, whi):
    lo=max(lo,wlo); hi=min(hi,whi)
    return (lo,hi) if lo < hi else None

def _intersection(a,b):
    if a is None or b is None:return None
    lo=max(a[0],b[0]);hi=min(a[1],b[1])
    return (lo,hi) if lo < hi else None

def _union_len(intervals):
    xs=sorted(x for x in intervals if x is not None)
    if not xs:return 0
    total=0;lo,hi=xs[0]
    for a,b in xs[1:]:
        if a <= hi:
            if b>hi:hi=b
        else:
            total += hi-lo;lo,hi=a,b
    return total + hi-lo

def occupancy_interval_union(wait, acts):
    guaranteed=[];possible=[];authority_guaranteed=[];authority_possible=[]
    for a in acts:
        g=_clip(a.down_hi,a.up_lo,wait.lo,wait.hi)
        p=_clip(a.down_lo,a.up_hi,wait.lo,wait.hi)
        if g is not None: guaranteed.append(g)
        if p is not None: possible.append(p)
        for z in a.authority:
            auth=_clip(z.lo,z.hi,wait.lo,wait.hi)
            gi=_intersection(g,auth);pi=_intersection(p,auth)
            if gi is not None:authority_guaranteed.append(gi)
            if pi is not None:authority_possible.append(pi)
    return (_union_len(guaranteed),_union_len(possible),_union_len(authority_guaranteed),_union_len(authority_possible))
