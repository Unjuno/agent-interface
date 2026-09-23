import random
from parent_candidate import Manager,Record,Snapshot,CRITICAL,STATE_KINDS
PRE=1_000_000; RESYNC=1_400_000; FINAL=1_800_000
CRIT=tuple(sorted(CRITICAL)); STATES=tuple(sorted(STATE_KINDS)); TARGETS=('T0','T1'); STREAMS=('X','Y')

def build_cases(seed,count):
    rng=random.Random(seed)
    for i in range(count):
        m=Manager(); seq=0
        # Session A always crosses epoch1 overflow.
        for _ in range(rng.randint(5,8)):
            seq+=1; m.append(Record(f'A-pre-{seq}',seq,rng.randrange(0,PRE+1),'A',rng.choice(TARGETS),rng.choice(STREAMS),rng.choice(CRIT)),PRE)
        for _ in range(rng.randint(1,4)):
            seq+=1; t=rng.randrange(350_000,PRE+1); m.append(Record(f'A-state-{seq}',seq,t,'A',rng.choice(TARGETS),rng.choice(STREAMS),rng.choice(STATES)),PRE)
        a=m.get('A'); oid=a.overflow_identity(); snap_seq=seq+rng.randint(0,2)
        snap=Snapshot(f'case{i:05d}-snap',snap_seq,RESYNC,'A','T0','X',oid)
        assert m.resync('A',snap,RESYNC)=='RESYNC_ACCEPTED'; seq=snap_seq
        # Epoch2: sometimes second overflow, always at least one fresh state.
        for _ in range(rng.randint(0,7)):
            seq+=1; m.append(Record(f'A-post-c-{seq}',seq,rng.randrange(RESYNC,FINAL+1),'A',rng.choice(TARGETS),rng.choice(STREAMS),rng.choice(CRIT)),FINAL)
        for _ in range(rng.randint(1,5)):
            seq+=1; t=rng.randrange(1_300_000,FINAL+1); m.append(Record(f'A-post-s-{seq}',seq,t,'A',rng.choice(TARGETS),rng.choice(STREAMS),rng.choice(STATES)),FINAL)
        # Session B remains epoch1, useful for isolation after restart.
        bseq=0
        for _ in range(rng.randint(1,6)):
            bseq+=1; kind=rng.choice(CRIT+STATES); t=rng.randrange(1_200_000,FINAL+1); m.append(Record(f'B-{bseq}',bseq,t,'B',rng.choice(TARGETS),rng.choice(STREAMS),kind),FINAL)
        yield f'case{i:05d}',m,snap
