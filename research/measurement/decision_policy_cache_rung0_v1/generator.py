import random
from cache import CacheEntry,Evidence

CONTROL_KINDS=('HARD_INVALIDATION','AMBIGUOUS_BOUNDARY','GENERATION_MISMATCH','PROVENANCE_MISMATCH','EXPIRED','INTENT_MISMATCH','STRATEGY_MISMATCH','MAX_UPDATES')

def entry(i):
    return CacheEntry(cache_id=f'c{i}',intent_id=f'intent-{i%7}',strategy_id=f'strategy-{i%3}',generation=i%11,provenance=f'p-{i%5}',macro_id='macro-maintain',allowed_action='ADVANCE_STEP',max_age=12,max_updates=16)

def valid_evidence(e,j,age=None):
    return Evidence(e.intent_id,e.strategy_id,e.generation,e.provenance,j if age is None else age,j,'VALID_CONTINUATION')

def terminal_evidence(e,j,kind):
    v=valid_evidence(e,j)
    if kind=='HARD_INVALIDATION': return Evidence(v.intent_id,v.strategy_id,v.generation,v.provenance,v.age,v.update_index,'HARD_INVALIDATION')
    if kind=='AMBIGUOUS_BOUNDARY': return Evidence(v.intent_id,v.strategy_id,v.generation,v.provenance,v.age,v.update_index,'AMBIGUOUS_BOUNDARY')
    if kind=='GENERATION_MISMATCH': return Evidence(v.intent_id,v.strategy_id,v.generation+1,v.provenance,v.age,v.update_index,v.regime)
    if kind=='PROVENANCE_MISMATCH': return Evidence(v.intent_id,v.strategy_id,v.generation,v.provenance+'-new',v.age,v.update_index,v.regime)
    if kind=='EXPIRED': return Evidence(v.intent_id,v.strategy_id,v.generation,v.provenance,e.max_age+1,v.update_index,v.regime)
    if kind=='INTENT_MISMATCH': return Evidence(v.intent_id+'-new',v.strategy_id,v.generation,v.provenance,v.age,v.update_index,v.regime)
    if kind=='STRATEGY_MISMATCH': return Evidence(v.intent_id,v.strategy_id+'-new',v.generation,v.provenance,v.age,v.update_index,v.regime)
    if kind=='MAX_UPDATES': return Evidence(v.intent_id,v.strategy_id,v.generation,v.provenance,v.age,e.max_updates,v.regime)
    raise ValueError(kind)

def trace(i,rng):
    e=entry(i)
    valid_prefix=1+rng.randrange(7)
    terminal=rng.choice((None,)+CONTROL_KINDS)
    rows=[valid_evidence(e,j) for j in range(valid_prefix)]
    if terminal is not None: rows.append(terminal_evidence(e,valid_prefix,terminal))
    # after terminal, retain two current evidence cycles to ensure no stale continuation.
    if terminal is not None:
        rows.extend([terminal_evidence(e,valid_prefix+k+1,terminal) for k in range(2)])
    return e,rows,terminal
