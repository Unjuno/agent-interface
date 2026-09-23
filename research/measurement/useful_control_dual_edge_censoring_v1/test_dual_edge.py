from dual_edge_contract import *
import random

# Projection discriminator: exact down=admitted_ns overstates guaranteed occupancy.
wait=Interval(0,100)
a=CensoredActuation(EdgeInterval(10,20),EdgeInterval(60,70),[Interval(0,100)],'a')
b=occupancy_bounds(a,wait)
assert (b.lower_ns,b.upper_ns)==(40,60)
assert 60-10 > b.lower_ns
assert 70-20 < b.upper_ns

a=CensoredActuation(EdgeInterval(10,30),EdgeInterval(20,40),[], 'b')
b=occupancy_bounds(a,wait)
assert (b.lower_ns,b.upper_ns)==(0,30)

a=CensoredActuation(EdgeInterval(10,10),EdgeInterval(40,40),[Interval(15,35)],'c')
b=occupancy_bounds(a,wait)
assert (b.lower_ns,b.upper_ns,b.authority_lower_ns,b.authority_upper_ns)==(30,30,20,20)

try:CensoredActuation(EdgeInterval(50,60),EdgeInterval(10,40),[],'x')
except ValueError:pass
else:raise AssertionError('impossible ordering accepted')

rng=random.Random(2026091701)
for case in range(100_000):
    ws=rng.randrange(0,30); we=rng.randrange(ws+1,80); w=Interval(ws,we)
    acts=[]
    for j in range(rng.randrange(0,6)):
        dlo=rng.randrange(0,70); dhi=rng.randrange(dlo,71)
        rlo=rng.randrange(0,71); rhi=rng.randrange(max(rlo,dlo),81)
        auth=[]
        for _ in range(rng.randrange(0,4)):
            s=rng.randrange(0,70);auth.append(Interval(s,rng.randrange(s+1,81)))
        acts.append(CensoredActuation(EdgeInterval(dlo,dhi),EdgeInterval(rlo,rhi),auth,f'id-{j}'))
    out=analyze(w,acts)
    assert out['authorized_occupancy_lower_ns']<=out['physical_occupancy_lower_ns']
    assert out['authorized_occupancy_upper_ns']<=out['physical_occupancy_upper_ns']
print('FUZZ_PASS 100000')
