from __future__ import annotations
import random
import sys
from pathlib import Path

PARENT = Path(__file__).resolve().parent.parent / 'useful_effect_censored_down_temporal_v1'
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
from candidate import Actuation, EffectRecord, Event, Interval

STRATA=('EXACT_DOWN','CENSORED_BOUNDARY','MULTI_ACTUATION','PRECEDENCE_STRESS')

def _auth(rng):
    xs=[]
    for _ in range(rng.randrange(0,4)):
        a=rng.randrange(0,40); b=rng.randrange(a,41); xs.append(Interval(a,b))
    return tuple(xs)

def _act(rng, aid, exact=None):
    lo=rng.randrange(0,24)
    if exact is True:
        hi=lo
    elif exact is False:
        hi=rng.randrange(lo+1,min(30,lo+6))
    else:
        hi=rng.randrange(lo,min(30,lo+6))
    ulo=rng.randrange(hi,min(34,hi+5))
    uhi=rng.randrange(ulo,min(40,ulo+6))
    return Actuation(aid,lo,hi,ulo,uhi,_auth(rng))

def _records_exact(rng, acts):
    rows=[]
    n=rng.randrange(1,6)
    for j in range(n):
        a=rng.choice(acts)
        t=a.down_lo+rng.randrange(-2,4)
        lin=rng.choice([a.actuation_id,'unknown',None])
        rows.append(EffectRecord(f'e{j}',Event(t,lin,bool(rng.getrandbits(1)),bool(rng.getrandbits(1)))))
    return rows

def _boundary_records(rng,a):
    points=[a.down_lo-1,a.down_lo]
    if a.down_hi-a.down_lo>1:
        points.append(rng.randrange(a.down_lo+1,a.down_hi))
    points.extend([a.down_hi,a.down_hi+1])
    rows=[]
    for j,t in enumerate(points):
        rows.append(EffectRecord(f'e{j}',Event(t,a.actuation_id,True,bool((j+rng.randrange(2))%2))))
    return rows

def _multi_records(rng,acts):
    rows=[]
    for j in range(rng.randrange(0,7)):
        modes=[None,'unknown']+[a.actuation_id for a in acts]
        lin=rng.choice(modes)
        rows.append(EffectRecord(f'e{j}',Event(rng.randrange(-2,43),lin,bool(rng.getrandbits(1)),bool(rng.getrandbits(1)))))
    return rows

def _precedence_records(rng,a):
    t=a.down_lo if a.down_lo<a.down_hi else a.down_lo
    return [
        EffectRecord('e0',Event(t,' ',True,True)),
        EffectRecord('e1',Event(-1,' ',True,True)),
        EffectRecord('e2',Event(-1,a.actuation_id,False,True)),
        EffectRecord('e3',Event(t,a.actuation_id,False,True)),
        EffectRecord('e4',Event(t,'unknown',True,True)),
        EffectRecord('e5',Event(t,None,True,False)),
    ]

def generate(seed:int, per_stratum:int):
    rng=random.Random(seed)
    idx=0
    for stratum in STRATA:
        for _ in range(per_stratum):
            if stratum=='EXACT_DOWN':
                acts=[_act(rng,f'a{i}',True) for i in range(rng.randrange(1,4))]
                records=_records_exact(rng,acts)
            elif stratum=='CENSORED_BOUNDARY':
                a=_act(rng,'a0',False); acts=[a]; records=_boundary_records(rng,a)
            elif stratum=='MULTI_ACTUATION':
                acts=[_act(rng,f'a{i}',None) for i in range(rng.randrange(0,4))]
                records=_multi_records(rng,acts)
            else:
                a=_act(rng,'a0',False); acts=[a]; records=_precedence_records(rng,a)
            yield idx,stratum,Interval(0,40),acts,records
            idx+=1
