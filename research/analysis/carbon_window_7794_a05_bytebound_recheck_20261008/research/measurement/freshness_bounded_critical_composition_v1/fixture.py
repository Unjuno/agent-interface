import random
from candidate import Record,CRITICAL,STATE_KINDS
NOW_NS=1_000_000
MAX_AGE_NS=250_000
SESSIONS=('S0','S1','S2','S3')
TARGETS=('T0','T1','T2')
STREAMS=('A','B','C')
CRIT=tuple(sorted(CRITICAL)); STATES=tuple(sorted(STATE_KINDS))

def batches(seed,count):
    rng=random.Random(seed)
    for bi in range(count):
        n=rng.randint(1,40); rows=[]; ccount={s:0 for s in SESSIONS}
        for j in range(1,n+1):
            s=rng.choice(SESSIONS)
            want_critical=rng.random()<0.45 and ccount[s]<12
            if want_critical:
                kind=rng.choice(CRIT); ccount[s]+=1
            else: kind=rng.choice(STATES)
            # Force useful boundary coverage periodically without changing semantics.
            mode=rng.randrange(20)
            if mode==0: t=NOW_NS-MAX_AGE_NS
            elif mode==1: t=max(0,NOW_NS-MAX_AGE_NS-1)
            else: t=rng.randrange(0,NOW_NS+1)
            rows.append(Record(f'b{bi:05d}-e{j:02d}',j,t,s,rng.choice(TARGETS),rng.choice(STREAMS),kind))
        yield rows
