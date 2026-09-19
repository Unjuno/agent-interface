import random
from interval_contract import *


def eq(a,b):
    assert a == b, (a,b)

wait = Interval(100, 1100)
a = Actuation(150, ReleaseReceipt(450, 500, False), [Interval(100, 800)], 'a')
r = analyze(wait,[a],[])
eq(r['physical_occupancy_lower_ns'], 300)
eq(r['physical_occupancy_upper_ns'], 350)
eq(r['authorized_occupancy_lower_ns'], 300)
eq(r['authorized_occupancy_upper_ns'], 350)

a = Actuation(150, ReleaseReceipt(900, 950, False), [Interval(100, 400)], 'a')
r = analyze(wait,[a],[])
eq(r['physical_occupancy_lower_ns'], 750)
eq(r['authorized_occupancy_lower_ns'], 250)
assert r['authorized_occupancy_upper_ns'] <= r['physical_occupancy_upper_ns']

a = Actuation(100, ReleaseReceipt(500, 520, False), [Interval(0,1000)], 'a')
b = Actuation(200, ReleaseReceipt(600, 650, False), [Interval(0,1000)], 'b')
r = analyze(Interval(0,1000),[a,b],[])
eq(r['physical_occupancy_lower_ns'], 500)
eq(r['physical_occupancy_upper_ns'], 550)

events = [EffectEvent(300,None,True,True), EffectEvent(320,'a',True,True), EffectEvent(330,'a',True,False), EffectEvent(340,'a',False,True)]
r = analyze(Interval(0,1000),[a],events)
eq(r['effects'], {'useful_bound':1,'useful_unbound':1,'nonuseful_bound':1,'unscored':1})

try:
    Actuation(100, ReleaseReceipt(200,300,True), [], 'bad')
except ValueError:
    pass
else:
    raise AssertionError('post_key_down=true should reject')

# Duplicate causal IDs must fail closed rather than overwrite per-actuation evidence.
try:
    analyze(Interval(0,1000), [
        Actuation(100, ReleaseReceipt(200,210,False), [Interval(0,1000)], 'dup'),
        Actuation(300, ReleaseReceipt(400,410,False), [Interval(0,1000)], 'dup'),
    ], [EffectEvent(350,'dup',True,True)])
except ValueError:
    pass
else:
    raise AssertionError('duplicate actuation_id should reject')

rng = random.Random(9172026)
for _ in range(100_000):
    ws = rng.randrange(0,10_000)
    we = ws + rng.randrange(1,5_000)
    wait = Interval(ws,we)
    acts=[]
    for j in range(rng.randrange(0,6)):
        down = rng.randrange(0,15_000)
        lo = down + rng.randrange(0,2_000)
        hi = lo + rng.randrange(0,500)
        auth=[]
        for _k in range(rng.randrange(0,4)):
            s=rng.randrange(0,15_000); e=s+rng.randrange(1,2_000)
            auth.append(Interval(s,e))
        acts.append(Actuation(down, ReleaseReceipt(lo,hi,False), auth, f'a{j}'))
    out=analyze(wait,acts,[])
    assert 0 <= out['physical_occupancy_lower_ns'] <= out['physical_occupancy_upper_ns'] <= wait.width_ns
    assert 0 <= out['authorized_occupancy_lower_ns'] <= out['authorized_occupancy_upper_ns'] <= wait.width_ns
    assert out['authorized_occupancy_lower_ns'] <= out['physical_occupancy_lower_ns']
    assert out['authorized_occupancy_upper_ns'] <= out['physical_occupancy_upper_ns']
print('PASS fixed + fuzz=100000')
