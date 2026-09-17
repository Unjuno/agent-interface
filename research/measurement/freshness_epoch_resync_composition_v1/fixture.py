import random
from candidate import Record,Snapshot,CRITICAL,STATE_KINDS
PRE_NOW=1_000_000; RESYNC_NOW=1_400_000; FINAL_NOW=1_800_000
SESSIONS=('A','B'); TARGETS=('T0','T1'); STREAMS=('X','Y')
CRIT=tuple(sorted(CRITICAL)); STATES=tuple(sorted(STATE_KINDS))

def _segment(rng,session,start_seq,ncrit,nstate,phase):
    labels=['C']*ncrit+['S']*nstate; rng.shuffle(labels); rows=[]; seq=start_seq
    for lab in labels:
        kind=rng.choice(CRIT if lab=='C' else STATES)
        if phase=='pre':
            now=PRE_NOW
            if lab=='S':
                m=rng.randrange(4); t=PRE_NOW-500_000 if m==0 else (PRE_NOW-500_001 if m==1 else rng.randrange(350_000,PRE_NOW+1))
            else:t=rng.randrange(0,PRE_NOW+1)
        else:
            now=FINAL_NOW
            if lab=='S':
                m=rng.randrange(4); t=FINAL_NOW-500_000 if m==0 else (FINAL_NOW-500_001 if m==1 else rng.randrange(1_100_000,FINAL_NOW+1))
            else:t=rng.randrange(0,FINAL_NOW+1)
        rows.append(Record(f'{session}-{phase}-{seq}',seq,t,session,rng.choice(TARGETS),rng.choice(STREAMS),kind)); seq+=1
    return rows

def scenarios(seed,count):
    rng=random.Random(seed)
    for i in range(count):
        preA=_segment(rng,'A',1,rng.randint(5,9),rng.randint(0,6),'pre')
        preB=_segment(rng,'B',1,rng.randint(0,7),rng.randint(1,5),'pre')
        lastA=preA[-1].seq; snap_seq=lastA+rng.randint(0,2)
        # expected_overflow filled by runner from the actual candidate pre-state; oracle derives same pre-gap independently.
        postA=_segment(rng,'A',snap_seq+1,rng.randint(0,8),rng.randint(0,7),'post')
        lastB=preB[-1].seq if preB else 0
        postB=_segment(rng,'B',lastB+1,rng.randint(0,5),rng.randint(0,5),'post')
        yield {'case_id':f'c{i:05d}','pre':{'A':preA,'B':preB},'snapshot_seq':snap_seq,'post':{'A':postA,'B':postB}}
