import random
from contract import Case
SEED=112820260918001
# Reconstruct exact retained Rung0 aggregate distribution at 2x its primary size:
# dynamic 320k: along1=191610, opposite1=32018, along2=64354, opposite2=32018.
# ambiguous 80k all realized within {-1,+1}. Overall hits reproduce 75.907% / 83.991%.
COUNTS={'along1':191610,'opposite1':32018,'along2':64354,'opposite2':32018,'ambiguous':80000}

def build(seed=SEED):
    rows=[]; cid=0
    def add(n,dirn,outcome,category):
        nonlocal cid
        hist=(-3*dirn,-2*dirn,-1*dirn) if dirn else (-1,1,0)
        for _ in range(n):
            rows.append(Case(cid,hist,outcome,category));cid+=1
    # Split every dynamic count equally across right/left histories.
    for name,total in [('along1',COUNTS['along1']),('opposite1',COUNTS['opposite1']),('along2',COUNTS['along2']),('opposite2',COUNTS['opposite2'])]:
        assert total%2==0
        n=total//2
        for d in (1,-1):
            if name=='along1': out=d
            elif name=='opposite1': out=-d
            elif name=='along2': out=2*d
            else: out=-2*d
            add(n,d,out,name)
    # Ambiguous histories use the parent selector {-1,+1}; alternate realized sign.
    for i in range(COUNTS['ambiguous']):
        rows.append(Case(cid,(-1,1,0),1 if i%2==0 else -1,'ambiguous'));cid+=1
    assert len(rows)==400000
    rnd=random.Random(seed);rnd.shuffle(rows)
    return rows
