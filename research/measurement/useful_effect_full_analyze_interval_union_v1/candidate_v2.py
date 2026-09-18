from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Sequence


def valid_id(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())

@dataclass(frozen=True)
class Interval:
    lo: int
    hi: int
    def __post_init__(self):
        if self.lo < 0 or self.hi < self.lo:
            raise ValueError('invalid interval')

@dataclass(frozen=True)
class Actuation:
    actuation_id: str
    down_lo: int
    down_hi: int
    up_lo: int
    up_hi: int
    authority: tuple[Interval, ...] = ()
    def __post_init__(self):
        if not valid_id(self.actuation_id):
            raise ValueError('invalid actuation_id')
        if not (0 <= self.down_lo <= self.down_hi <= self.up_lo <= self.up_hi):
            raise ValueError('invalid edge order')

@dataclass(frozen=True)
class Event:
    t: int
    actuation_id: Any
    independently_scored: bool
    useful: bool

@dataclass(frozen=True)
class EffectRecord:
    effect_id: str
    event: Event

BUCKETS = (
    'useful_bound','useful_unbound','nonuseful_bound','unscored',
    'invalid_identity','invalid_temporal','temporal_ambiguous'
)

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

def occupancy_only(wait: Interval, acts: Sequence[Actuation]) -> tuple[int,int,int,int]:
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

def analyze(wait: Interval, acts: Sequence[Actuation], records: Sequence[EffectRecord]):
    ids=[a.actuation_id for a in acts]
    if len(ids)!=len(set(ids)):
        raise ValueError('duplicate actuation_id')
    effect_ids=[]
    for r in records:
        if not valid_id(r.effect_id):
            raise ValueError('invalid effect_id')
        effect_ids.append(r.effect_id)
    if len(effect_ids)!=len(set(effect_ids)):
        raise ValueError('duplicate effect_id')
    by={a.actuation_id:a for a in acts}
    counts={k:0 for k in BUCKETS}
    for r in records:
        e=r.event
        # Exact #974 precedence up through bound lookup.
        if e.actuation_id is not None and not valid_id(e.actuation_id):
            counts['invalid_identity'] += 1; continue
        if e.t < 0:
            counts['invalid_temporal'] += 1; continue
        if not e.independently_scored:
            counts['unscored'] += 1; continue
        a=by.get(e.actuation_id)
        if a is None:
            if e.useful:
                counts['useful_unbound'] += 1
            continue
        # Only changed gate: exact down -> censored down.
        if e.t < a.down_lo:
            counts['invalid_temporal'] += 1
        elif e.t < a.down_hi:
            counts['temporal_ambiguous'] += 1
        else:
            counts['useful_bound' if e.useful else 'nonuseful_bound'] += 1
    return {'occupancy':occupancy_only(wait,acts),'effects':counts}
