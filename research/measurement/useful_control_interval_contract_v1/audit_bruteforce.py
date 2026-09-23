import random
from interval_contract import *

rng = random.Random(9172027)
for case in range(50_000):
    ws = rng.randrange(0,40); we = rng.randrange(ws+1,61); wait=Interval(ws,we)
    acts=[]
    for j in range(rng.randrange(0,5)):
        down=rng.randrange(0,61); lo=rng.randrange(down,62); hi=rng.randrange(lo,63)
        auth=[]
        for _ in range(rng.randrange(0,4)):
            s=rng.randrange(0,61); e=rng.randrange(s+1,63); auth.append(Interval(s,e))
        acts.append(Actuation(down,ReleaseReceipt(lo,hi,False),auth,f'a{j}'))
    out=analyze(wait,acts,[])
    def units(upper=False, authorized=False):
        covered=set()
        for a in acts:
            end=a.release.hi_ns if upper else a.release.lo_ns
            for t in range(max(wait.start_ns,a.down_ns), min(wait.end_ns,end)):
                if not authorized or any(x.start_ns <= t < x.end_ns for x in a.authority):
                    covered.add(t)
        return len(covered)
    expected=(units(False,False),units(True,False),units(False,True),units(True,True))
    got=(out['physical_occupancy_lower_ns'],out['physical_occupancy_upper_ns'],out['authorized_occupancy_lower_ns'],out['authorized_occupancy_upper_ns'])
    if got != expected:
        raise AssertionError((case,wait,acts,got,expected))
print('PASS independent brute-force cases=50000')
