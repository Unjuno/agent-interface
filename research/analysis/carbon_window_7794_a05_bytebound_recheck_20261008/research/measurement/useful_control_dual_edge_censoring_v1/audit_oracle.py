from dual_edge_contract import *
import random

def exact_occ(d,r,w):
    if r<d:return None
    x=intersect(Interval(d,r),w)
    return 0 if x is None else x.width_ns

def auth_occ(d,r,w,auth):
    if r<d:return None
    x=intersect(Interval(d,r),w)
    if not x:return 0
    return measure(y for a in auth if (y:=intersect(x,a)))

def oracle(a,w):
    vals=[];avals=[]
    for d in range(a.down.lo_ns,a.down.hi_ns+1):
        for r in range(a.release.lo_ns,a.release.hi_ns+1):
            if d<=r:
                vals.append(exact_occ(d,r,w));avals.append(auth_occ(d,r,w,a.authority))
    if not vals: raise AssertionError('no feasible realization')
    return min(vals),max(vals),min(avals),max(avals)

rng=random.Random(2026091702)
for case in range(50_000):
    ws=rng.randrange(0,8);we=rng.randrange(ws+1,13);w=Interval(ws,we)
    dlo=rng.randrange(0,10);dhi=rng.randrange(dlo,11)
    rlo=rng.randrange(0,11);rhi=rng.randrange(max(rlo,dlo),13)
    auth=[]
    for _ in range(rng.randrange(0,3)):
        s=rng.randrange(0,11);auth.append(Interval(s,rng.randrange(s+1,13)))
    a=CensoredActuation(EdgeInterval(dlo,dhi),EdgeInterval(rlo,rhi),auth,'a')
    got=occupancy_bounds(a,w); mn,mx,amn,amx=oracle(a,w)
    if got.lower_ns!=mn or got.upper_ns!=mx:
        raise AssertionError((case,a,w,got,(mn,mx)))
    if got.authority_lower_ns>amn or got.authority_upper_ns<amx:
        raise AssertionError(('authority not conservative',case,a,w,got,(amn,amx)))
print('ORACLE_PASS 50000')
