from __future__ import annotations
from itertools import combinations, product
DOMS=('T','D','E','S')
ORDER={d:i for i,d in enumerate(DOMS)}
PHASE_SUPPORT={
    'PREPARE': frozenset(('T','D','S')),
    'EFFECT_PENDING': frozenset(DOMS),
    'TERMINAL': frozenset(('E','S')),
}

def decision(phase:str, state:tuple[int,int,int,int])->str:
    T,D,E,S=state
    if phase=='PREPARE':
        if S: return 'ABORT'
        if T and D: return 'READY'
        return 'WAIT'
    if phase=='EFFECT_PENDING':
        if S: return 'ABORT'
        if E: return 'COMPLETE'
        if T and D: return 'CONTINUE'
        return 'WAIT'
    if phase=='TERMINAL':
        if S: return 'ABORT'
        if E: return 'COMPLETE'
        return 'TERMINAL_UNRESOLVED'
    raise ValueError('bad_phase')

def all_masks():
    for r in range(5):
        for c in combinations(DOMS,r):
            yield frozenset(c)

def agrees(state, other, mask):
    idx={d:i for i,d in enumerate(DOMS)}
    return all(state[idx[d]]==other[idx[d]] for d in mask)

def valid_certificate(phase,state,mask):
    target=decision(phase,state)
    for nxt in product((0,1), repeat=4):
        if agrees(state,nxt,mask) and decision(phase,nxt)!=target:
            return False
    return True

def select_certificate(phase,state):
    valid=[m for m in all_masks() if valid_certificate(phase,state,m)]
    valid.sort(key=lambda m:(len(m), tuple(ORDER[d] for d in sorted(m,key=ORDER.get))))
    return valid[0], valid

def changed(a,b):
    return frozenset(d for d,x,y in zip(DOMS,a,b) if x!=y)
