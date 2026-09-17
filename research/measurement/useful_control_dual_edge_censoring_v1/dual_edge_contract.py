from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

@dataclass(frozen=True, order=True)
class Interval:
    start_ns: int
    end_ns: int
    def __post_init__(self):
        if type(self.start_ns) is not int or type(self.end_ns) is not int or self.start_ns < 0 or self.end_ns < self.start_ns:
            raise ValueError('invalid interval')
    @property
    def width_ns(self): return self.end_ns - self.start_ns

def intersect(a: Interval,b: Interval):
    s,e=max(a.start_ns,b.start_ns),min(a.end_ns,b.end_ns)
    return Interval(s,e) if e>s else None

def merge(xs: Iterable[Interval]):
    xs=sorted(xs)
    if not xs:return []
    out=[xs[0]]
    for x in xs[1:]:
        p=out[-1]
        if x.start_ns<=p.end_ns: out[-1]=Interval(p.start_ns,max(p.end_ns,x.end_ns))
        else: out.append(x)
    return out

def measure(xs: Iterable[Interval]): return sum(x.width_ns for x in merge(xs))

@dataclass(frozen=True)
class EdgeInterval:
    lo_ns:int
    hi_ns:int
    def __post_init__(self):
        if type(self.lo_ns) is not int or type(self.hi_ns) is not int or self.lo_ns<0 or self.hi_ns<self.lo_ns:
            raise ValueError('invalid edge interval')

@dataclass(frozen=True)
class CensoredActuation:
    down: EdgeInterval
    release: EdgeInterval
    authority: Sequence[Interval]
    actuation_id: str
    def __post_init__(self):
        if not isinstance(self.actuation_id,str) or not self.actuation_id.strip(): raise ValueError('invalid actuation_id')
        # There must exist at least one physically ordered realization D <= R.
        if self.down.lo_ns > self.release.hi_ns: raise ValueError('impossible edge ordering')

@dataclass(frozen=True)
class Bounds:
    lower_ns:int
    upper_ns:int
    authority_lower_ns:int
    authority_upper_ns:int

def envelopes(a:CensoredActuation):
    # Guaranteed occupancy under every feasible realization is only where even
    # the latest possible down precedes the earliest possible release.
    lower = Interval(a.down.hi_ns,a.release.lo_ns) if a.release.lo_ns>a.down.hi_ns else None
    # Possible occupancy is bounded by earliest possible down to latest release.
    upper = Interval(a.down.lo_ns,a.release.hi_ns) if a.release.hi_ns>a.down.lo_ns else None
    return lower,upper

def occupancy_bounds(a:CensoredActuation,wait:Interval):
    lower,upper=envelopes(a)
    lw=intersect(lower,wait) if lower else None
    uw=intersect(upper,wait) if upper else None
    auth=merge(a.authority)
    al=[];au=[]
    for x in auth:
        if lw:
            y=intersect(lw,x)
            if y:al.append(y)
        if uw:
            y=intersect(uw,x)
            if y:au.append(y)
    return Bounds(0 if not lw else lw.width_ns,0 if not uw else uw.width_ns,measure(al),measure(au))

def analyze(wait:Interval,acts:Sequence[CensoredActuation]):
    ids=[a.actuation_id for a in acts]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate actuation_id')
    lowers=[];uppers=[];als=[];aus=[]
    per={}
    for a in acts:
        b=occupancy_bounds(a,wait);per[a.actuation_id]=b.__dict__
        l,u=envelopes(a)
        l=intersect(l,wait) if l else None;u=intersect(u,wait) if u else None
        if l: lowers.append(l)
        if u: uppers.append(u)
        for x in a.authority:
            if l:
                y=intersect(l,x)
                if y:als.append(y)
            if u:
                y=intersect(u,x)
                if y:aus.append(y)
    out=dict(wait_ns=wait.width_ns,physical_occupancy_lower_ns=measure(lowers),physical_occupancy_upper_ns=measure(uppers),authorized_occupancy_lower_ns=measure(als),authorized_occupancy_upper_ns=measure(aus),per_actuation=per)
    if not (0<=out['physical_occupancy_lower_ns']<=out['physical_occupancy_upper_ns']<=wait.width_ns): raise AssertionError('physical invariant')
    if not (0<=out['authorized_occupancy_lower_ns']<=out['physical_occupancy_lower_ns'] and 0<=out['authorized_occupancy_upper_ns']<=out['physical_occupancy_upper_ns']): raise AssertionError('authority invariant')
    return out
