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

def occupancy_only(wait: Interval, acts: Sequence[Actuation]) -> tuple[int,int,int,int]:
    # Integer half-open semantics, equivalent to union lengths on integer endpoints.
    guaranteed=set(); possible=set(); ag=set(); ap=set()
    wait_pts=set(range(wait.lo, wait.hi))
    for a in acts:
        g=set(range(a.down_hi, a.up_lo)) & wait_pts
        p=set(range(a.down_lo, a.up_hi)) & wait_pts
        auth=set()
        for z in a.authority:
            auth.update(range(z.lo,z.hi))
        guaranteed |= g
        possible |= p
        ag |= g & auth
        ap |= p & auth
    return len(guaranteed),len(possible),len(ag),len(ap)

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
